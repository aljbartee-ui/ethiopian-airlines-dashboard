from flask import Blueprint, request, jsonify, session
from src.models.user import db
from src.models.sales import AdminUser
from werkzeug.security import check_password_hash, generate_password_hash

admin_bp = Blueprint('admin', __name__)

def ensure_admin_user():
    """Ensure admin user exists"""
    try:
        admin = AdminUser.query.filter_by(username='admin').first()
        if not admin:
            admin = AdminUser(
                username='admin',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()
            return True
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error creating admin user: {e}")
        return False

@admin_bp.route('/admin/create', methods=['POST'])
def create_admin():
    """Create admin user endpoint"""
    try:
        if ensure_admin_user():
            return jsonify({'message': 'Admin user created successfully'})
        else:
            return jsonify({'error': 'Failed to create admin user'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/admin/login', methods=['POST'])
def admin_login():
    """Admin login endpoint"""
    try:
        # Ensure admin user exists
        ensure_admin_user()
        
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        admin = AdminUser.query.filter_by(username=username).first()
        
        if admin and check_password_hash(admin.password_hash, password):
            session['admin_logged_in'] = True
            session['admin_user_id'] = admin.id
            return jsonify({'message': 'Login successful'})
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/admin/logout', methods=['POST'])
def admin_logout():
    """Admin logout endpoint"""
    session.pop('admin_logged_in', None)
    session.pop('admin_user_id', None)
    return jsonify({'message': 'Logout successful'})

@admin_bp.route('/admin/status')
def admin_status():
    """Check admin login status"""
    is_logged_in = session.get('admin_logged_in', False)
    return jsonify({'logged_in': is_logged_in})
