import uuid
from datetime import datetime, timedelta

# Add this function to create a persistent session
def get_current_session_id():
    """Generate or retrieve a persistent session ID"""
    return 'ethiopian_airlines_session'

# Update the upload function to use persistent session
@route_analysis_bp.route('/upload', methods=['POST'])
def upload_route_analysis():
    """Handle route analysis Excel file upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type. Please upload .xlsx or .xls file'}), 400
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        upload_folder = current_app.config.get('UPLOAD_FOLDER', '/tmp')
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # Parse the Excel file
        parsed_data = parse_route_analysis_excel(file_path)
        
        if not parsed_data['success']:
            os.remove(file_path)
            return jsonify({'success': False, 'error': parsed_data['error']}), 400
        
        # Get session ID for persistence
        session_id = get_current_session_id()
        
        # Clear existing data for this session only
        RouteAnalysis.query.filter_by(session_id=session_id).delete()
        
        # Store in database with session ID
        for route in parsed_data['routes']:
            route_record = RouteAnalysis(
                route_code=route['code'],
                city=route['city'],
                country=route['country'],
                total_passengers=route['total_passengers'],
                previous_week=route['previous_week'],
                variance=route['variance'],
                variance_pct=route['variance_pct'],
                daily_data=route['daily_passengers'],
                week_identifier=parsed_data['sheet_name'],
                session_id=session_id
            )
            db.session.add(route_record)
        
        db.session.commit()
        
        # Clean up temp file
        os.remove(file_path)
        
        return jsonify({
            'success': True,
            'message': f'Successfully uploaded {parsed_data["total_routes"]} routes',
            'summary': {
                'total_routes': parsed_data['total_routes'],
                'total_passengers': parsed_data['total_passengers'],
                'previous_week': parsed_data['previous_week'],
                'variance': parsed_data['variance'],
                'variance_pct': parsed_data['variance_pct'],
                'top_route': parsed_data['top_route'],
                'busiest_day': parsed_data['busiest_day'],
                'week': parsed_data['sheet_name']
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Update the data endpoint to use persistent session
@route_analysis_bp.route('/data', methods=['GET'])
def get_route_analysis_data():
    """Get current route analysis data"""
    try:
        session_id = get_current_session_id()
        routes = RouteAnalysis.query.filter_by(session_id=session_id).all()
        
        if not routes:
            return jsonify({
                'success': False,
                'message': 'No data available. Please upload an Excel file first.'
            })
        
        # Calculate summary metrics
        total_passengers = sum(r.total_passengers for r in routes)
        total_previous = sum(r.previous_week for r in routes)
        variance = total_passengers - total_previous
        variance_pct = (variance / total_previous * 100) if total_previous > 0 else 0
        
        # Find top route
        top_route = max(routes, key=lambda x: x.total_passengers) if routes else None
        
        # Calculate busiest day
        all_daily_totals = {}
        for route in routes:
            if route.daily_data:
                for date, pax in route.daily_data.items():
                    all_daily_totals[date] = all_daily_totals.get(date, 0) + pax
        
        busiest_day = max(all_daily_totals, key=all_daily_totals.get) if all_daily_totals else None
        busiest_day_pax = all_daily_totals[busiest_day] if busiest_day else 0
        
        return jsonify({
            'success': True,
            'summary': {
                'total_routes': len(routes),
                'total_passengers': total_passengers,
                'previous_week': total_previous,
                'variance': variance,
                'variance_pct': round(variance_pct, 2),
                'top_route': {
                    'code': top_route.route_code,
                    'display_name': get_airport_display_name(top_route.route_code),
                    'passengers': top_route.total_passengers
                } if top_route else None,
                'busiest_day': {
                    'date': busiest_day,
                    'passengers': busiest_day_pax
                } if busiest_day else None,
                'week': routes[0].week_identifier if routes else 'Unknown'
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Update all chart endpoints to use persistent session
@route_analysis_bp.route('/charts/top-destinations', methods=['GET'])
def get_top_destinations():
    """Get top destinations chart data"""
    try:
        limit = request.args.get('limit', 10, type=int)
        session_id = get_current_session_id()
        
        routes = RouteAnalysis.query.filter_by(session_id=session_id).order_by(RouteAnalysis.total_passengers.desc()).limit(limit).all()
        
        labels = [get_airport_display_name(r.route_code) for r in routes]
        data = [r.total_passengers for r in routes]
        
        return jsonify({
            'success': True,
            'labels': labels,
            'datasets': [{
                'label': 'Passengers',
                'data': data,
                'backgroundColor': 'rgba(0, 128, 0, 0.7)',
                'borderColor': 'rgba(0, 128, 0, 1)',
                'borderWidth': 2
            }]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Add this new endpoint to clear data when needed
@route_analysis_bp.route('/clear', methods=['POST'])
def clear_route_analysis_data():
    """Clear all route analysis data"""
    try:
        session_id = get_current_session_id()
        RouteAnalysis.query.filter_by(session_id=session_id).delete()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Route analysis data cleared successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
