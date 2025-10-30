"""
Ethiopian Airlines Analytics Portal
Main application file with all routes
"""

from flask import Flask, render_template, send_from_directory, redirect, url_for
from src.models.sales import db
from src.routes.sales_working import sales_bp
from src.routes.flight_load import flight_load_bp
from src.routes.route_analysis import route_analysis_bp
from src.routes.manifest import manifest_bp
from src.models.user import User
from src.models.sales import SalesData
from src.models.flight_load import FlightLoad
from src.models.route_analysis import RouteAnalysisWeek, RouteAnalysisUpload
from src.models.manifest import DailyManifest
import os

app = Flask(__name__, 
            static_folder='src/static',
            template_folder='src/templates')

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ethiopian-airlines-secret-key-2025')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///ethiopian_airlines.db')
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Initialize database
db.init_app(app)

# Register blueprints
app.register_blueprint(sales_bp, url_prefix='/sales')
app.register_blueprint(flight_load_bp, url_prefix='/flight-load')
app.register_blueprint(route_analysis_bp, url_prefix='/flight-load/route-analysis')
app.register_blueprint(manifest_bp, url_prefix='/flight-load/manifest')

# Create tables
with app.app_context():
    db.create_all()
    print("✅ Database tables created successfully")

@app.route('/')
def index():
    """Serve the home page"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404
    return send_from_directory(static_folder_path, 'index.html')

@app.route('/dashboard')
def dashboard():
    """Serve the sales dashboard"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404
    return send_from_directory(static_folder_path, 'dashboard.html')

@app.route('/flight-load-dashboard')
def flight_load_dashboard():
    """Redirect to flight load menu"""
    return redirect('/flight-load/menu')

@app.route('/flight-load/menu')
def flight_load_menu():
    """Serve the flight load menu page"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404
    return send_from_directory(static_folder_path, 'flight-load-menu.html')

@app.route('/flight-load/load-factor')
def flight_load_factor():
    """Serve the flight load factor dashboard"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404
    return send_from_directory(static_folder_path, 'flight-load-factor.html')

@app.route('/flight-load/route-analysis')
def flight_load_route_analysis():
    """Serve the route analysis dashboard"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404
    return send_from_directory(static_folder_path, 'flight-load-route-analysis.html')

@app.route('/flight-load/manifest-dashboard')
def manifest_dashboard():
    """Serve the manifest dashboard"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404
    return send_from_directory(static_folder_path, 'manifest-dashboard.html')

@app.route('/route-analysis')
def route_analysis_redirect():
    """Redirect old route-analysis URL to new location"""
    return redirect('/flight-load/route-analysis')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

