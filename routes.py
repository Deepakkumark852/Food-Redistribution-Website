from flask import render_template, request, redirect, url_for, flash, session, jsonify
import re
from datetime import datetime, date, time, timedelta
from werkzeug.security import generate_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from functools import wraps
import os

# RBAC decorator
def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            user_roles = claims.get('roles', [])
            if isinstance(user_roles, str):
                user_roles = [r.strip() for r in user_roles.split(',') if r.strip()]
            if not any(r in user_roles for r in roles):
                return jsonify({'msg': 'Forbidden'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def init_routes(app, mysql):
    # JWT setup
    app.config['JWT_SECRET_KEY'] = app.config.get('SECRET_KEY', 'dev-key-123')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=15)
    jwt = JWTManager(app)

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        print('DEBUG JWT expired_token_loader called')
        return jsonify({'error': 'Session expired. Please log in again.'}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        print('DEBUG JWT invalid_token_loader called:', error)
        # Check if it's the "Subject must be a string" error from old tokens
        if "Subject must be a string" in str(error):
            return jsonify({'error': 'Token format outdated. Please log in again.', 'logout_required': True}), 401
        return jsonify({'error': 'Invalid token. Please log in again.'}), 401

    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        print('DEBUG JWT unauthorized_loader called:', error)
        return jsonify({'error': 'Missing or invalid token. Please log in again.'}), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        print('DEBUG JWT revoked_token_loader called')
        return jsonify({'error': 'Token has been revoked. Please log in again.'}), 401
        
    # API Endpoints
    @app.route('/api/requests', methods=['POST'])
    @jwt_required()
    def api_create_request():
        cur = None
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['food_id', 'quantity', 'delivery_address', 'transport_arranged']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
            
            current_user_id = int(get_jwt_identity())
            cur = mysql.connection.cursor()
            
            # Get donation details with proper error handling
            try:
                cur.execute("""
                    SELECT d.*, u.username, d.food_name 
                    FROM donations d 
                    JOIN users u ON d.donor_id = u.id 
                    WHERE d.id = %s
                    FOR UPDATE  -- Lock the row for update
                """, (data['food_id'],))
                donation = cur.fetchone()
            except Exception as e:
                app.logger.error(f'Error fetching donation: {str(e)}')
                return jsonify({'error': 'Error fetching donation details'}), 500
            
            if not donation:
                return jsonify({'error': 'Donation not found'}), 404
                
            # Validate quantity
            try:
                requested_quantity = int(data['quantity'])
                if requested_quantity <= 0:
                    return jsonify({'error': 'Quantity must be greater than 0'}), 400
                    
                if donation['quantity'] < requested_quantity:
                    return jsonify({
                        'error': f'Not enough quantity available. Only {donation["quantity"]} servings left.'
                    }), 400
            except (ValueError, TypeError) as e:
                return jsonify({'error': 'Invalid quantity value'}), 400
            
            # Parse delivery location if provided
            delivery_lat = None
            delivery_lng = None
            if 'delivery_latitude' in data and data['delivery_latitude'] is not None and \
               'delivery_longitude' in data and data['delivery_longitude'] is not None:
                try:
                    delivery_lat = float(data['delivery_latitude'])
                    delivery_lng = float(data['delivery_longitude'])
                except (ValueError, TypeError):
                    app.logger.warning(f'Invalid delivery coordinates: {data.get("delivery_latitude")}, {data.get("delivery_longitude")}')
            
            # Create the request
            try:
                cur.execute("""
                    INSERT INTO requests 
                    (food_id, requester_id, quantity, delivery_address, 
                     delivery_latitude, delivery_longitude, transport_arranged, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending', NOW())
                """, (
                    data['food_id'],
                    current_user_id,
                    requested_quantity,
                    data['delivery_address'],
                    delivery_lat,
                    delivery_lng,
                    bool(data['transport_arranged'])
                ))
                
                request_id = cur.lastrowid
                
                # Update donation quantity
                new_quantity = donation['quantity'] - requested_quantity
                cur.execute("""
                    UPDATE donations 
                    SET quantity = %s 
                    WHERE id = %s
                """, (new_quantity, data['food_id']))
                
                # Create notification for donor
                try:
                    cur.execute("""
                        INSERT INTO notifications 
                        (user_id, message, created_at, is_read)
                        VALUES (%s, %s, NOW(), FALSE)
                    """, (
                        donation['donor_id'],
                        f"New request for {requested_quantity} servings of {donation['food_name']}"
                    ))
                except Exception as e:
                    app.logger.error(f'Error creating notification: {str(e)}')
                    # Don't fail the request if notification fails
                
                mysql.connection.commit()
                
                response_data = {
                    'id': request_id,
                    'food_id': data['food_id'],
                    'food_name': donation.get('food_name', 'Unknown Food'),
                    'quantity': requested_quantity,
                    'status': 'pending',
                    'remaining_quantity': new_quantity,
                    'message': 'Request submitted successfully'
                }
                
                return jsonify(response_data), 201
                
            except Exception as e:
                mysql.connection.rollback()
                app.logger.error(f'Database error: {str(e)}')
                return jsonify({'error': 'Database error while processing request'}), 500
                
        except Exception as e:
            if mysql.connection:
                mysql.connection.rollback()
            app.logger.error(f'Unexpected error in api_create_request: {str(e)}')
            return jsonify({'error': 'An unexpected error occurred'}), 500
            
        finally:
            if cur:
                try:
                    cur.close()
                except:
                    pass

    @app.route('/')
    @role_required('donor', 'requester', 'volunteer', 'admin')
    def home():
        if 'user_id' in session:
            return redirect(url_for('donate'))
        return redirect(url_for('login'))

    # ========== AUTHENTICATION ROUTES ==========
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM users WHERE username = %s", [username])
            user = cur.fetchone()
            cur.close()
            
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                flash('Login successful!', 'success')
                return redirect(url_for('donate'))
            else:
                flash('Invalid username or password', 'danger')
        
        return render_template('login.html')

    @app.route('/logout')
    @role_required('donor', 'requester', 'volunteer', 'admin')
    def logout():
        session.clear()
        flash('You have been logged out', 'info')
        return redirect(url_for('login'))

    # ========== MAIN APPLICATION ROUTES ========== 
    @app.route('/donate', methods=['GET', 'POST'])
    @role_required('donor', 'admin')
    def donate():
        if 'user_id' not in session:
            return redirect(url_for('login'))
            
        if request.method == 'POST':
            food_data = {
                'food_name': request.form['food_name'],
                'quantity': int(request.form['quantity']),
                'expiry_date': request.form['expiry_date'],
                'pickup_address': request.form['pickup_address'],
                'pickup_time': request.form['pickup_time'],
                'special_instructions': request.form.get('special_instructions', ''),
                'donor_id': session['user_id']
            }
            
            try:
                cur = mysql.connection.cursor()
                cur.execute("""
                    INSERT INTO donations 
                    (food_name, quantity, expiry_date, pickup_address, pickup_time, special_instructions, donor_id)
                    VALUES (%(food_name)s, %(quantity)s, %(expiry_date)s, %(pickup_address)s, %(pickup_time)s, %(special_instructions)s, %(donor_id)s)
                """, food_data)
                mysql.connection.commit()
                flash('Food donation submitted successfully!', 'success')
                return redirect(url_for('donate'))
            except Exception as e:
                mysql.connection.rollback()
                flash(f'Error: {str(e)}', 'danger')
            finally:
                cur.close()
        
        return render_template('donate.html')

    @app.route('/request', methods=['GET', 'POST'])
    @role_required('requester', 'admin')
    def request_food():
        if 'user_id' not in session:
            return redirect(url_for('login'))
            
        cur = mysql.connection.cursor()
        
        if request.method == 'POST':
            request_data = {
                'food_id': int(request.form['food_id']),
                'quantity': int(request.form['quantity']),
                'delivery_address': request.form['delivery_address'],
                'transport': request.form['transport'] == 'self'
            }
            
            try:
                # Check available quantity
                cur.execute("SELECT quantity FROM donations WHERE id = %s", [request_data['food_id']])
                donation = cur.fetchone()
                
                if not donation or donation['quantity'] < request_data['quantity']:
                    flash('Not enough quantity available', 'danger')
                    return redirect(url_for('request_food'))
                
                # Create request
                cur.execute("""
                    INSERT INTO requests 
                    (food_id, requester_id, quantity, delivery_address, transport_arranged)
                    VALUES (%s, %s, %s, %s, %s)
                """, (request_data['food_id'], session['user_id'], request_data['quantity'], 
                     request_data['delivery_address'], request_data['transport']))
                
                # Update donation quantity
                new_quantity = donation['quantity'] - request_data['quantity']
                cur.execute("""
                    UPDATE donations SET quantity = %s WHERE id = %s
                """, (new_quantity, request_data['food_id']))
                
                mysql.connection.commit()
                flash('Request submitted successfully!', 'success')
                return redirect(url_for('request_food'))
            except Exception as e:
                mysql.connection.rollback()
                flash(f'Error: {str(e)}', 'danger')
            finally:
                cur.close()
              
        
        # GET request - show available donations
        cur.execute("""
            SELECT d.*, u.username AS donor_name 
            FROM donations d
            JOIN users u ON d.donor_id = u.id
            WHERE expiry_date >= CURDATE()
            ORDER BY created_at DESC
        """)
        donations = cur.fetchall()
        cur.close()
        
        return render_template('request.html', donations=donations)
        #return render_template('template.html', expiry_date=donation.expiry_date)
    

    @app.route('/volunteer')
    @role_required('volunteer', 'admin')
    def volunteer():
        if 'user_id' not in session:
            return redirect(url_for('login'))
            
        cur = mysql.connection.cursor()
        
        # Get pending requests
        cur.execute("""
            SELECT r.*, d.food_name, d.pickup_address, u.username AS requester_name
            FROM requests r
            JOIN donations d ON r.food_id = d.id
            JOIN users u ON r.requester_id = u.id
            WHERE r.status = 'pending'
            ORDER BY created_at DESC
        """)
        pending_requests = cur.fetchall()
        
        # Get my assignments
        cur.execute("""
            SELECT r.*, d.food_name, d.pickup_address, u.username AS requester_name
            FROM requests r
            JOIN donations d ON r.food_id = d.id
            JOIN users u ON r.requester_id = u.id
            WHERE r.volunteer_id = %s AND r.status = 'assigned'
            ORDER BY assigned_at DESC
        """, [session['user_id']])
        my_assignments = cur.fetchall()
        
        cur.close()
        return render_template('volunteer.html', 
                            pending_requests=pending_requests,
                            my_assignments=my_assignments)

    # ========== API ROUTES ========== 
    @app.route('/api/food/<int:food_id>')
    @role_required('donor', 'requester', 'volunteer', 'admin')
    def get_food_details(food_id):
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT d.*, u.username AS donor_name, u.email AS donor_email, u.mobile AS donor_mobile
            FROM donations d
            JOIN users u ON d.donor_id = u.id
            WHERE d.id = %s
        """, [food_id])
        food = cur.fetchone()
        cur.close()
        if food:
            from datetime import datetime, date, time, timedelta
            def serialize(v):
                if isinstance(v, (datetime, date, time, timedelta)):
                    return v.isoformat() if hasattr(v, 'isoformat') else str(v)
                return v
            return jsonify({k: serialize(v) for k, v in food.items()})
        return jsonify({'error': 'Food not found'}), 404

    @app.route('/api/register', methods=['POST'])
    def api_register():
        data = request.get_json()
        username = data.get('username')
        password = generate_password_hash(data.get('password'))
        email = data.get('email')
        mobile = data.get('mobile')
        roles = [data.get('role', 'donor')]
        special_key = data.get('special_key')
        # Validate inputs
        if len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters'}), 400
        if len(data.get('password')) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        if not re.match(r'^\d{10,15}$', mobile):
            return jsonify({'error': 'Invalid mobile number'}), 400
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            return jsonify({'error': 'Invalid email address'}), 400
        if 'admin' in roles:
            from config import Config
            if not special_key or special_key != Config.ADMIN_SPECIAL_KEY:
                return jsonify({'error': 'Invalid or missing special key for admin registration'}), 403
        try:
            cur = mysql.connection.cursor()
            cur.execute(
                "INSERT INTO users (username, password, email, mobile, roles) VALUES (%s, %s, %s, %s, %s)",
                (username, password, email, mobile, ','.join(roles))
            )
            mysql.connection.commit()
            cur.close()
            return jsonify({'msg': 'Registration successful!'}), 201
        except Exception as e:
            mysql.connection.rollback()
            return jsonify({'error': str(e)}), 400

    @app.route('/api/login', methods=['POST'])
    def api_login():
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", [username])
        user = cur.fetchone()
        cur.close()
        if user and check_password_hash(user['password'], password):
            user_roles = [r.strip() for r in user['roles'].split(',') if r.strip()]
            access_token = create_access_token(identity=str(user['id']), additional_claims={
                'username': user['username'],
                'roles': user_roles
            })
            return jsonify({'access_token': access_token, 'roles': user_roles, 'user': {'id': user['id'], 'username': user['username']}}), 200
        else:
            return jsonify({'error': 'Invalid username or password'}), 401

    @app.route('/api/donate', methods=['POST'])
    @role_required('donor', 'admin')
    def api_donate():
        from googlemaps_helper import geocode_address, reverse_geocode
        data = request.get_json(silent=True)
        user_id = int(get_jwt_identity())
        api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
        try:
            address = data.get('pickup_address')
            lat = data.get('latitude')
            lng = data.get('longitude')
            if address and (not lat or not lng):
                lat, lng = geocode_address(address, api_key)
            if (lat and lng) and not address:
                address = reverse_geocode(lat, lng, api_key)
            food_data = {
                'food_name': data['food_name'],
                'quantity': int(data['quantity']),
                'expiry_date': data['expiry_date'],
                'pickup_address': address,
                'pickup_time': data['pickup_time'],
                'special_instructions': data.get('special_instructions', ''),
                'donor_id': user_id,
                'latitude': lat,
                'longitude': lng,
                'food_image_base64': data.get('food_image_base64') or None
            }
        except (KeyError, ValueError, TypeError) as e:
            return jsonify({'error': f'Invalid or missing field: {str(e)}'}), 422
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO donations 
                (food_name, quantity, expiry_date, pickup_address, pickup_time, special_instructions, donor_id, latitude, longitude, food_image_base64)
                VALUES (%(food_name)s, %(quantity)s, %(expiry_date)s, %(pickup_address)s, %(pickup_time)s, %(special_instructions)s, %(donor_id)s, %(latitude)s, %(longitude)s, %(food_image_base64)s)
            """, food_data)
            mysql.connection.commit()
            cur.close()
            return jsonify({'msg': 'Food donation submitted successfully!'}), 201
        except Exception as e:
            mysql.connection.rollback()
            return jsonify({'error': str(e)}), 400

    # --- New endpoint: Get donations, optionally sorted by proximity ---
    @app.route('/api/donations', methods=['GET'])
    @jwt_required()
    def get_donations():
        user_lat = request.args.get('latitude', type=float)
        user_lng = request.args.get('longitude', type=float)
        filter_food = request.args.get('food_name')
        filter_expiry = request.args.get('expiry_date')
        cur = mysql.connection.cursor()
        base_query = "SELECT * FROM donations"
        filters = []
        params = []
        if filter_food:
            filters.append("food_name LIKE %s")
            params.append(f"%{filter_food}%")
        if filter_expiry:
            filters.append("expiry_date = %s")
            params.append(filter_expiry)
        if filters:
            base_query += " WHERE " + " AND ".join(filters)
        # If user location provided, calculate distance using Haversine formula
        if user_lat is not None and user_lng is not None:
            base_query = base_query.replace("SELECT *", "SELECT *, (6371 * acos(cos(radians(%s)) * cos(radians(latitude)) * cos(radians(longitude) - radians(%s)) + sin(radians(%s)) * sin(radians(latitude)))) AS distance")
            params = [user_lat, user_lng, user_lat] + params
            base_query += " ORDER BY distance ASC"
        else:
            base_query += " ORDER BY created_at DESC"
        cur.execute(base_query, params)
        donations = cur.fetchall()
        cur.close()
        # Serialize all rows to handle datetime/timedelta
        def serialize_row(row):
            from datetime import datetime, date, time, timedelta
            result = {}
            for k, v in row.items():
                if isinstance(v, (datetime, date, time, timedelta)):
                    result[k] = str(v)
                else:
                    result[k] = v
            return result
        donations = [serialize_row(d) for d in donations]
        return jsonify({'donations': donations})

    @app.route('/api/profile', methods=['GET'])
    @jwt_required()
    def get_profile():
        user_id = int(get_jwt_identity())
        cur = mysql.connection.cursor()
        cur.execute("SELECT username, email, mobile, roles FROM users WHERE id = %s", [user_id])
        user = cur.fetchone()
        cur.close()
        if user:
            user['roles'] = [r.strip() for r in user['roles'].split(',') if r.strip()]
            return jsonify(user)
        return jsonify({'error': 'User not found'}), 404

    @app.route('/api/profile/edit', methods=['POST'])
    @jwt_required()
    def edit_profile():
        user_id = int(get_jwt_identity())
        data = request.get_json()
        email = data.get('email')
        mobile = data.get('mobile')
        roles = data.get('roles')
        special_key = data.get('special_key')
        # Validate email/mobile
        if email and not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            return jsonify({'error': 'Invalid email address'}), 400
        if mobile and not re.match(r'^\d{10,15}$', mobile):
            return jsonify({'error': 'Invalid mobile number'}), 400
        cur = mysql.connection.cursor()
        # Update email/mobile
        if email or mobile:
            cur.execute("UPDATE users SET email = %s, mobile = %s WHERE id = %s", (email, mobile, user_id))
        # Update roles if provided
        if roles:
            # Validate roles
            valid_roles = {'donor', 'requester', 'volunteer', 'admin'}
            roles_set = set([r.strip() for r in roles if r.strip()])
            if not roles_set.issubset(valid_roles):
                cur.close()
                return jsonify({'error': 'Invalid roles'}), 400
            # Admin role requires special key
            if 'admin' in roles_set:
                from config import Config
                if not special_key or special_key != Config.ADMIN_SPECIAL_KEY:
                    cur.close()
                    return jsonify({'error': 'Invalid or missing special key for admin role'}), 403
            cur.execute("UPDATE users SET roles = %s WHERE id = %s", (','.join(roles_set), user_id))
        mysql.connection.commit()
        cur.execute("SELECT roles FROM users WHERE id = %s", [user_id])
        new_roles = [r.strip() for r in cur.fetchone()['roles'].split(',') if r.strip()]
        cur.close()
        return jsonify({'msg': 'Profile updated', 'roles': new_roles})

    @app.route('/api/profile/change_password', methods=['POST'])
    @jwt_required()
    def change_password():
        user_id = int(get_jwt_identity())
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        if not current_password or not new_password:
            return jsonify({'error': 'All fields required'}), 400
        if len(new_password) < 8:
            return jsonify({'error': 'New password must be at least 8 characters'}), 400
        cur = mysql.connection.cursor()
        cur.execute("SELECT password FROM users WHERE id = %s", [user_id])
        user = cur.fetchone()
        from werkzeug.security import check_password_hash
        if not user or not check_password_hash(user['password'], current_password):
            cur.close()
            return jsonify({'error': 'Current password incorrect'}), 403
        new_hash = generate_password_hash(new_password)
        cur.execute("UPDATE users SET password = %s WHERE id = %s", (new_hash, user_id))
        mysql.connection.commit()
        cur.close()
        return jsonify({'msg': 'Password changed successfully'})

    # ========== HISTORY API ROUTES ========== 
    def serialize_row(row):
        # Converts all datetime/date/time/timedelta fields to string and Decimal to float
        result = {}
        for k, v in row.items():
            if v is None:
                result[k] = None
            elif isinstance(v, (datetime, date, time, timedelta)):
                result[k] = str(v)
            elif hasattr(v, '__class__') and v.__class__.__name__ == 'Decimal':
                result[k] = float(v)
            else:
                result[k] = v
        return result

    @app.route('/api/history/donations')
    @role_required('donor', 'admin')
    def donation_history():
        user_id = int(get_jwt_identity())
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT * FROM donations WHERE donor_id = %s ORDER BY created_at DESC
        """, [user_id])
        donations = cur.fetchall()
        cur.close()
        # Serialize all rows
        donations = [serialize_row(d) for d in donations]
        return jsonify({'donations': donations})

    @app.route('/api/history/requests')
    @role_required('requester', 'admin')
    def request_history():
        user_id = int(get_jwt_identity())
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT r.*, d.food_name FROM requests r
            JOIN donations d ON r.food_id = d.id
            WHERE r.requester_id = %s ORDER BY r.created_at DESC
        """, [user_id])
        requests = cur.fetchall()
        cur.close()
        requests = [serialize_row(r) for r in requests]
        return jsonify({'requests': requests})

    @app.route('/api/history/volunteering')
    @role_required('volunteer', 'admin')
    def volunteering_history():
        user_id = int(get_jwt_identity())
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT r.*, d.food_name FROM requests r
            JOIN donations d ON r.food_id = d.id
            WHERE r.volunteer_id = %s ORDER BY r.assigned_at DESC
        """, [user_id])
        volunteering = cur.fetchall()
        cur.close()
        volunteering = [serialize_row(v) for v in volunteering]
        return jsonify({'volunteering': volunteering})

    @app.route('/api/volunteer/pending')
    @role_required('volunteer', 'admin')
    def get_pending_volunteer_requests():
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT r.*, d.food_name, d.pickup_address, u.username AS requester_name
            FROM requests r
            JOIN donations d ON r.food_id = d.id
            JOIN users u ON r.requester_id = u.id
            WHERE r.status = 'pending' AND r.volunteer_id IS NULL
            ORDER BY r.created_at DESC
        """)
        pending_requests = cur.fetchall()
        cur.close()
        pending_requests = [serialize_row(r) for r in pending_requests]
        return jsonify({'pending_requests': pending_requests})

    @app.route('/api/volunteer/assignments')
    @role_required('volunteer', 'admin')
    def get_volunteer_assignments():
        user_id = int(get_jwt_identity())
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT r.*, d.food_name, d.pickup_address, u.username AS requester_name,
                   d.donor_id, donor.username AS donor_name, d.latitude AS donor_lat, 
                   d.longitude AS donor_lng, r.delivery_latitude, r.delivery_longitude
            FROM requests r
            JOIN donations d ON r.food_id = d.id
            JOIN users u ON r.requester_id = u.id
            JOIN users donor ON d.donor_id = donor.id
            WHERE r.volunteer_id = %s AND r.status != 'completed'
            ORDER BY r.assigned_at DESC
        """, [user_id])
        assignments = cur.fetchall()
        cur.close()
        assignments = [serialize_row(a) for a in assignments]
        return jsonify({'assignments': assignments})

    @app.route('/api/volunteer/accept', methods=['POST'])
    @role_required('volunteer', 'admin')
    def accept_volunteer_request():
        user_id = int(get_jwt_identity())
        data = request.get_json()
        request_id = data.get('request_id')
        
        cur = mysql.connection.cursor()
        
        # Check if volunteer already has an active assignment
        cur.execute("SELECT COUNT(*) as count FROM requests WHERE volunteer_id = %s AND status != 'completed'", [user_id])
        active_count = cur.fetchone()['count']
        
        if active_count > 0:
            cur.close()
            return jsonify({'error': 'You already have an active assignment. Complete it first.'}), 400
        
        # Check if request is still available
        cur.execute("SELECT * FROM requests WHERE id = %s AND status = 'pending' AND volunteer_id IS NULL", [request_id])
        req = cur.fetchone()
        
        if not req:
            cur.close()
            return jsonify({'error': 'Request is no longer available'}), 400
        
        # Assign the request
        cur.execute("""
            UPDATE requests 
            SET volunteer_id = %s, status = 'assigned', assigned_at = NOW() 
            WHERE id = %s
        """, [user_id, request_id])
        
        mysql.connection.commit()
        cur.close()
        return jsonify({'msg': 'Request accepted successfully'})

    @app.route('/api/volunteer/pickup-confirmed', methods=['POST'])
    @role_required('volunteer', 'admin')
    def confirm_pickup():
        user_id = int(get_jwt_identity())
        data = request.get_json()
        request_id = data.get('request_id')
        
        cur = mysql.connection.cursor()
        
        # Verify this is the volunteer's assignment
        cur.execute("""
            SELECT * FROM requests 
            WHERE id = %s AND volunteer_id = %s AND status = 'assigned'
        """, [request_id, user_id])
        
        req = cur.fetchone()
        if not req:
            cur.close()
            return jsonify({'error': 'Assignment not found or not yours'}), 400
        
        # Update status to assigned (waiting for donor verification) and record pickup confirmation time
        cur.execute("""
            UPDATE requests 
            SET pickup_confirmed_at = NOW()
            WHERE id = %s
        """, [request_id])
        
        mysql.connection.commit()
        cur.close()
        return jsonify({'msg': 'Pickup confirmed successfully'})

    @app.route('/api/volunteer/request-delivery', methods=['POST'])
    @role_required('volunteer', 'admin')
    def request_delivery_verification():
        user_id = int(get_jwt_identity())
        data = request.get_json()
        request_id = data.get('request_id')
        
        cur = mysql.connection.cursor()
        
        # Verify this is the volunteer's assignment and pickup is verified by donor
        cur.execute("""
            SELECT * FROM requests 
            WHERE id = %s AND volunteer_id = %s AND status = 'assigned' AND pickup_verified_by_donor = TRUE
        """, [request_id, user_id])
        
        req = cur.fetchone()
        if not req:
            cur.close()
            return jsonify({'error': 'Assignment not found, not yours, or pickup not verified'}), 400
        
        # Mark delivery as confirmed (waiting for requester verification)
        cur.execute("""
            UPDATE requests 
            SET delivery_confirmed_at = NOW()
            WHERE id = %s
        """, [request_id])
        
        mysql.connection.commit()
        cur.close()
        return jsonify({'msg': 'Delivery verification requested'})

    @app.route('/api/donor/verify-pickup', methods=['POST'])
    @role_required('donor', 'admin')
    def donor_verify_pickup():
        user_id = int(get_jwt_identity())
        data = request.get_json()
        request_id = data.get('request_id')
        
        cur = mysql.connection.cursor()
        
        # Verify this is the donor's donation and pickup was confirmed
        cur.execute("""
            SELECT r.*, d.donor_id FROM requests r
            JOIN donations d ON r.food_id = d.id
            WHERE r.id = %s AND d.donor_id = %s AND r.status = 'assigned' AND r.pickup_confirmed_at IS NOT NULL
        """, [request_id, user_id])
        
        req = cur.fetchone()
        if not req:
            cur.close()
            return jsonify({'error': 'Request not found or not yours'}), 400
        
        # Update pickup verification
        cur.execute("""
            UPDATE requests 
            SET donor_verified_at = NOW(), pickup_verified_by_donor = TRUE
            WHERE id = %s
        """, [request_id])
        
        mysql.connection.commit()
        cur.close()
        return jsonify({'msg': 'Pickup verified successfully'})

    @app.route('/api/requester/verify-delivery', methods=['POST'])
    @role_required('requester', 'admin')
    def requester_verify_delivery():
        user_id = int(get_jwt_identity())
        data = request.get_json()
        request_id = data.get('request_id')
        
        cur = mysql.connection.cursor()
        
        # Verify this is the requester's request and delivery was confirmed
        cur.execute("""
            SELECT * FROM requests 
            WHERE id = %s AND requester_id = %s AND status = 'assigned' AND delivery_confirmed_at IS NOT NULL
        """, [request_id, user_id])
        
        req = cur.fetchone()
        if not req:
            cur.close()
            return jsonify({'error': 'Request not found or not yours'}), 400
        
        # Complete the request
        cur.execute("""
            UPDATE requests 
            SET status = 'completed', requester_verified_at = NOW(), delivery_verified_by_requester = TRUE, completed_at = NOW()
            WHERE id = %s
        """, [request_id])
        
        mysql.connection.commit()
        cur.close()
        return jsonify({'msg': 'Delivery verified and request completed'})

    @app.route('/api/pending-verifications')
    @jwt_required()
    def get_pending_verifications():
        user_id = int(get_jwt_identity())
        claims = get_jwt()
        user_roles = claims.get('roles', [])
        
        cur = mysql.connection.cursor()
        verifications = []
        
        # Get donor verifications
        if 'donor' in user_roles or 'admin' in user_roles:
            cur.execute("""
                SELECT r.*, d.food_name, u.username as volunteer_name, req_user.username as requester_name
                FROM requests r
                JOIN donations d ON r.food_id = d.id
                JOIN users u ON r.volunteer_id = u.id
                JOIN users req_user ON r.requester_id = req_user.id
                WHERE d.donor_id = %s AND r.status = 'assigned' AND r.pickup_confirmed_at IS NOT NULL AND r.pickup_verified_by_donor = FALSE
                ORDER BY r.assigned_at DESC
            """, [user_id])
            donor_verifications = cur.fetchall()
            for v in donor_verifications:
                v_dict = serialize_row(v)
                v_dict['verification_type'] = 'pickup'
                v_dict['role'] = 'donor'
                verifications.append(v_dict)
        
        # Get requester verifications  
        if 'requester' in user_roles or 'admin' in user_roles:
            cur.execute("""
                SELECT r.*, d.food_name, u.username as volunteer_name, donor_user.username as donor_name
                FROM requests r
                JOIN donations d ON r.food_id = d.id
                JOIN users u ON r.volunteer_id = u.id
                JOIN users donor_user ON d.donor_id = donor_user.id
                WHERE r.requester_id = %s AND r.status = 'assigned' AND r.delivery_confirmed_at IS NOT NULL AND r.delivery_verified_by_requester = FALSE
                ORDER BY r.assigned_at DESC
            """, [user_id])
            requester_verifications = cur.fetchall()
            for v in requester_verifications:
                v_dict = serialize_row(v)
                v_dict['verification_type'] = 'delivery'
                v_dict['role'] = 'requester'
                verifications.append(v_dict)
        
        cur.close()
        return jsonify({'verifications': verifications})

    # ========== UTILITY ROUTES ==========
    def check_password_hash(hashed_password, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(hashed_password, password)

    @app.route('/api/user/roles', methods=['GET'])
    @jwt_required()
    def get_user_roles():
        user_id = int(get_jwt_identity())
        cur = mysql.connection.cursor()
        cur.execute("SELECT roles FROM users WHERE id = %s", [user_id])
        user = cur.fetchone()
        cur.close()
        if user:
            user_roles = [r.strip() for r in user['roles'].split(',') if r.strip()]
            return jsonify({'roles': user_roles})
        return jsonify({'error': 'User not found'}), 404

    @app.route('/api/user/add-role', methods=['POST'])
    @jwt_required()
    def add_user_role():
        user_id = int(get_jwt_identity())
        data = request.get_json()
        new_role = data.get('role')
        
        if new_role not in ['donor', 'requester', 'volunteer', 'admin']:
            return jsonify({'error': 'Invalid role'}), 400
            
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE id = %s", [user_id])
        user = cur.fetchone()
        
        if user:
            current_roles = [r.strip() for r in user['roles'].split(',') if r.strip()]
            if new_role not in current_roles:
                current_roles.append(new_role)
                updated_roles = ','.join(current_roles)
                cur.execute("UPDATE users SET roles = %s WHERE id = %s", [updated_roles, user_id])
                mysql.connection.commit()
                
                # Generate new JWT token with updated roles
                new_access_token = create_access_token(identity=str(user['id']), additional_claims={
                    'username': user['username'],
                    'roles': current_roles
                })
                
                cur.close()
                return jsonify({
                    'msg': f'Role {new_role} added successfully', 
                    'roles': current_roles,
                    'new_access_token': new_access_token,
                    'note': 'Please use the new access token for updated permissions'
                })
            else:
                cur.close()
                return jsonify({'msg': f'Role {new_role} already exists', 'roles': current_roles})
        cur.close()
        return jsonify({'error': 'User not found'}), 404

    @app.route('/api/request', methods=['POST'])
    @role_required('requester', 'admin')
    def api_request():
        from googlemaps_helper import geocode_address, reverse_geocode
        from config import Config
        data = request.get_json(silent=True)
        user_id = int(get_jwt_identity())
        api_key = Config.GOOGLE_MAPS_API_KEY
        try:
            address = data.get('delivery_address')
            lat = data.get('latitude')
            lng = data.get('longitude')
            # If only address, geocode
            if address and (not lat or not lng):
                lat, lng = geocode_address(address, api_key)
            # If only lat/lng, reverse geocode
            if (lat and lng) and not address:
                address = reverse_geocode(lat, lng, api_key)
            request_data = {
                'food_id': int(data['food_id']),
                'requester_id': user_id,
                'quantity': int(data['quantity']),
                'delivery_address': address,
                'transport_arranged': data.get('transport') == 'arranged',
                'latitude': lat,
                'longitude': lng
            }
        except (KeyError, ValueError, TypeError) as e:
            return jsonify({'error': f'Invalid or missing field: {str(e)}'}), 422
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO requests (food_id, requester_id, quantity, delivery_address, transport_arranged, latitude, longitude)
                VALUES (%(food_id)s, %(requester_id)s, %(quantity)s, %(delivery_address)s, %(transport_arranged)s, %(latitude)s, %(longitude)s)
            """, request_data)
            mysql.connection.commit()
            cur.close()
            return jsonify({'msg': 'Request submitted successfully!'}), 201
        except Exception as e:
            mysql.connection.rollback()
            return jsonify({'error': str(e)}), 400
