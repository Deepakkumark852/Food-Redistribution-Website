from flask import render_template, request, redirect, url_for, flash, session, jsonify, current_app
import re
from datetime import datetime, date, time, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
from functools import wraps
import os
import uuid
from email_service import send_verification_email
from config import Config

# RBAC decorator
def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Handle OPTIONS requests without JWT validation
            if request.method == 'OPTIONS':
                # CORS preflight support
                response = current_app.make_default_options_response()
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
                response.headers['Access-Control-Allow-Methods'] = 'POST,GET,OPTIONS'
                return response
                
            # For non-OPTIONS requests, require JWT
            verify_jwt_in_request()
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

    # Add CORS headers to all responses
    @app.after_request
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'  # Or specific origins
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS,PUT,DELETE'
        return response

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        print('DEBUG JWT expired_token_loader called')
        return jsonify({'error': 'Session expired. Please log in again.'}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        print('DEBUG JWT invalid-token_loader called:', error)
        return jsonify({'error': 'Invalid token. Please log in again.'}), 401

    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        print('DEBUG JWT unauthorized_loader called:', error)
        return jsonify({'error': 'Missing or invalid token. Please log in again.'}), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        print('DEBUG JWT revoked_token_loader called')
        return jsonify({'error': 'Token has been revoked. Please log in again.'}), 401

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
        try:
            cur.execute("SELECT * FROM users WHERE username = %s", [username])
            user = cur.fetchone()
            
            if user and check_password_hash(user['password'], password):
                if not user['is_active']:
                    return jsonify({'error': 'Account is deactivated.'}), 403

                # Update last_login timestamp
                cur.execute("UPDATE users SET last_login = %s WHERE id = %s", (datetime.utcnow(), user['id']))
                mysql.connection.commit()

                user_roles = [r.strip() for r in user['roles'].split(',') if r.strip()]
                access_token = create_access_token(identity=user['username'], additional_claims={
                    'id': user['id'],
                    'roles': user_roles
                })
                return jsonify({'access_token': access_token, 'roles': user_roles}), 200
            else:
                return jsonify({'error': 'Invalid username or password'}), 401
        finally:
            cur.close()

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
            
            quantity = int(data['original_quantity'])

            food_data = {
                'food_name': data['food_name'],
                'original_quantity': quantity,
                'remaining_quantity': quantity, # Initially, remaining is same as original
                'expiry_date': data['expiry_date'],
                'pickup_address': address,
                'pickup_window_start': data['pickup_window_start'],
                'pickup_window_end': data['pickup_window_end'],
                'special_instructions': data.get('special_instructions', ''),
                'donor_id': user_id,
                'latitude': lat,
                'longitude': lng,
                'food_image_base64': data.get('food_image_base64') or None,
                'status': 'available' # Default status
            }
        except (KeyError, ValueError, TypeError) as e:
            return jsonify({'error': f'Invalid or missing field: {str(e)}'}), 422
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO donations 
                (food_name, original_quantity, remaining_quantity, expiry_date, pickup_address, pickup_window_start, pickup_window_end, special_instructions, donor_id, latitude, longitude, food_image_base64, status)
                VALUES (%(food_name)s, %(original_quantity)s, %(remaining_quantity)s, %(expiry_date)s, %(pickup_address)s, %(pickup_window_start)s, %(pickup_window_end)s, %(special_instructions)s, %(donor_id)s, %(latitude)s, %(longitude)s, %(food_image_base64)s, %(status)s)
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
        
        cur = mysql.connection.cursor()
        
        params = []
        
        # Start with distance calculation if location is provided
        if user_lat is not None and user_lng is not None:
            select_clause = "SELECT *, (6371 * acos(cos(radians(%s)) * cos(radians(latitude)) * cos(radians(longitude) - radians(%s)) + sin(radians(%s)) * sin(radians(latitude)))) AS distance"
            params.extend([user_lat, user_lng, user_lat])
        else:
            # If no user location, we can't calculate distance, so we select NULL.
            # The query will filter out donations without location anyway.
            select_clause = "SELECT *, NULL AS distance"

        base_query = f"{select_clause} FROM donations"
        
        # Use new schema fields for filtering
        filters = [
            "status = 'available'", 
            "remaining_quantity > 0", 
            "expiry_date >= CURDATE()",
            "latitude IS NOT NULL",
            "longitude IS NOT NULL"
        ]
        
        if filter_food:
            filters.append("food_name LIKE %s")
            params.append(f"%{filter_food}%")
        
        if filters:
            base_query += " WHERE " + " AND ".join(filters)

        if user_lat is not None and user_lng is not None:
            base_query += " ORDER BY distance ASC, created_at DESC"
        else:
            base_query += " ORDER BY created_at DESC"
            
        cur.execute(base_query, params)
        donations = cur.fetchall()
        cur.close()
        
        return jsonify({'donations': donations})

    @app.route('/api/profile', methods=['GET'])
    @jwt_required()
    def get_profile():
        claims = get_jwt()
        user_id = claims.get('id')
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, username, email, mobile, roles, created_at, last_login, profile_picture_url, is_active FROM users WHERE id = %s", [user_id])
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
        
        # Fields that can be updated
        email = data.get('email')
        mobile = data.get('mobile')
        profile_picture_url = data.get('profile_picture_url')
        roles = data.get('roles')
        special_key = data.get('special_key')

        # Validate inputs
        if email and not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            return jsonify({'error': 'Invalid email address'}), 400
        if mobile and not re.match(r'^\d{10,15}$', mobile):
            return jsonify({'error': 'Invalid mobile number'}), 400

        update_fields = []
        update_values = []

        if email:
            update_fields.append("email = %s")
            update_values.append(email)
        if mobile:
            update_fields.append("mobile = %s")
            update_values.append(mobile)
        if profile_picture_url:
            update_fields.append("profile_picture_url = %s")
            update_values.append(profile_picture_url)

        cur = mysql.connection.cursor()
        
        try:
            if update_fields:
                query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
                update_values.append(user_id)
                cur.execute(query, tuple(update_values))

            # Role updates require special handling and validation
            if roles:
                valid_roles = {'donor', 'requester', 'volunteer', 'admin'}
                roles_set = set([r.strip() for r in roles if r.strip()])
                if not roles_set.issubset(valid_roles):
                    return jsonify({'error': 'Invalid roles provided'}), 400
                
                # Admin role requires special key
                if 'admin' in roles_set:
                    from config import Config
                    if not special_key or special_key != Config.ADMIN_SPECIAL_KEY:
                        return jsonify({'error': 'Invalid or missing special key for admin role'}), 403
                
                cur.execute("UPDATE users SET roles = %s WHERE id = %s", (','.join(roles_set), user_id))

            mysql.connection.commit()

            # Fetch updated user data to return
            cur.execute("SELECT id, username, email, mobile, roles, created_at, last_login, profile_picture_url, is_active FROM users WHERE id = %s", [user_id])
            user = cur.fetchone()
            user['roles'] = [r.strip() for r in user['roles'].split(',') if r.strip()]
            
            return jsonify({'msg': 'Profile updated successfully', 'user': serialize_row(user)})
        
        except Exception as e:
            mysql.connection.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            cur.close()

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

    # ========== NOTIFICATIONS API ROUTES ==========
    @app.route('/api/notifications', methods=['GET'])
    @jwt_required()
    def get_notifications():
        claims = get_jwt()
        user_id = claims.get('id')
        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                SELECT id, message, is_read, link, created_at 
                FROM notifications 
                WHERE user_id = %s 
                ORDER BY created_at DESC
            """, [user_id])
            notifications = [serialize_row(n) for n in cur.fetchall()]
            return jsonify({'notifications': notifications})
        finally:
            cur.close()

    @app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
    @jwt_required()
    def mark_notification_as_read(notification_id):
        claims = get_jwt()
        user_id = claims.get('id')
        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                UPDATE notifications 
                SET is_read = TRUE 
                WHERE id = %s AND user_id = %s
            """, [notification_id, user_id])
            mysql.connection.commit()
            if cur.rowcount == 0:
                return jsonify({'error': 'Notification not found or not owned by user'}), 404
            return jsonify({'msg': 'Notification marked as read'})
        except Exception as e:
            mysql.connection.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            cur.close()

    # ========== UTILITY ROUTES ==========
    def check_password_hash(hashed_password, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(hashed_password, password)

    @app.route('/api/request', methods=['POST', 'OPTIONS'])
    @app.route('/api/requests', methods=['POST', 'OPTIONS'])
    @role_required('requester', 'admin')
    def api_request():
        from googlemaps_helper import geocode_address, reverse_geocode
        from config import Config
        data = request.get_json(silent=True)
        claims = get_jwt()
        user_id = claims.get('id')
        api_key = Config.GOOGLE_MAPS_API_KEY
        
        try:
            food_id = int(data['food_id'])
            quantity_requested = int(data['quantity'])
            delivery_address = data.get('delivery_address')
            lat = data.get('latitude')
            lng = data.get('longitude')

            if delivery_address and (not lat or not lng):
                lat, lng = geocode_address(delivery_address, api_key)
            if (lat and lng) and not delivery_address:
                delivery_address = reverse_geocode(lat, lng, api_key)

        except (KeyError, ValueError, TypeError) as e:
            return jsonify({'error': f'Invalid or missing field: {str(e)}'}), 422

        cur = mysql.connection.cursor()
        try:
            # Lock the donation row to prevent race conditions
            cur.execute("SELECT remaining_quantity, status FROM donations WHERE id = %s FOR UPDATE", [food_id])
            donation = cur.fetchone()

            if not donation:
                return jsonify({'error': 'Donation not found'}), 404
            if donation['status'] != 'available':
                return jsonify({'error': f"Donation is no longer available (status: {donation['status']})"}), 409
            if donation['remaining_quantity'] < quantity_requested:
                return jsonify({'error': f"Not enough quantity available. Only {donation['remaining_quantity']} left."}), 409

            # Create the request
            request_data = {
                'food_id': food_id,
                'requester_id': user_id,
                'quantity': quantity_requested,
                'delivery_address': delivery_address,
                'delivery_latitude': lat,
                'delivery_longitude': lng,
                'transport_arranged': data.get('transport_arranged', False),
                'status': 'pending'
            }
            cur.execute("""
                INSERT INTO requests (food_id, requester_id, quantity, status, delivery_address, delivery_latitude, delivery_longitude, transport_arranged)
                VALUES (%(food_id)s, %(requester_id)s, %(quantity)s, %(status)s, %(delivery_address)s, %(delivery_latitude)s, %(delivery_longitude)s, %(transport_arranged)s)
            """, request_data)
            
            # Update donation's remaining quantity and status
            new_remaining_quantity = donation['remaining_quantity'] - quantity_requested
            new_status = 'fully_claimed' if new_remaining_quantity == 0 else 'available'
            
            cur.execute("""
                UPDATE donations SET remaining_quantity = %s, status = %s WHERE id = %s
            """, (new_remaining_quantity, new_status, food_id))

            mysql.connection.commit()
            return jsonify({'msg': 'Request submitted successfully!'}), 201

        except Exception as e:
            mysql.connection.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            cur.close()

    # ========== VOLUNTEER API ROUTES ==========
    
    @app.route('/api/volunteer/pending', methods=['GET', 'OPTIONS'])
    @role_required('volunteer', 'admin')
    def api_volunteer_pending():
        """Returns all pending food requests that need a volunteer"""
        if request.method == 'OPTIONS':
            return jsonify({'msg': 'OK'})
            
        cur = mysql.connection.cursor()
        try:
            # Get user's location for distance calculation
            cur.execute("""
                SELECT r.id, r.food_id, r.requester_id, r.quantity, r.delivery_address, r.requested_at, 
                       d.food_name, d.pickup_address, d.special_instructions, 
                       d.latitude as donor_lat, d.longitude as donor_lng,
                       r.delivery_latitude, r.delivery_longitude,
                       u.username as requester_name, 
                       u2.username as donor_name,
                       u2.email as donor_email, 
                       u2.mobile as donor_mobile,
                       r.transport_arranged
                FROM requests r
                JOIN donations d ON r.food_id = d.id
                JOIN users u ON r.requester_id = u.id
                JOIN users u2 ON d.donor_id = u2.id
                WHERE r.status = 'pending' AND r.volunteer_id IS NULL
                ORDER BY r.requested_at DESC
            """)
            
            pending_requests = cur.fetchall()
            pending_requests = [serialize_row(r) for r in pending_requests]
            
            return jsonify({'pending_requests': pending_requests})
        finally:
            cur.close()
    
    @app.route('/api/volunteer/assignments', methods=['GET', 'OPTIONS'])
    @role_required('volunteer', 'admin')
    def api_volunteer_assignments():
        """Returns all active assignments for a volunteer"""
        if request.method == 'OPTIONS':
            return jsonify({'msg': 'OK'})

        claims = get_jwt()
        user_id = claims.get('id')
        
        cur = mysql.connection.cursor()
        try:
            # Fetch assignments in any active state
            cur.execute("""
                SELECT r.id, r.food_id, r.requester_id, r.quantity, r.delivery_address, 
                       r.status, r.assigned_at, r.transport_arranged,
                       d.food_name, d.pickup_address, d.special_instructions,
                       d.latitude as donor_lat, d.longitude as donor_lng,
                       r.delivery_latitude, r.delivery_longitude,
                       u.username as requester_name, u.email as requester_email, u.mobile as requester_mobile,
                       u2.username as donor_name, u2.email as donor_email, u2.mobile as donor_mobile
                FROM requests r
                JOIN donations d ON r.food_id = d.id
                JOIN users u ON r.requester_id = u.id
                JOIN users u2 ON d.donor_id = u2.id
                WHERE r.volunteer_id = %s AND r.status IN ('assigned', 'pickup_pending_verification', 'in_transit', 'delivery_pending_verification')
                ORDER BY r.assigned_at DESC
            """, (user_id,))
            
            assignments = cur.fetchall()
            assignments = [serialize_row(a) for a in assignments]
            
            return jsonify({'assignments': assignments})
        finally:
            cur.close()
    
    @app.route('/api/volunteer/accept', methods=['POST', 'OPTIONS'])
    @role_required('volunteer', 'admin')
    def api_volunteer_accept():
        """Assigns a volunteer to a pending food request"""
        if request.method == 'OPTIONS':
            return jsonify({'msg': 'OK'})

        data = request.get_json()
        request_id = data.get('request_id')
        
        if not request_id:
            return jsonify({'error': 'Request ID is required'}), 400

        claims = get_jwt()
        volunteer_id = claims.get('id')

        cur = mysql.connection.cursor()
        try:
            # Check if the request is available and lock the row
            cur.execute("SELECT volunteer_id, status FROM requests WHERE id = %s FOR UPDATE", (request_id,))
            req = cur.fetchone()
            
            if not req:
                return jsonify({'error': 'Request not found'}), 404
            if req['volunteer_id'] is not None or req['status'] != 'pending':
                return jsonify({'error': 'Request is no longer available'}), 409

            # Assign the volunteer
            cur.execute("""
                UPDATE requests 
                SET volunteer_id = %s, status = 'assigned', assigned_at = %s
                WHERE id = %s
            """, (volunteer_id, datetime.utcnow(), request_id))
            
            mysql.connection.commit()
            
            return jsonify({'msg': 'Request accepted successfully'}), 200
        except Exception as e:
            mysql.connection.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            cur.close()

    @app.route('/api/volunteer/assignment/<int:assignment_id>', methods=['GET', 'OPTIONS'])
    @role_required('volunteer', 'admin')
    def api_volunteer_assignment_details(assignment_id):
        """Returns details of a specific volunteer assignment"""
        if request.method == 'OPTIONS':
            return jsonify({'msg': 'OK'})
            
        claims = get_jwt()
        user_id = claims.get('id')
        
        cur = mysql.connection.cursor()
        try:
            # Get assignment details including donor and requester info for navigation
            cur.execute("""
                SELECT r.id, r.food_id, r.requester_id, r.quantity, r.delivery_address,
                       r.status, r.assigned_at, r.transport_arranged,
                       r.delivery_latitude, r.delivery_longitude,
                       d.food_name, d.pickup_address, d.special_instructions, d.food_image_base64,
                       d.latitude as donor_lat, d.longitude as donor_lng, 
                       d.donor_id, d.expiry_date, d.original_quantity, d.remaining_quantity,
                       d.pickup_window_start, d.pickup_window_end,
                       u.username as requester_name, u.email as requester_email, u.mobile as requester_mobile,
                       u2.username as donor_name, u2.email as donor_email, u2.mobile as donor_mobile
                FROM requests r
                JOIN donations d ON r.food_id = d.id
                JOIN users u ON r.requester_id = u.id
                JOIN users u2 ON d.donor_id = u2.id
                WHERE r.id = %s AND r.volunteer_id = %s
            """, (assignment_id, user_id))
            
            assignment = cur.fetchone()
            
            if not assignment:
                return jsonify({'error': 'Assignment not found or not assigned to you'}), 404
                
            return jsonify({'assignment': assignment})
        finally:
            cur.close()
            
    @app.route('/api/assignment/<int:assignment_id>/initiate-pickup', methods=['POST'])
    @role_required('volunteer')
    def initiate_pickup(assignment_id):
        claims = get_jwt()
        volunteer_id = claims.get('id')
        
        cur = mysql.connection.cursor()
        try:
            # Verify assignment and get donor details
            cur.execute("""
                SELECT r.status, d.donor_id, u_donor.email as donor_email, u_donor.username as donor_name,
                       u_volunteer.username as volunteer_name, d.food_name
                FROM requests r
                JOIN donations d ON r.food_id = d.id
                JOIN users u_donor ON d.donor_id = u_donor.id
                JOIN users u_volunteer ON r.volunteer_id = u_volunteer.id
                WHERE r.id = %s AND r.volunteer_id = %s
            """, (assignment_id, volunteer_id))
            details = cur.fetchone()

            if not details:
                return jsonify({'error': 'Assignment not found or invalid.'}), 404
            if details['status'] != 'assigned':
                return jsonify({'error': f"Cannot initiate pickup. Status is '{details['status']}' not 'assigned'."}), 409

            # Generate a unique token for verification
            token = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(hours=24)
            
            # Create verification entry
            cur.execute("""
                INSERT INTO verifications (request_id, user_id, token, type, expires_at)
                VALUES (%s, %s, %s, 'pickup', %s)
            """, (assignment_id, details['donor_id'], token, expires_at))

            # Update request status
            cur.execute("UPDATE requests SET status = 'pickup_pending_verification' WHERE id = %s", (assignment_id,))

            # Send email to donor
            verification_link = f"{Config.FRONTEND_URL}/verify?token={token}"
            send_verification_email(
                to_email=details['donor_email'],
                recipient_name=details['donor_name'],
                volunteer_name=details['volunteer_name'],
                food_name=details['food_name'],
                verification_type='pickup',
                verification_link=verification_link
            )
            
            mysql.connection.commit()
            return jsonify({'message': 'Pickup verification email sent to donor.'}), 200
        except Exception as e:
            mysql.connection.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            cur.close()

    @app.route('/api/assignment/<int:assignment_id>/initiate-delivery', methods=['POST'])
    @role_required('volunteer')
    def initiate_delivery(assignment_id):
        claims = get_jwt()
        volunteer_id = claims.get('id')
        
        cur = mysql.connection.cursor()
        try:
            # Verify assignment and get requester details
            cur.execute("""
                SELECT r.status, r.requester_id, u_requester.email as requester_email, u_requester.username as requester_name,
                       u_volunteer.username as volunteer_name, d.food_name
                FROM requests r
                JOIN donations d ON r.food_id = d.id
                JOIN users u_requester ON r.requester_id = u_requester.id
                JOIN users u_volunteer ON r.volunteer_id = u_volunteer.id
                WHERE r.id = %s AND r.volunteer_id = %s
            """, (assignment_id, volunteer_id))
            details = cur.fetchone()

            if not details:
                return jsonify({'error': 'Assignment not found or invalid.'}), 404
            if details['status'] != 'in_transit':
                return jsonify({'error': f"Cannot initiate delivery. Status is '{details['status']}' not 'in_transit'."}), 409

            # Generate a unique token for verification
            token = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(hours=24)
            
            # Create verification entry
            cur.execute("""
                INSERT INTO verifications (request_id, user_id, token, type, expires_at)
                VALUES (%s, %s, %s, 'delivery', %s)
            """, (assignment_id, details['requester_id'], token, expires_at))

            # Update request status
            cur.execute("UPDATE requests SET status = 'delivery_pending_verification' WHERE id = %s", (assignment_id,))

            # Send email to requester
            verification_link = f"{Config.FRONTEND_URL}/verify?token={token}"
            send_verification_email(
                to_email=details['requester_email'],
                recipient_name=details['requester_name'],
                volunteer_name=details['volunteer_name'],
                food_name=details['food_name'],
                verification_type='delivery',
                verification_link=verification_link
            )
            
            mysql.connection.commit()
            return jsonify({'message': 'Delivery verification email sent to requester.'}), 200
        except Exception as e:
            mysql.connection.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            cur.close()

    @app.route('/api/verify', methods=['POST'])
    def verify_action():
        token = request.json.get('token')
        if not token:
            return jsonify({'error': 'Token is required.'}), 400

        cur = mysql.connection.cursor()
        try:
            # Find the verification record, lock it
            cur.execute("SELECT * FROM verifications WHERE token = %s AND is_verified = FALSE AND expires_at > NOW() FOR UPDATE", (token,))
            verification = cur.fetchone()

            if not verification:
                return jsonify({'error': 'Invalid, expired, or already used token.'}), 404

            # Update verification status
            cur.execute("UPDATE verifications SET is_verified = TRUE, verified_at = NOW() WHERE id = %s", (verification['id'],))
            
            request_id = verification['request_id']
            
            # Update request status based on verification type
            if verification['type'] == 'pickup':
                new_status = 'in_transit'
                cur.execute("UPDATE requests SET status = %s WHERE id = %s", (new_status, request_id))
                # Notify volunteer
                cur.execute("SELECT volunteer_id FROM requests WHERE id = %s", (request_id,))
                volunteer = cur.fetchone()
                if volunteer:
                    cur.execute("INSERT INTO notifications (user_id, message, link) VALUES (%s, %s, %s)", 
                                (volunteer['volunteer_id'], "Pickup confirmed. You can now proceed to delivery.", f"/volunteer/assignment/{request_id}"))

            elif verification['type'] == 'delivery':
                new_status = 'completed'
                cur.execute("UPDATE requests SET status = %s, completed_at = NOW() WHERE id = %s", (new_status, request_id))
                
                # Add notifications for requester, donor, and volunteer
                cur.execute("""
                    SELECT r.requester_id, r.volunteer_id, d.donor_id, d.food_name
                    FROM requests r JOIN donations d ON r.food_id = d.id
                    WHERE r.id = %s
                """, (request_id,))
                ids = cur.fetchone()

                if ids:
                    # Requester
                    cur.execute("INSERT INTO notifications (user_id, message, link) VALUES (%s, %s, %s)", 
                                (ids['requester_id'], f"Your request for '{ids['food_name']}' is complete. Thank you!", "/history"))
                    # Donor
                    cur.execute("INSERT INTO notifications (user_id, message, link) VALUES (%s, %s, %s)", 
                                (ids['donor_id'], f"Your donation of '{ids['food_name']}' has been successfully delivered.", "/history"))
                    # Volunteer
                    cur.execute("INSERT INTO notifications (user_id, message, link) VALUES (%s, %s, %s)", 
                                (ids['volunteer_id'], f"Delivery of '{ids['food_name']}' is complete. Great job!", "/history"))

            mysql.connection.commit()
            return jsonify({'message': f"{verification['type'].capitalize()} verified successfully.", 'status': new_status}), 200
        except Exception as e:
            mysql.connection.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            cur.close()

    @app.route('/api/verifications/pending', methods=['GET'])
    @jwt_required()
    def get_pending_verifications():
        claims = get_jwt()
        user_id = claims.get('id')
        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                SELECT 
                    v.id, v.token, v.type,
                    r.id as request_id,
                    d.food_name,
                    u.username as volunteer_name
                FROM verifications v
                JOIN requests r ON v.request_id = r.id
                JOIN donations d ON r.food_id = d.id
                JOIN users u ON r.volunteer_id = u.id
                WHERE v.user_id = %s AND v.is_verified = FALSE AND v.expires_at > NOW()
                ORDER BY v.created_at DESC
            """, (user_id,))
            verifications = cur.fetchall()
            return jsonify({'verifications': [serialize_row(v) for v in verifications]})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            cur.close()

    # This route is now obsolete as completion is handled by the verification flow.
    # @app.route('/api/volunteer/assignment/<int:assignment_id>/complete', methods=['POST'])
    # @role_required('volunteer', 'admin')
    # def api_volunteer_assignment_complete(assignment_id):
    # ... (code removed) ...

    # Register the Blueprints
    # app.register_blueprint(bp)
