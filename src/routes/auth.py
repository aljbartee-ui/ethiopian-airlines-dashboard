from flask import Blueprint, request, jsonify, session, redirect, url_for
from src.models.user import db, AdminUser
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
auth_bp = Blueprint('auth', __name__)

# NOTE: In a real application, this should be done securely, e.g., via a CLI command or a one-time setup page.
# For demonstration and initial setup, we'll use a simple setup route.
@auth_bp.route('/setup_admin', methods=['POST'])
def setup_admin():
    # Check if an admin already exists
    if AdminUser.query.first():
        return jsonify({'error': 'Admin user already exists. Cannot set up again.'}), 400

    # Hardcoded credentials for initial setup (MUST be changed in production)
    username = 'admin'
    password = 'password123' 
    
    hashed_password = generate_password_hash(password)
    
    new_admin = AdminUser(username=username, password_hash=hashed_password)
    db.session.add(new_admin)
    db.session.commit()
    
    return jsonify({'message': f'Admin user "{username}" created successfully. Please log in.'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    admin_user = AdminUser.query.filter_by(username=username).first()

    if admin_user and check_password_hash(admin_user.password_hash, password):
        session['admin_logged_in'] = True
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('admin_logged_in', None)
    return jsonify({'message': 'Logout successful'}), 200

@auth_bp.route('/status', methods=['GET'])
def status():
    return jsonify({'admin_logged_in': session.get('admin_logged_in', False)}), 200

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({'error': 'Admin authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function
