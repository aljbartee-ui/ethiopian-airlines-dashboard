import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, session, request, jsonify, redirect
from src.models.user import db
from src.models.sales import SalesData, AdminUser
from src.routes.user import user_bp
from src.routes.admin_fixed import admin_bp
from src.routes.sales_working import sales_bp
from src.routes.charts_redesigned import charts_bp
from src.routes.flight_load import flight_load_bp
from src.routes.route_analysis import route_analysis_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Register blueprints with correct URL prefixes
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(admin_bp, url_prefix='/api')
app.register_blueprint(sales_bp, url_prefix='/api')
app.register_blueprint(charts_bp, url_prefix='/api')
app.register_blueprint(flight_load_bp, url_prefix='/api/flight-load')
app.register_blueprint(route_analysis_bp, url_prefix='/flight-load/route-analysis')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create database tables
with app.app_context():
    try:
        db.create_all()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")

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
    from datetime import datetime, timedelta
    
    # Check if user is authenticated
    is_admin = session.get('admin_logged_in', False)
    is_public = session.get('public_authenticated', False)
    
    # Check session timeout (1 hour)
    last_activity = session.get('last_activity')
    if last_activity:
        last_activity_time = datetime.fromisoformat(last_activity)
        if datetime.now() - last_activity_time > timedelta(hours=1):
            # Session expired
            session.clear()
            return send_from_directory(app.static_folder, 'sales-login.html')
    
    # If not authenticated, redirect to login
    if not is_admin and not is_public:
        return send_from_directory(app.static_folder, 'sales-login.html')
    
    # Update last activity time
    session['last_activity'] = datetime.now().isoformat()
    
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404
    return send_from_directory(static_folder_path, 'dashboard.html')

@app.route('/flight-load')
def flight_load():
    """Serve the flight load menu page"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404
    return send_from_directory(static_folder_path, 'flight-load-menu.html')

@app.route('/flight-load/load-factor')
def flight_load_factor():
    """Serve the load factor dashboard"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404
    return send_from_directory(static_folder_path, 'flight-load-factor.html')

@app.route('/flight-load/route-analysis')
def flight_load_route_analysis():
    """Serve the route analysis dashboard under flight load"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404
    return send_from_directory(static_folder_path, 'flight-load-route-analysis.html')

@app.route('/admin')
def admin_panel():
    """Serve the admin panel"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404
    return send_from_directory(static_folder_path, 'admin.html')

# Legacy route - redirect to new location
@app.route('/route-analysis')
def route_analysis_redirect():
    """Redirect old route analysis URL to new location"""
    return redirect('/flight-load/route-analysis', code=301)

# Public authentication endpoints
@app.route('/api/public/login', methods=['POST'])
def public_login():
    """Simple password authentication for public viewers"""
    from datetime import datetime
    
    data = request.get_json()
    password = data.get('password', '')
    
    # Simple password check (you can change this password)
    PUBLIC_PASSWORD = os.environ.get('PUBLIC_PASSWORD', 'ethiopian2025')
    
    if password == PUBLIC_PASSWORD:
        session['public_authenticated'] = True
        session['last_activity'] = datetime.now().isoformat()
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
