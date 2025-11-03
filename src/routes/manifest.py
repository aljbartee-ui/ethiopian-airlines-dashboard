from flask import Blueprint, render_template, request, jsonify, session
from src.models.user import db
from src.models.manifest import DailyManifest, RouteForecast, AirportMaster
from datetime import datetime, timedelta
import openpyxl
from io import BytesIO
from collections import defaultdict

manifest_bp = Blueprint('manifest', __name__)

def admin_required(f):
    """Decorator to require admin authentication"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({'success': False, 'error': 'Admin authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@manifest_bp.route('/manifest-dashboard')
def manifest_dashboard():
    """Manifest upload and analytics dashboard"""
    return render_template('manifest-dashboard.html')

@manifest_bp.route('/forecast-interface')
def forecast_interface():
    """Manual forecast data entry interface"""
    return render_template('forecast-interface.html')

@manifest_bp.route('/api/manifest/upload', methods=['POST'])
@admin_required
def upload_manifest():
    """
    Upload daily manifest (actual passenger data)
    This OVERRIDES Excel forecast for the specific date
    """
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    try:
        # Read manifest file
        file_content = file.read()
        workbook = openpyxl.load_workbook(BytesIO(file_content), data_only=True)
        sheet = workbook.active
        
        # Parse manifest data
        # Assuming format: Date | Flight | Direction | Total Pax | Business | Economy | Route Breakdown
        records_processed = 0
        
        for row_idx in range(2, sheet.max_row + 1):
            date_val = sheet.cell(row_idx, 1).value
            flight_no = str(sheet.cell(row_idx, 2).value) if sheet.cell(row_idx, 2).value else None
            direction = str(sheet.cell(row_idx, 3).value).lower() if sheet.cell(row_idx, 3).value else None
            total_pax = int(sheet.cell(row_idx, 4).value) if sheet.cell(row_idx, 4).value else 0
            business_pax = int(sheet.cell(row_idx, 5).value) if sheet.cell(row_idx, 5).value else 0
            economy_pax = int(sheet.cell(row_idx, 6).value) if sheet.cell(row_idx, 6).value else 0
            
            if not date_val or not flight_no:
                continue
            
            # Convert date
            if isinstance(date_val, datetime):
                flight_date = date_val.date()
            else:
                flight_date = datetime.strptime(str(date_val), '%Y-%m-%d').date()
            
            # Get capacity (standard aircraft config)
            # TODO: Make this configurable
            total_cap = 180  # Example capacity
            business_cap = 30
            economy_cap = 150
            
            # Calculate load factors
            lf = (total_pax / total_cap * 100) if total_cap > 0 else 0
            lf_c = (business_pax / business_cap * 100) if business_cap > 0 else 0
            lf_y = (economy_pax / economy_cap * 100) if economy_cap > 0 else 0
            
            # Parse route breakdown (if exists in column 7+)
            route_breakdown = {}
            # Example: Column 7 might have JSON or comma-separated "ADD:45,DXB:23"
            
            # Check if manifest already exists for this flight/date
            existing = DailyManifest.query.filter_by(
                flight_date=flight_date,
                flight_number=flight_no
            ).first()
            
            if existing:
                # Update existing manifest
                existing.total_passengers = total_pax
                existing.business_passengers = business_pax
                existing.economy_passengers = economy_pax
                existing.total_capacity = total_cap
                existing.business_capacity = business_cap
                existing.economy_capacity = economy_cap
                existing.load_factor = lf
                existing.business_load_factor = lf_c
                existing.economy_load_factor = lf_y
                existing.route_breakdown = route_breakdown
                existing.uploaded_at = datetime.utcnow()
                existing.uploaded_by = session.get('admin_username')
                existing.source = 'manifest'
            else:
                # Create new manifest record
                new_manifest = DailyManifest(
                    flight_date=flight_date,
                    flight_number=flight_no,
                    direction=direction or ('inbound' if flight_no == '620' else 'outbound'),
                    total_passengers=total_pax,
                    business_passengers=business_pax,
                    economy_passengers=economy_pax,
                    total_capacity=total_cap,
                    business_capacity=business_cap,
                    economy_capacity=economy_cap,
                    load_factor=lf,
                    business_load_factor=lf_c,
                    economy_load_factor=lf_y,
                    route_breakdown=route_breakdown,
                    uploaded_by=session.get('admin_username'),
                    source='manifest'
                )
                db.session.add(new_manifest)
            
            records_processed += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully processed {records_processed} manifest records',
            'records_processed': records_processed
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@manifest_bp.route('/api/manifest/data')
def get_manifest_data():
    """Get manifest data for date range"""
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    query = DailyManifest.query
    
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        query = query.filter(DailyManifest.flight_date >= start_date)
    
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        query = query.filter(DailyManifest.flight_date <= end_date)
    
    records = query.order_by(DailyManifest.flight_date).all()
    
    return jsonify({
        'success': True,
        'data': [r.to_dict() for r in records],
        'total_passengers': sum(r.total_passengers for r in records),
        'average_load_factor': sum(r.load_factor for r in records) / len(records) if records else 0,
        'record_count': len(records)
    })

@manifest_bp.route('/api/forecast/save', methods=['POST'])
@admin_required
def save_forecast():
    """
    Save manual forecast data
    This is SEPARATE from manifest data
    """
    data = request.get_json()
    forecasts = data.get('forecasts', [])
    
    try:
        saved_count = 0
        
        for forecast in forecasts:
            forecast_date = datetime.strptime(forecast['date'], '%Y-%m-%d').date()
            airport_code = forecast['airport_code']
            direction = forecast['direction']
            passengers = int(forecast['passengers'])
            
            # Check if forecast exists
            existing = RouteForecast.query.filter_by(
                forecast_date=forecast_date,
                airport_code=airport_code,
                direction=direction
            ).first()
            
            if existing:
                existing.passengers = passengers
                existing.updated_at = datetime.utcnow()
                existing.created_by = session.get('admin_username')
            else:
                new_forecast = RouteForecast(
                    forecast_date=forecast_date,
                    airport_code=airport_code,
                    direction=direction,
                    passengers=passengers,
                    created_by=session.get('admin_username')
                )
                db.session.add(new_forecast)
            
            saved_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully saved {saved_count} forecasts'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@manifest_bp.route('/api/forecast/data')
def get_forecast_data():
    """
    Get combined forecast and manifest data
    Manifest data (actuals) takes precedence over forecasts
    """
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    direction = request.args.get('direction', 'inbound')
    
    if not start_date_str or not end_date_str:
        return jsonify({'success': False, 'error': 'Date range required'}), 400
    
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    
    # Get all dates in range
    date_list = []
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date)
        current_date += timedelta(days=1)
    
    # Get forecasts for date range
    forecasts = RouteForecast.query.filter(
        RouteForecast.forecast_date >= start_date,
        RouteForecast.forecast_date <= end_date,
        RouteForecast.direction == direction
    ).all()
    
    # Get manifests for date range (actuals)
    manifests = DailyManifest.query.filter(
        DailyManifest.flight_date >= start_date,
        DailyManifest.flight_date <= end_date,
        DailyManifest.direction == direction
    ).all()
    
    # Build combined data structure
    # Group by airport and date
    data_by_airport = defaultdict(lambda: defaultdict(lambda: {'passengers': 0, 'source': 'forecast', 'confirmed': False}))
    
    # First, add forecast data
    for forecast in forecasts:
        date_str = forecast.forecast_date.strftime('%Y-%m-%d')
        data_by_airport[forecast.airport_code][date_str] = {
            'passengers': forecast.passengers,
            'source': 'forecast',
            'confirmed': False
        }
    
    # Then, override with manifest data (actuals) where available
    manifest_dates = set()
    for manifest in manifests:
        date_str = manifest.flight_date.strftime('%Y-%m-%d')
        manifest_dates.add(date_str)
        
        # Parse route breakdown
        if manifest.route_breakdown:
            for airport, pax_count in manifest.route_breakdown.items():
                data_by_airport[airport][date_str] = {
                    'passengers': pax_count,
                    'source': 'manifest',
                    'confirmed': True
                }
    
    # Get all airports
    airports = AirportMaster.query.filter_by(active=True).all()
    airport_codes = [a.code for a in airports]
    
    # Add any airports from data that aren't in master list
    for airport in data_by_airport.keys():
        if airport not in airport_codes:
            airport_codes.append(airport)
    
    # Build response
    result = {
        'dates': [d.strftime('%Y-%m-%d') for d in date_list],
        'airports': sorted(airport_codes),
        'data': dict(data_by_airport),
        'manifest_dates': list(manifest_dates)
    }
    
    return jsonify({
        'success': True,
        'result': result
    })

@manifest_bp.route('/api/airports/list')
def list_airports():
    """Get list of airports for dropdown"""
    airports = AirportMaster.query.filter_by(active=True).order_by(AirportMaster.code).all()
    return jsonify({
        'success': True,
        'airports': [a.to_dict() for a in airports]
    })

@manifest_bp.route('/api/airports/add', methods=['POST'])
@admin_required
def add_airport():
    """Add new airport to master list"""
    data = request.get_json()
    code = data.get('code', '').upper().strip()
    name = data.get('name', '').strip()
    country = data.get('country', '').strip()
    
    if not code:
        return jsonify({'success': False, 'error': 'Airport code required'}), 400
    
    # Check if exists
    existing = AirportMaster.query.filter_by(code=code).first()
    if existing:
        return jsonify({'success': False, 'error': 'Airport code already exists'}), 400
    
    try:
        new_airport = AirportMaster(
            code=code,
            name=name,
            country=country,
            active=True
        )
        db.session.add(new_airport)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'airport': new_airport.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

