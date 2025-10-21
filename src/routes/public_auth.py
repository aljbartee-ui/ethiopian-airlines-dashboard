from flask import Blueprint, jsonify, request, session

public_auth_bp = Blueprint('public_auth', __name__)

# Single shared password for all public viewers
PUBLIC_PASSWORD = "ethiopian2025"

@public_auth_bp.route('/public/login', methods=['POST'])
def public_login():
    """Public viewer login with shared password"""
    try:
        data = request.json
        password = data.get('password', '')
        
        if password == PUBLIC_PASSWORD:
            session['public_authenticated'] = True
            return jsonify({'success': True, 'message': 'Access granted'}), 200
        else:
            return jsonify({'success': False, 'error': 'Invalid password'}), 401
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@public_auth_bp.route('/public/logout', methods=['POST'])
def public_logout():
    """Public viewer logout"""
    session.pop('public_authenticated', None)
    return jsonify({'success': True, 'message': 'Logged out'}), 200

@public_auth_bp.route('/public/status', methods=['GET'])
def public_status():
    """Check if public viewer is authenticated"""
    is_authenticated = session.get('public_authenticated', False)
    return jsonify({'authenticated': is_authenticated}), 200

