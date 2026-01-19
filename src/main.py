import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, session, jsonify, request
from src.models.user import db
from src.models.sales import SalesData, AdminUser
from src.routes.user import user_bp
from src.routes.admin_fixed import admin_bp
from src.routes.sales_working import sales_bp
from src.routes.charts_redesigned import charts_bp
from src.routes.flight_load import flight_load_bp
from src.routes.manifest import manifest_bp
from src.routes.route_analysis import route_analysis_bp
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(admin_bp, url_prefix='/api')
app.register_blueprint(sales_bp, url_prefix='/api')
app.register_blueprint(charts_bp, url_prefix='/api')
app.register_blueprint(flight_load_bp, url_prefix='/api/flight-load')
app.register_blueprint(manifest_bp, url_prefix='/api')
app.register_blueprint(route_analysis_bp, url_prefix='/api/route-analysis')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

# Public view password (can be changed by admin)
PUBLIC_VIEW_PASSWORD = os.environ.get('PUBLIC_VIEW_PASSWORD', 'ethiopian2024')

@app.route('/')
def home():
    """Serve the home page"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404
    return send_from_directory(static_folder_path, 'index.html')

@app.route('/sales-report')
def sales_report():
    """Serve sales report page (requires authentication)"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404
    return send_from_directory(static_folder_path, 'sales-login.html')

@app.route('/dashboard')
def dashboard():
    """Serve the dashboard (requires authentication)"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404
    return send_from_directory(static_folder_path, 'dashboard.html')

@app.route('/flight-analysis')
def flight_analysis():
    """Serve flight analysis menu page"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404
    return send_from_directory(static_folder_path, 'flight-load-menu.html')

@app.route('/load-factor')
def load_factor():
    """Serve load factor page"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404
    return send_from_directory(static_folder_path, 'load-factor.html')

@app.route('/routes-analysis')
def routes_analysis():
    """Serve routes analysis page"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404
    return send_from_directory(static_folder_path, 'routes-analysis.html')

# Authentication endpoints
@app.route('/api/auth/public-login', methods=['POST'])
def public_login():
    """Public view password authentication"""
    data = request.get_json()
    password = data.get('password', '')
    
    if password == PUBLIC_VIEW_PASSWORD:
        session['public_authenticated'] = True
        return jsonify({'success': True, 'message': 'Authentication successful'})
    else:
        return jsonify({'success': False, 'error': 'Invalid password'}), 401

@app.route('/api/auth/public-status')
def public_status():
    """Check public authentication status"""
    is_public = session.get('public_authenticated', False)
    is_admin = session.get('admin_logged_in', False)
    return jsonify({
        'public_authenticated': is_public,
        'admin_authenticated': is_admin,
        'authenticated': is_public or is_admin
    })

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout from all sessions"""
    session.pop('public_authenticated', None)
    session.pop('admin_logged_in', None)
    session.pop('admin_user_id', None)
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/<path:path>')
def serve(path):
    """Serve static files"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404
    
    if os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        return "File not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
