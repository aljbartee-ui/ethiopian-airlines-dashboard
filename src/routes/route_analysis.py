"""
Route Analysis Routes
Handles route analysis dashboard with proper multi-week support
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from src.models.route_analysis import RouteAnalysis
from src.models.user import db
from src.utils.airport_lookup import get_airport_info, get_airport_display_name
import openpyxl
from datetime import datetime, timedelta
import os
import re

route_analysis_bp = Blueprint('route_analysis', __name__)

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_current_session_id():
    """Generate or retrieve a persistent session ID"""
    return 'ethiopian_airlines_session'

def extract_week_dates_from_sheet_name(sheet_name):
    """Extract start and end dates from sheet name"""
    # Common patterns for week dates
    patterns = [
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}).*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # MM/DD/YYYY - MM/DD/YYYY
        r'(\d{1,2}[/-]\d{1,2}).*?(\d{1,2}[/-]\d{1,2})',  # MM/DD - MM/DD
        r'(\w+\s+\d{1,2}).*?(\w+\s+\d{1,2})',  # Month DD - Month DD
    ]
    
    for pattern in patterns:
        match = re.search(pattern, sheet_name, re.IGNORECASE)
        if match:
            return match.group(1), match.group(2)
    
    # If no pattern matches, return the sheet name as both dates
    return sheet_name, sheet_name

def parse_route_analysis_excel(file_path):
    """
    Parse route analysis Excel file with improved data handling
    
    Expected format:
    - Row 1: Empty
    - Row 2: Headers (POINTS, dates..., GRAND TOTAL, PREVIOUS WEEK, VARIANCE)
    - Row 3+: Airport codes with passenger counts
    
    Returns:
        dict: Parsed data with routes, dates, and metrics
    """
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        sheet = wb.active
        
        # Get sheet name (week identifier)
        sheet_name = sheet.title
        week_start, week_end = extract_week_dates_from_sheet_name(sheet_name)
        
        # Row 2 contains headers
        headers = []
        date_columns = []
        
        for col_idx in range(1, sheet.max_column + 1):
            header = sheet.cell(2, col_idx).value
            if header:
                header_str = str(header).strip()
                headers.append(header_str)
                
                # Check if it's a date column (not POINTS, GRAND TOTAL, etc.)
                if header_str not in ['POINTS', 'GRAND TOTAL', 'PREVIOUS WEEK', 'VARIANCE', 'VARIANCE %']:
                    # Try to parse as date
                    try:
                        if isinstance(header, datetime):
                            date_columns.append((col_idx, header.strftime('%Y-%m-%d')))
                        else:
                            date_columns.append((col_idx, header_str))
                    except:
                        date_columns.append((col_idx, header_str))
            else:
                headers.append('')
        
        # Find special columns
        grand_total_col = None
        previous_week_col = None
        variance_col = None
        
        for idx, header in enumerate(headers, 1):
            header_upper = str(header).upper()
            if 'GRAND TOTAL' in header_upper:
                grand_total_col = idx
            elif 'PREVIOUS WEEK' in header_upper or 'PREVIOUS' in header_upper:
                previous_week_col = idx
            elif 'VARIANCE' in header_upper and '%' not in header_upper:
                variance_col = idx
        
        # Parse routes starting from row 3
        routes = []
        total_passengers = 0
        total_previous = 0
        
        for row_idx in range(3, sheet.max_row + 1):
            route_code = sheet.cell(row_idx, 1).value
            
            if not route_code or str(route_code).strip() == '':
                continue
                
            route_code = str(route_code).strip().upper()
            
            # Skip TOTAL row and any summary rows
            if route_code in ['TOTAL', 'GRAND TOTAL', 'TOTALS', 'SUMMARY']:
                continue
            
            # Get airport information - use code directly if not found
            airport_info = get_airport_info(route_code)
            if airport_info['city'] == 'Unknown':
                # Use the code as display name if airport not found
                display_name = route_code
            else:
                display_name = get_airport_display_name(route_code)
            
            # Get passenger counts per date
            daily_passengers = {}
            for col_idx, date_str in date_columns:
                pax = sheet.cell(row_idx, col_idx).value
                try:
                    pax_count = int(pax) if pax is not None else 0
                except (ValueError, TypeError):
                    pax_count = 0
                daily_passengers[date_str] = pax_count
            
            # Get totals
            grand_total = 0
            if grand_total_col:
                val = sheet.cell(row_idx, grand_total_col).value
                try:
                    grand_total = int(val) if val is not None else 0
                except (ValueError, TypeError):
                    grand_total = sum(daily_passengers.values())
            else:
                grand_total = sum(daily_passengers.values())
            
            previous_week = 0
            if previous_week_col:
                val = sheet.cell(row_idx, previous_week_col).value
                try:
                    previous_week = int(val) if val is not None else 0
                except (ValueError, TypeError):
                    previous_week = 0
            
            variance = 0
            if variance_col:
                val = sheet.cell(row_idx, variance_col).value
                try:
                    variance = int(val) if val is not None else 0
                except (ValueError, TypeError):
                    variance = grand_total - previous_week
            else:
                variance = grand_total - previous_week
            
            # Calculate variance percentage
            variance_pct = 0
            if previous_week > 0:
                variance_pct = (variance / previous_week) * 100
            
            routes.append({
                'code': route_code,
                'city': airport_info['city'],
                'country': airport_info['country'],
                'display_name': display_name,
                'daily_passengers': daily_passengers,
                'total_passengers': grand_total,
                'previous_week': previous_week,
                'variance': variance,
                'variance_pct': round(variance_pct, 2)
            })
            
            total_passengers += grand_total
            total_previous += previous_week
        
        # Calculate overall metrics
        overall_variance = total_passengers - total_previous
        overall_variance_pct = 0
        if total_previous > 0:
            overall_variance_pct = (overall_variance / total_previous) * 100
        
        # Find top route
        top_route = max(routes, key=lambda x: x['total_passengers']) if routes else None
        
        # Find busiest day
        all_daily_totals = {}
        for route in routes:
            for date, pax in route['daily_passengers'].items():
                all_daily_totals[date] = all_daily_totals.get(date, 0) + pax
        
        busiest_day = None
        busiest_day_pax = 0
        if all_daily_totals:
            busiest_day = max(all_daily_totals, key=all_daily_totals.get)
            busiest_day_pax = all_daily_totals[busiest_day]
        
        return {
            'success': True,
            'sheet_name': sheet_name,
            'week_start': week_start,
            'week_end': week_end,
            'total_routes': len(routes),
            'total_passengers': total_passengers,
            'previous_week': total_previous,
            'variance': overall_variance,
            'variance_pct': round(overall_variance_pct, 2),
            'top_route': {
                'code': top_route['code'],
                'display_name': top_route['display_name'],
                'passengers': top_route['total_passengers']
            } if top_route else None,
            'busiest_day': {
                'date': busiest_day,
                'passengers': busiest_day_pax
            } if busiest_day else None,
            'routes': routes,
            'dates': [date for _, date in date_columns],
            'daily_totals': all_daily_totals
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error parsing Excel file: {str(e)}'
        }

@route_analysis_bp.route('/upload', methods=['POST'])
def upload_route_analysis():
    """Handle route analysis Excel file upload with proper multi-week support"""
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
        
        # Check if this week already exists
        existing_week = RouteAnalysis.query.filter_by(
            session_id=session_id, 
            week_identifier=parsed_data['sheet_name']
        ).first()
        
        if existing_week:
            # Delete existing data for this week
            RouteAnalysis.query.filter_by(
                session_id=session_id, 
                week_identifier=parsed_data['sheet_name']
            ).delete()
        
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
                week_start_date=parsed_data['week_start'],
                week_end_date=parsed_data['week_end'],
                session_id=session_id
            )
            db.session.add(route_record)
        
        db.session.commit()
        
        # Clean up temp file
        os.remove(file_path)
        
        return jsonify({
            'success': True,
            'message': f'Successfully uploaded {parsed_data["total_routes"]} routes for week {parsed_data["sheet_name"]}',
            'summary': {
                'total_routes': parsed_data['total_routes'],
                'total_passengers': parsed_data['total_passengers'],
                'previous_week': parsed_data['previous_week'],
                'variance': parsed_data['variance'],
                'variance_pct': parsed_data['variance_pct'],
                'top_route': parsed_data['top_route'],
                'busiest_day': parsed_data['busiest_day'],
                'week': parsed_data['sheet_name'],
                'week_start': parsed_data['week_start'],
                'week_end': parsed_data['week_end']
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@route_analysis_bp.route('/weeks', methods=['GET'])
def get_available_weeks():
    """Get list of available weeks for filtering"""
    try:
        session_id = get_current_session_id()
        weeks = RouteAnalysis.query.with_entities(
            RouteAnalysis.week_identifier,
            RouteAnalysis.week_start_date,
            RouteAnalysis.week_end_date
        ).filter_by(session_id=session_id).distinct().all()
        
        week_list = []
        for week in weeks:
            week_list.append({
                'identifier': week.week_identifier,
                'start_date': week.week_start_date,
                'end_date': week.week_end_date,
                'display_name': f"{week.week_identifier} ({week.week_start_date} - {week.week_end_date})"
            })
        
        # Sort weeks by start date (most recent first)
        week_list.sort(key=lambda x: x['start_date'], reverse=True)
        
        return jsonify({
            'success': True,
            'weeks': week_list
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@route_analysis_bp.route('/data', methods=['GET'])
def get_route_analysis_data():
    """Get route analysis data with week filtering"""
    try:
        session_id = get_current_session_id()
        week_filter = request.args.get('week', 'all')
        
        # Build query based on week filter
        if week_filter and week_filter != 'all':
            routes = RouteAnalysis.query.filter_by(
                session_id=session_id, 
                week_identifier=week_filter
            ).all()
            current_week = week_filter
        else:
            routes = RouteAnalysis.query.filter_by(session_id=session_id).all()
            # Get the most recent week for display
            recent_week = RouteAnalysis.query.filter_by(session_id=session_id).order_by(
                RouteAnalysis.week_start_date.desc()
            ).first()
            current_week = recent_week.week_identifier if recent_week else 'Unknown'
        
        if not routes:
            return jsonify({
                'success': False,
                'message': 'No data available. Please upload an Excel file first.'
            })
        
        # Calculate summary metrics for the filtered data
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
        
        # Get current week info
        if week_filter and week_filter != 'all':
            current_week_data = RouteAnalysis.query.filter_by(
                session_id=session_id, 
                week_identifier=week_filter
            ).first()
        else:
            current_week_data = RouteAnalysis.query.filter_by(session_id=session_id).order_by(
                RouteAnalysis.week_start_date.desc()
            ).first()
        
        current_week_start = current_week_data.week_start_date if current_week_data else 'Unknown'
        current_week_end = current_week_data.week_end_date if current_week_data else 'Unknown'
        
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
                    'display_name': get_airport_display_name(top_route.route_code) if top_route.city != 'Unknown' else top_route.route_code,
                    'passengers': top_route.total_passengers
                } if top_route else None,
                'busiest_day': {
                    'date': busiest_day,
                    'passengers': busiest_day_pax
                } if busiest_day else None,
                'week': current_week,
                'week_start': current_week_start,
                'week_end': current_week_end
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@route_analysis_bp.route('/charts/top-destinations', methods=['GET'])
def get_top_destinations():
    """Get top destinations chart data with week filtering"""
    try:
        limit = request.args.get('limit', 10, type=int)
        week_filter = request.args.get('week', 'all')
        session_id = get_current_session_id()
        
        # Build query based on week filter
        if week_filter and week_filter != 'all':
            routes = RouteAnalysis.query.filter_by(
                session_id=session_id, 
                week_identifier=week_filter
            ).order_by(RouteAnalysis.total_passengers.desc()).limit(limit).all()
        else:
            routes = RouteAnalysis.query.filter_by(session_id=session_id).order_by(
                RouteAnalysis.total_passengers.desc()
            ).limit(limit).all()
        
        labels = []
        data = []
        
        for r in routes:
            if r.city != 'Unknown':
                labels.append(get_airport_display_name(r.route_code))
            else:
                labels.append(r.route_code)
            data.append(r.total_passengers)
        
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

@route_analysis_bp.route('/charts/daily-trend', methods=['GET'])
def get_daily_trend():
    """Get daily passenger trend chart data with week filtering"""
    try:
        week_filter = request.args.get('week', 'all')
        session_id = get_current_session_id()
        
        # Build query based on week filter
        if week_filter and week_filter != 'all':
            routes = RouteAnalysis.query.filter_by(
                session_id=session_id, 
                week_identifier=week_filter
            ).all()
        else:
            routes = RouteAnalysis.query.filter_by(session_id=session_id).all()
        
        if not routes:
            return jsonify({'success': False, 'message': 'No data available'})
        
        # Aggregate daily totals
        daily_totals = {}
        for route in routes:
            if route.daily_data:
                for date, pax in route.daily_data.items():
                    daily_totals[date] = daily_totals.get(date, 0) + pax
        
        # Sort by date
        sorted_dates = sorted(daily_totals.keys())
        labels = sorted_dates
        data = [daily_totals[date] for date in sorted_dates]
        
        return jsonify({
            'success': True,
            'labels': labels,
            'datasets': [{
                'label': 'Total Passengers',
                'data': data,
                'borderColor': 'rgba(255, 215, 0, 1)',
                'backgroundColor': 'rgba(255, 215, 0, 0.2)',
                'borderWidth': 3,
                'fill': True,
                'tension': 0.4
            }]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@route_analysis_bp.route('/charts/growth-rates', methods=['GET'])
def get_growth_rates():
    """Get growth rates chart data with proper filtering"""
    try:
        limit = request.args.get('limit', 10, type=int)
        week_filter = request.args.get('week', 'all')
        session_id = get_current_session_id()
        
        # Build query based on week filter
        if week_filter and week_filter != 'all':
            routes = RouteAnalysis.query.filter_by(
                session_id=session_id, 
                week_identifier=week_filter
            ).filter(RouteAnalysis.previous_week > 0).order_by(RouteAnalysis.variance_pct.desc()).limit(limit).all()
        else:
            routes = RouteAnalysis.query.filter_by(session_id=session_id).filter(
                RouteAnalysis.previous_week > 0
            ).order_by(RouteAnalysis.variance_pct.desc()).limit(limit).all()
        
        labels = []
        data = []
        
        for r in routes:
            if r.city != 'Unknown':
                labels.append(get_airport_display_name(r.route_code))
            else:
                labels.append(r.route_code)
            data.append(r.variance_pct)
        
        # Color based on positive/negative growth
        colors = ['rgba(0, 128, 0, 0.7)' if v >= 0 else 'rgba(255, 0, 0, 0.7)' for v in data]
        
        return jsonify({
            'success': True,
            'labels': labels,
            'datasets': [{
                'label': 'Growth Rate (%)',
                'data': data,
                'backgroundColor': colors,
                'borderColor': colors,
                'borderWidth': 2
            }]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@route_analysis_bp.route('/charts/passenger-distribution', methods=['GET'])
def get_passenger_distribution():
    """Get passenger distribution by route - show all routes individually"""
    try:
        week_filter = request.args.get('week', 'all')
        session_id = get_current_session_id()
        
        # Build query based on week filter
        if week_filter and week_filter != 'all':
            routes = RouteAnalysis.query.filter_by(
                session_id=session_id, 
                week_identifier=week_filter
            ).order_by(RouteAnalysis.total_passengers.desc()).all()
        else:
            routes = RouteAnalysis.query.filter_by(session_id=session_id).order_by(
                RouteAnalysis.total_passengers.desc()
            ).all()
        
        # Show all routes individually - no "Others" category
        labels = []
        data = []
        
        for r in routes:
            if r.city != 'Unknown':
                labels.append(get_airport_display_name(r.route_code))
            else:
                labels.append(r.route_code)
            data.append(r.total_passengers)
        
        # Generate colors
        colors = [
            'rgba(92, 140, 76, 0.9)',   # Green
            'rgba(252, 204, 44, 0.9)',  # Yellow
            'rgba(196, 36, 43, 0.9)',   # Red
            'rgba(58, 90, 47, 0.9)',    # Dark Green
            'rgba(217, 179, 36, 0.9)',  # Dark Yellow
            'rgba(154, 28, 34, 0.9)',   # Dark Red
            'rgba(123, 166, 107, 0.9)', # Light Green
            'rgba(255, 223, 102, 0.9)', # Light Yellow
            'rgba(128, 128, 128, 0.7)', # Gray
            'rgba(0, 0, 255, 0.7)',     # Blue
            'rgba(255, 165, 0, 0.7)',   # Orange
            'rgba(128, 0, 128, 0.7)',   # Purple
        ]
        
        # Repeat colors if needed
        if len(data) > len(colors):
            colors = colors * (len(data) // len(colors) + 1)
        
        return jsonify({
            'success': True,
            'labels': labels,
            'datasets': [{
                'label': 'Passengers',
                'data': data,
                'backgroundColor': colors[:len(data)],
                'borderColor': '#fff',
                'borderWidth': 2
            }]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@route_analysis_bp.route('/charts/week-comparison', methods=['GET'])
def get_week_comparison():
    """Get current vs previous week comparison"""
    try:
        week_filter = request.args.get('week', 'all')
        session_id = get_current_session_id()
        
        # Build query based on week filter
        if week_filter and week_filter != 'all':
            routes = RouteAnalysis.query.filter_by(
                session_id=session_id, 
                week_identifier=week_filter
            ).order_by(RouteAnalysis.total_passengers.desc()).limit(10).all()
        else:
            routes = RouteAnalysis.query.filter_by(session_id=session_id).order_by(
                RouteAnalysis.total_passengers.desc()
            ).limit(10).all()
        
        labels = []
        current_week = []
        previous_week = []
        
        for r in routes:
            if r.city != 'Unknown':
                labels.append(get_airport_display_name(r.route_code))
            else:
                labels.append(r.route_code)
            current_week.append(r.total_passengers)
            previous_week.append(r.previous_week)
        
        return jsonify({
            'success': True,
            'labels': labels,
            'datasets': [
                {
                    'label': 'Current Week',
                    'data': current_week,
                    'backgroundColor': 'rgba(0, 128, 0, 0.7)',
                    'borderColor': 'rgba(0, 128, 0, 1)',
                    'borderWidth': 2
                },
                {
                    'label': 'Previous Week',
                    'data': previous_week,
                    'backgroundColor': 'rgba(255, 215, 0, 0.7)',
                    'borderColor': 'rgba(255, 215, 0, 1)',
                    'borderWidth': 2
                }
            ]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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

@route_analysis_bp.route('/clear-week', methods=['POST'])
def clear_specific_week():
    """Clear data for a specific week"""
    try:
        data = request.get_json()
        week_identifier = data.get('week')
        
        if not week_identifier:
            return jsonify({'success': False, 'error': 'Week identifier is required'}), 400
        
        session_id = get_current_session_id()
        RouteAnalysis.query.filter_by(
            session_id=session_id, 
            week_identifier=week_identifier
        ).delete()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Data for week {week_identifier} cleared successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@route_analysis_bp.route('/all-data', methods=['GET'])
def get_all_weeks_data():
    """Get data for all weeks to debug"""
    try:
        session_id = get_current_session_id()
        weeks = RouteAnalysis.query.with_entities(
            RouteAnalysis.week_identifier,
            RouteAnalysis.week_start_date,
            RouteAnalysis.week_end_date
        ).filter_by(session_id=session_id).distinct().all()
        
        all_data = []
        for week in weeks:
            routes = RouteAnalysis.query.filter_by(
                session_id=session_id,
                week_identifier=week.week_identifier
            ).all()
            
            week_data = {
                'week_identifier': week.week_identifier,
                'week_start': week.week_start_date,
                'week_end': week.week_end_date,
                'total_routes': len(routes),
                'total_passengers': sum(r.total_passengers for r in routes)
            }
            all_data.append(week_data)
        
        return jsonify({
            'success': True,
            'weeks': all_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
