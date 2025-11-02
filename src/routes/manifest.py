from flask import Blueprint, request, jsonify
import re
from datetime import datetime
from collections import Counter
from src.models.sales import db
from src.utils.airport_lookup import get_airport_info

# Import the model (will be added to main models folder)
# from src.models.manifest import DailyManifest

manifest_bp = Blueprint('manifest', __name__)

def parse_manifest_text(manifest_text):
    """
    Parse flight manifest text and extract key data
    Returns: dict with flight info, passenger counts, and route breakdown
    """
    result = {
        'flight_number': None,
        'flight_date': None,
        'origin': None,
        'destination': None,
        'total_passengers': 0,
        'c_class_passengers': 0,
        'y_class_passengers': 0,
        'male_count': 0,
        'female_count': 0,
        'child_count': 0,
        'infant_count': 0,
        'total_bags': 0,
        'total_weight': 0,
        'route_breakdown': {}
    }
    
    # Extract flight number
    flight_match = re.search(r'FLIGHT:\s+ET\s+(\d+)', manifest_text)
    if flight_match:
        result['flight_number'] = f"ET {flight_match.group(1)}"
    
    # Extract date
    date_match = re.search(r'DATE:\s+(\d+)(\w+)(\d+)', manifest_text)
    if date_match:
        day = date_match.group(1)
        month = date_match.group(2).upper()
        year = date_match.group(3)
        
        # Convert month abbreviation to number
        month_map = {
            'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
            'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
            'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
        }
        month_num = month_map.get(month[:3], '01')
        
        # Handle 2-digit year
        if len(year) == 2:
            year = f"20{year}"
        
        try:
            result['flight_date'] = datetime.strptime(f"{year}-{month_num}-{day.zfill(2)}", "%Y-%m-%d").date()
        except:
            pass
    
    # Extract route (origin and destination)
    route_match = re.search(r'PT\.OF EMBARKATION:\s+(\w+)\s+PT\.OF DEST:\s+(\w+)', manifest_text)
    if route_match:
        result['origin'] = route_match.group(1)
        result['destination'] = route_match.group(2)
    
    # Extract passenger origins/destinations (TR.ORG field)
    # Pattern: /ET\d+/([A-Z]{3})/
    routes = re.findall(r'/ET\d+/([A-Z]{3})/', manifest_text)
    route_counts = Counter(routes)
    result['route_breakdown'] = dict(route_counts)
    result['total_passengers'] = len(routes)
    
    # Extract class breakdown
    # C class passengers
    c_class_section = manifest_text.split('C CLASS')[1].split('Y CLASS')[0] if 'C CLASS' in manifest_text and 'Y CLASS' in manifest_text else ''
    c_passengers = len(re.findall(r'^\d{3}\s', c_class_section, re.MULTILINE))
    result['c_class_passengers'] = c_passengers
    
    # Y class passengers
    y_class_section = manifest_text.split('Y CLASS')[1] if 'Y CLASS' in manifest_text else ''
    y_passengers = len(re.findall(r'^\d{3}\s', y_class_section, re.MULTILINE))
    result['y_class_passengers'] = y_passengers
    
    # Extract totals (demographics and baggage)
    totals_match = re.search(
        r'TOTALS:.*?MALE\s+FEMALE\s+CHILD\s+INFANT\s+BAGS\s+WEIGHT\s+\.?\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)',
        manifest_text,
        re.DOTALL
    )
    if totals_match:
        result['male_count'] = int(totals_match.group(1))
        result['female_count'] = int(totals_match.group(2))
        result['child_count'] = int(totals_match.group(3))
        result['infant_count'] = int(totals_match.group(4))
        result['total_bags'] = int(totals_match.group(5))
        result['total_weight'] = int(totals_match.group(6))
    
    return result

@manifest_bp.route('/upload', methods=['POST'])
def upload_manifest():
    """
    Upload and parse manifest file
    Expects: manifest_text (inbound or outbound), direction (INBOUND/OUTBOUND)
    """
    try:
        data = request.get_json()
        
        if not data or 'manifest_text' not in data:
            return jsonify({'success': False, 'error': 'No manifest text provided'}), 400
        
        manifest_text = data['manifest_text']
        direction = data.get('direction', 'INBOUND').upper()
        
        if direction not in ['INBOUND', 'OUTBOUND']:
            return jsonify({'success': False, 'error': 'Direction must be INBOUND or OUTBOUND'}), 400
        
        # Parse manifest
        parsed_data = parse_manifest_text(manifest_text)
        
        if not parsed_data['flight_number'] or not parsed_data['flight_date']:
            return jsonify({'success': False, 'error': 'Could not extract flight number or date from manifest'}), 400
        
        # Import here to avoid circular imports
        from src.models.manifest import DailyManifest
        from src.models.flight_load import FlightLoadRecord
        from src.models.route_analysis import ManualForecast
        
        flight_no = parsed_data['flight_number'].split(' ')[1] # Assuming "ET 620" -> "620"
        travel_date = parsed_data['flight_date']
        
        # 1. Update/Create DailyManifest record
        existing_manifest = DailyManifest.query.filter_by(
            flight_number=parsed_data['flight_number'],
            flight_date=travel_date,
            direction=direction
        ).first()
        
        if existing_manifest:
            manifest = existing_manifest
        else:
            manifest = DailyManifest()
        
        # Set all fields
        manifest.flight_number = parsed_data['flight_number']
        manifest.flight_date = travel_date
        manifest.direction = direction
        manifest.origin = parsed_data['origin']
        manifest.destination = parsed_data['destination']
        manifest.total_passengers = parsed_data['total_passengers']
        manifest.c_class_passengers = parsed_data['c_class_passengers']
        manifest.y_class_passengers = parsed_data['y_class_passengers']
        manifest.male_count = parsed_data['male_count']
        manifest.female_count = parsed_data['female_count']
        manifest.child_count = parsed_data['child_count']
        manifest.infant_count = parsed_data['infant_count']
        manifest.total_bags = parsed_data['total_bags']
        manifest.total_weight = parsed_data['total_weight']
        manifest.set_route_breakdown(parsed_data['route_breakdown'])
        manifest.upload_date = datetime.utcnow()
        
        if not existing_manifest:
            db.session.add(manifest)
            
        # 2. Update/Create FlightLoadRecord with manifest data (Actual Load)
        # ... (existing logic for FlightLoadRecord) ...
        
        # 3. Update/Create ManualForecast records for each route in the breakdown
        route_breakdown = manifest.get_route_breakdown()
        
        for airport_code, pax_count in route_breakdown.items():
            # Determine direction based on the manifest's direction
            # For simplicity, we'll assume the manifest direction is the direction of the passenger flow
            # e.g., INBOUND manifest means passengers are inbound to the destination (KWI in the example)
            # and the breakdown is for the origin airports (ADD, LOS, etc.)
            # The user's request is about inbound flight from 01dec to 06dec, so I'll assume
            # the breakdown is for the origin airports of the inbound flight.
            
            # Since the manifest is for a specific flight (e.g., ET 620 ADD-KWI), 
            # the route analysis page is likely concerned with the flow to/from the hub.
            # I will use the manifest's direction for the ManualForecast record.
            
            existing_forecast = ManualForecast.query.filter_by(
                travel_date=travel_date,
                airport_code=airport_code,
                direction=direction
            ).first()
            
            if existing_forecast:
                # Only update if the existing record is a manual forecast
                if existing_forecast.data_source == 'manual':
                    existing_forecast.forecast_pax = pax_count
                    existing_forecast.data_source = 'manifest'
                    existing_forecast.last_updated = datetime.utcnow()
            else:
                # Create a new record from the manifest
                new_forecast = ManualForecast(
                    travel_date=travel_date,
                    airport_code=airport_code,
                    direction=direction,
                    forecast_pax=pax_count,
                    data_source='manifest'
                )
                db.session.add(new_forecast)
        
        # 2. Update/Create FlightLoadRecord with manifest data (Actual Load)
        existing_load_record = FlightLoadRecord.query.filter_by(
            travel_date=travel_date,
            flight_no=flight_no
        ).first()
        
        # Assuming capacity data is not in the manifest, we only update passenger counts
        # If a forecast exists, we use its capacity data. Otherwise, capacity is 0.
        capacity_data = {
            'c_cap': existing_load_record.c_cap if existing_load_record else 0,
            'y_cap': existing_load_record.y_cap if existing_load_record else 0,
            'tot_cap': existing_load_record.tot_cap if existing_load_record else 0,
        }
        
        # Calculate Load Factors based on manifest data
        pax_c = manifest.c_class_passengers
        pax_y = manifest.y_class_passengers
        pax = manifest.total_passengers
        
        c_cap = capacity_data['c_cap']
        y_cap = capacity_data['y_cap']
        tot_cap = capacity_data['tot_cap']
        
        lf_c = (pax_c / c_cap) * 100 if c_cap > 0 else 0.0
        lf_y = (pax_y / y_cap) * 100 if y_cap > 0 else 0.0
        lf = (pax / tot_cap) * 100 if tot_cap > 0 else 0.0
        
        load_data = {
            'pax_c': pax_c,
            'pax_y': pax_y,
            'pax': pax,
            'lf_c': lf_c,
            'lf_y': lf_y,
            'lf': lf,
            # Preserve capacity data
            'c_cap': c_cap,
            'y_cap': y_cap,
            'tot_cap': tot_cap,
        }
        
        if existing_load_record:
            existing_load_record.update_from_dict(load_data)
            existing_load_record.data_source = 'manifest'
        else:
            new_load_record = FlightLoadRecord(
                travel_date=travel_date,
                flight_no=flight_no,
                data_source='manifest'
            )
            new_load_record.update_from_dict(load_data)
            db.session.add(new_load_record)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f"Successfully processed {direction} manifest for {parsed_data['flight_number']} on {parsed_data['flight_date']}",
            'data': manifest.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@manifest_bp.route('/data', methods=['GET'])
def get_manifest_data():
    """
    Get manifest data with optional filtering
    Query params: start_date, end_date, direction, flight_number
    """
    try:
        from src.models.manifest import DailyManifest
        
        query = DailyManifest.query
        
        # Apply filters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        direction = request.args.get('direction')
        flight_number = request.args.get('flight_number')
        
        if start_date:
            query = query.filter(DailyManifest.flight_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(DailyManifest.flight_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        if direction:
            query = query.filter(DailyManifest.direction == direction.upper())
        if flight_number:
            query = query.filter(DailyManifest.flight_number == flight_number)
        
        # Order by date descending
        manifests = query.order_by(DailyManifest.flight_date.desc()).all()
        
        return jsonify({
            'success': True,
            'count': len(manifests),
            'data': [m.to_dict() for m in manifests]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@manifest_bp.route('/charts/top-routes', methods=['GET'])
def get_top_routes_chart():
    """
    Get top routes chart data
    Query params: direction (INBOUND/OUTBOUND), days (default 30)
    """
    try:
        from src.models.manifest import DailyManifest
        from datetime import timedelta
        
        direction = request.args.get('direction', 'INBOUND').upper()
        days = int(request.args.get('days', 30))
        
        # Get manifests from last N days
        start_date = datetime.utcnow().date() - timedelta(days=days)
        manifests = DailyManifest.query.filter(
            DailyManifest.direction == direction,
            DailyManifest.flight_date >= start_date
        ).all()
        
        # Aggregate route breakdown
        route_totals = Counter()
        for manifest in manifests:
            breakdown = manifest.get_route_breakdown()
            route_totals.update(breakdown)
        
        # Get top 10 routes with airport info
        top_routes = []
        for route_code, count in route_totals.most_common(10):
            airport_info = get_airport_info(route_code)
            top_routes.append({
                'code': route_code,
                'name': airport_info['name'] if airport_info else route_code,
                'city': airport_info['city'] if airport_info else '',
                'country': airport_info['country'] if airport_info else '',
                'passengers': count
            })
        
        return jsonify({
            'success': True,
            'direction': direction,
            'period_days': days,
            'routes': top_routes
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@manifest_bp.route('/charts/daily-trend', methods=['GET'])
def get_daily_trend_chart():
    """
    Get daily passenger trend chart data
    Query params: direction, days (default 30)
    """
    try:
        from src.models.manifest import DailyManifest
        from datetime import timedelta
        
        direction = request.args.get('direction')
        days = int(request.args.get('days', 30))
        
        start_date = datetime.utcnow().date() - timedelta(days=days)
        query = DailyManifest.query.filter(DailyManifest.flight_date >= start_date)
        
        if direction:
            query = query.filter(DailyManifest.direction == direction.upper())
        
        manifests = query.order_by(DailyManifest.flight_date).all()
        
        # Group by date
        daily_data = {}
        for manifest in manifests:
            date_str = manifest.flight_date.isoformat()
            if date_str not in daily_data:
                daily_data[date_str] = {
                    'date': date_str,
                    'inbound': 0,
                    'outbound': 0,
                    'total': 0
                }
            
            if manifest.direction == 'INBOUND':
                daily_data[date_str]['inbound'] += manifest.total_passengers
            else:
                daily_data[date_str]['outbound'] += manifest.total_passengers
            
            daily_data[date_str]['total'] += manifest.total_passengers
        
        # Convert to list and sort by date
        trend_data = sorted(daily_data.values(), key=lambda x: x['date'])
        
        return jsonify({
            'success': True,
            'period_days': days,
            'data': trend_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
