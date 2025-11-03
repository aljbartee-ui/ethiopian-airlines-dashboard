from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from src.models.sales import AdminUser
from src.models.user import db
import functools

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin authentication"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return jsonify({'error': 'Admin authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    admin = AdminUser.query.filter_by(username=username).first()
    
    if admin and check_password_hash(admin.password_hash, password):
        session['admin_id'] = admin.id
        session['admin_username'] = admin.username
        return jsonify({
            'message': 'Login successful',
            'admin': admin.to_dict()
        })
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@admin_bp.route('/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    return jsonify({'message': 'Logout successful'})

@admin_bp.route('/admin/status', methods=['GET'])
def admin_status():
    if 'admin_id' in session:
        admin = AdminUser.query.get(session['admin_id'])
        if admin:
            return jsonify({
                'authenticated': True,
                'admin': admin.to_dict()
            })
    
    return jsonify({'authenticated': False})

@admin_bp.route('/admin/create', methods=['POST'])
def create_admin():
    """Create the first admin user - only works if no admin exists"""
    existing_admin = AdminUser.query.first()
    if existing_admin:
        return jsonify({'error': 'Admin user already exists'}), 400
    
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    admin = AdminUser(
        username=username,
        password_hash=generate_password_hash(password)
    )
    
    db.session.add(admin)
    db.session.commit()
    
    return jsonify({
        'message': 'Admin user created successfully',
        'admin': admin.to_dict()
    }), 201
