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
        return jsonify({'error': 'Invalid token. Please log in again.'}), 401

    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        print('DEBUG JWT unauthorized_loader called:', error)
        return jsonify({'error': 'Missing or invalid token. Please log in again.'}), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        print('DEBUG JWT revoked_token_loader called')
        return jsonify({'error': 'Token has been revoked. Please log in again.'}), 401

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
                if new_quantity > 0:
                    cur.execute("""
                        UPDATE donations SET quantity = %s WHERE id = %s
                    """, (new_quantity, request_data['food_id']))
                else:
                    cur.execute("DELETE FROM donations WHERE id = %s", [request_data['food_id']])
                
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
            access_token = create_access_token(identity=user['username'], additional_claims={
                'id': user['id'],
                'roles': user_roles
            })
            return jsonify({'access_token': access_token, 'roles': user_roles}), 200
        else:
            return jsonify({'error': 'Invalid username or password'}), 401

    @app.route('/api/donate', methods=['POST'])
    @role_required('donor', 'admin')
    def api_donate():
        from googlemaps_helper import geocode_address, reverse_geocode
        data = request.get_json(silent=True)
        claims = get_jwt()
        user_id = claims.get('id')
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
        claims = get_jwt()
        user_id = claims.get('id')
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
        claims = get_jwt()
        user_id = claims.get('id')
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
        claims = get_jwt()
        user_id = claims.get('id')
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
        # Converts all datetime/date/time/timedelta fields to string
        result = {}
        for k, v in row.items():
            if isinstance(v, (datetime, date, time, timedelta)):
                result[k] = str(v)
            else:
                result[k] = v
        return result

    @app.route('/api/history/donations')
    @role_required('donor', 'admin')
    def donation_history():
        claims = get_jwt()
        user_id = claims.get('id')
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
        claims = get_jwt()
        user_id = claims.get('id')
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
        claims = get_jwt()
        user_id = claims.get('id')
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

    # ========== UTILITY ROUTES ==========
    def check_password_hash(hashed_password, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(hashed_password, password)

    @app.route('/api/request', methods=['POST'])
    @role_required('requester', 'admin')
    def api_request():
        from googlemaps_helper import geocode_address, reverse_geocode
        from config import Config
        data = request.get_json(silent=True)
        claims = get_jwt()
        user_id = claims.get('id')
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
