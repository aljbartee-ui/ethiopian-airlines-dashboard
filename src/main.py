import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, session, request, jsonify
from src.models.user import db
from src.models.sales import SalesData, AdminUser
from src.routes.user import user_bp
from src.routes.admin_fixed import admin_bp
from src.routes.sales_working import sales_bp
from src.routes.charts_redesigned import charts_bp
from src.routes.flight_load import flight_load_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(admin_bp, url_prefix='/api')
app.register_blueprint(sales_bp, url_prefix='/api')
app.register_blueprint(charts_bp, url_prefix='/api')
app.register_blueprint(flight_load_bp, url_prefix='/api/flight-load')

# uncomment if you need to use database
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    """Serve the home page"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404
    return send_from_directory(static_folder_path, 'index.html')

@app.route('/sales-report')
def sales_report():
    """Redirect to sales login page"""
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

@app.route('/flight-load')
def flight_load():
    """Serve the flight load dashboard"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404
    return send_from_directory(static_folder_path, 'flight-load.html')

@app.route('/admin')
def admin_panel():
    """Serve the admin panel"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404
    return send_from_directory(static_folder_path, 'admin.html')

# Public authentication endpoints
@app.route('/api/public/login', methods=['POST'])
def public_login():
    """Simple password authentication for public viewers"""
    data = request.get_json()
    password = data.get('password', '')
    
    # Simple password check (you can change this password)
    PUBLIC_PASSWORD = os.environ.get('PUBLIC_PASSWORD', 'ethiopian2025')
    
    if password == PUBLIC_PASSWORD:
        session['public_authenticated'] = True
        return jsonify({'success': True, 'message': 'Authentication successful'})
    else:
        return jsonify({'success': False, 'message': 'Invalid password'}), 401

@app.route('/api/public/status')
def public_status():
    """Check if user is authenticated"""
    is_authenticated = session.get('public_authenticated', False) or session.get('admin_logged_in', False)
    return jsonify({'authenticated': is_authenticated})

@app.route('/api/public/logout', methods=['POST'])
def public_logout():
    """Logout public user"""
    session.pop('public_authenticated', None)
    return jsonify({'success': True})

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
