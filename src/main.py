from flask import Flask, send_from_directory, render_template
from src.models.user import db, User, AdminUser
from src.models.sales import SalesData
from src.models.flight_load import FlightLoadRecord
from src.models.route_analysis import RouteAnalysisWeek, RouteAnalysisUpload
from src.models.manifest import DailyManifest, RouteForecast, AirportMaster
import os

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ethiopian-airlines-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///ethiopian_airlines.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload

# Initialize database
db.init_app(app)

# Import and register blueprints
from src.routes.user import user_bp
from src.routes.admin_fixed import admin_bp
from src.routes.sales_working import sales_bp
from src.routes.charts_redesigned import charts_bp
from src.routes.flight_load import flight_load_bp
from src.routes.route_analysis import route_analysis_bp
from src.routes.manifest import manifest_bp

app.register_blueprint(user_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(sales_bp)
app.register_blueprint(charts_bp)
app.register_blueprint(flight_load_bp, url_prefix='/flight-load')
app.register_blueprint(route_analysis_bp, url_prefix='/flight-load')
app.register_blueprint(manifest_bp, url_prefix='/flight-load')

# Create database tables
with app.app_context():
    db.create_all()
    print("Database tables created successfully!")
    
    # Create default airports if none exist
    if AirportMaster.query.count() == 0:
        default_airports = [
            {'code': 'ADD', 'name': 'Addis Ababa', 'country': 'Ethiopia'},
            {'code': 'KWI', 'name': 'Kuwait City', 'country': 'Kuwait'},
            {'code': 'DXB', 'name': 'Dubai', 'country': 'UAE'},
            {'code': 'JED', 'name': 'Jeddah', 'country': 'Saudi Arabia'},
            {'code': 'CAI', 'name': 'Cairo', 'country': 'Egypt'},
            {'code': 'NBO', 'name': 'Nairobi', 'country': 'Kenya'},
            {'code': 'LHR', 'name': 'London Heathrow', 'country': 'UK'},
            {'code': 'FRA', 'name': 'Frankfurt', 'country': 'Germany'},
            {'code': 'CDG', 'name': 'Paris Charles de Gaulle', 'country': 'France'},
            {'code': 'IAD', 'name': 'Washington Dulles', 'country': 'USA'},
        ]
        
        for airport_data in default_airports:
            airport = AirportMaster(**airport_data, active=True)
            db.session.add(airport)
        
        db.session.commit()
        print(f"Created {len(default_airports)} default airports")

# Home route
@app.route('/')
def home():
    return send_from_directory('static', 'index.html')

# Serve static files
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# Flight Load menu route
@app.route('/flight-load')
def flight_load_redirect():
    return send_from_directory('static', 'flight-load-menu.html')

# Forecast interface route
@app.route('/flight-load/forecast')
def forecast_interface():
    return send_from_directory('static', 'forecast-interface.html')

# Manifest dashboard route
@app.route('/flight-load/manifest-dashboard')
def manifest_dashboard_page():
    return send_from_directory('static', 'manifest-dashboard.html')

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

