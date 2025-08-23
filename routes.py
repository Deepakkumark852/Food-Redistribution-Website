from flask import render_template, request, redirect, url_for, flash, session, jsonify
import re
from datetime import datetime
from werkzeug.security import generate_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from functools import wraps

# RBAC decorator
def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            user = get_jwt_identity()
            if user['role'] not in roles:
                return jsonify({'msg': 'Forbidden'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def init_routes(app, mysql):
    # JWT setup
    app.config['JWT_SECRET_KEY'] = app.config.get('SECRET_KEY', 'dev-key-123')
    jwt = JWTManager(app)

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
            SELECT d.*, u.username AS donor_name
            FROM donations d
            JOIN users u ON d.donor_id = u.id
            WHERE d.id = %s
        """, [food_id])
        food = cur.fetchone()
        cur.close()
        
        if food:
            return jsonify({
                'id': food['id'],
                'food_name': food['food_name'],
                'quantity': food['quantity'],
                'donor_name': food['donor_name'],
                'expiry_date': str(food['expiry_date']),
                'pickup_address': food['pickup_address'],
                'pickup_time': str(food['pickup_time'])
            })
        return jsonify({'error': 'Food not found'}), 404

    @app.route('/api/register', methods=['POST'])
    def api_register():
        data = request.get_json()
        username = data.get('username')
        password = generate_password_hash(data.get('password'))
        email = data.get('email')
        mobile = data.get('mobile')
        role = data.get('role', 'donor')
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
        if role == 'admin':
            # Only allow admin registration if special_key matches
            from config import Config
            if not special_key or special_key != Config.ADMIN_SPECIAL_KEY:
                return jsonify({'error': 'Invalid or missing special key for admin registration'}), 403
        try:
            cur = mysql.connection.cursor()
            cur.execute(
                "INSERT INTO users (username, password, email, mobile, role) VALUES (%s, %s, %s, %s, %s)",
                (username, password, email, mobile, role)
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
            access_token = create_access_token(identity={'id': user['id'], 'username': user['username'], 'role': user['role']})
            return jsonify({'access_token': access_token, 'role': user['role']}), 200
        else:
            return jsonify({'error': 'Invalid username or password'}), 401

    @app.route('/api/donate', methods=['POST'])
    @role_required('donor', 'admin')
    def api_donate():
        data = request.get_json()
        user = get_jwt_identity()
        food_data = {
            'food_name': data['food_name'],
            'quantity': int(data['quantity']),
            'expiry_date': data['expiry_date'],
            'pickup_address': data['pickup_address'],
            'pickup_time': data['pickup_time'],
            'special_instructions': data.get('special_instructions', ''),
            'donor_id': user['id']
        }
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO donations 
                (food_name, quantity, expiry_date, pickup_address, pickup_time, special_instructions, donor_id)
                VALUES (%(food_name)s, %(quantity)s, %(expiry_date)s, %(pickup_address)s, %(pickup_time)s, %(special_instructions)s, %(donor_id)s)
            """, food_data)
            mysql.connection.commit()
            cur.close()
            return jsonify({'msg': 'Food donation submitted successfully!'}), 201
        except Exception as e:
            mysql.connection.rollback()
            return jsonify({'error': str(e)}), 400

    # ========== UTILITY ROUTES ==========
    def check_password_hash(hashed_password, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(hashed_password, password)
