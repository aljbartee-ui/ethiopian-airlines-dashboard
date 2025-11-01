from flask import Blueprint, request, jsonify, session
from src.models.user import db
from src.models.route_analysis import RouteAnalysisData
import json
from datetime import datetime
import openpyxl
from io import BytesIO

route_analysis_bp = Blueprint('route_analysis', __name__)

def process_route_excel_file(file_content, filename):
    """Process Route Analysis Excel file and extract data"""
    try:
        # Load workbook from bytes with data_only=True to read formula values
        workbook = openpyxl.load_workbook(BytesIO(file_content), data_only=True)
        
        # Use the first sheet (active sheet)
        sheet = workbook.active
        sheet_name = sheet.title
        
        # Row 2 contains headers
        headers = []
        for col_idx in range(1, sheet.max_column + 1):
            header = sheet.cell(2, col_idx).value
            headers.append(header if header is not None else f'Column_{col_idx}')
        
        # Extract data starting from row 3
        routes_data = []
        daily_totals = {}
        
        for row_idx in range(3, sheet.max_row + 1):
            # Get route point from column 1
            route_point = sheet.cell(row_idx, 1).value
            
            if route_point and isinstance(route_point, str):
                row_data = {
                    'route': route_point,
                    'daily_values': {},
                    'grand_total': 0,
                    'previous_week': 0,
                    'variance': 0
                }
                
                # Extract daily values (columns 2-7)
                for col_idx in range(2, 8):
                    value = sheet.cell(row_idx, col_idx).value
                    date_header = headers[col_idx - 1]
                    
                    if value is not None and isinstance(value, (int, float)):
                        # Convert datetime header to string if needed
                        if isinstance(date_header, datetime):
                            date_str = date_header.strftime('%Y-%m-%d')
                        else:
                            date_str = str(date_header)
                        
                        row_data['daily_values'][date_str] = int(value)
                        
                        # Accumulate daily totals
                        if date_str not in daily_totals:
                            daily_totals[date_str] = 0
                        daily_totals[date_str] += int(value)
                
                # Get grand total (column 8)
                grand_total = sheet.cell(row_idx, 8).value
                if grand_total and isinstance(grand_total, (int, float)):
                    row_data['grand_total'] = int(grand_total)
                
                # Get previous week (column 9)
                prev_week = sheet.cell(row_idx, 9).value
                if prev_week and isinstance(prev_week, (int, float)):
                    row_data['previous_week'] = int(prev_week)
                
                # Calculate variance
                if row_data['grand_total'] and row_data['previous_week']:
                    row_data['variance'] = row_data['grand_total'] - row_data['previous_week']
                    row_data['variance_pct'] = round((row_data['variance'] / row_data['previous_week']) * 100, 2) if row_data['previous_week'] > 0 else 0
                
                routes_data.append(row_data)
        
        # Calculate summary metrics
        total_passengers = sum(r['grand_total'] for r in routes_data)
        total_previous = sum(r['previous_week'] for r in routes_data)
        total_variance = total_passengers - total_previous
        variance_pct = round((total_variance / total_previous) * 100, 2) if total_previous > 0 else 0
        
        # Find top route
        top_route = max(routes_data, key=lambda x: x['grand_total']) if routes_data else None
        
        # Find busiest day
        busiest_day = max(daily_totals.items(), key=lambda x: x[1]) if daily_totals else (None, 0)
        
        processed_data = {
            'sheet_name': sheet_name,
            'routes': routes_data,
            'daily_totals': daily_totals,
            'summary': {
                'total_routes': len(routes_data),
                'total_passengers': total_passengers,
                'previous_week_passengers': total_previous,
                'variance': total_variance,
                'variance_pct': variance_pct,
                'top_route': top_route['route'] if top_route else 'N/A',
                'top_route_passengers': top_route['grand_total'] if top_route else 0,
                'busiest_day': busiest_day[0] if busiest_day[0] else 'N/A',
                'busiest_day_passengers': busiest_day[1] if busiest_day[0] else 0
            }
        }
        
        return processed_data
        
    except Exception as e:
        print(f"Error processing Route Analysis Excel file: {e}")
        raise e

@route_analysis_bp.route('/data')
def get_current_data():
    """Get information about the current active route analysis dataset"""
    try:
        active_data = RouteAnalysisData.query.filter_by(is_active=True).first()
        if active_data:
            data = active_data.get_data()
            return jsonify({
                'filename': active_data.filename,
                'upload_date': active_data.upload_date.isoformat(),
                'summary': data.get('summary', {}),
                'total_routes': len(data.get('routes', []))
            })
        else:
            return jsonify({'error': 'No data available'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@route_analysis_bp.route('/upload', methods=['POST'])
def upload_file():
    """Handle Route Analysis Excel file upload (admin only)"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Admin authentication required'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'Invalid file type. Please upload Excel files only.'}), 400
    
    try:
        # Read file content
        file_content = file.read()
        
        # Process Excel file
        processed_data = process_route_excel_file(file_content, file.filename)
        
        if not processed_data or not processed_data.get('routes'):
            return jsonify({'error': 'No route data found in Excel file'}), 400
        
        # Deactivate all previous data
        RouteAnalysisData.query.update({'is_active': False})
        
        # Create new route analysis data entry using set_data method
        route_data = RouteAnalysisData(
            filename=file.filename,
            is_active=True
        )
        route_data.set_data(processed_data)
        
        db.session.add(route_data)
        db.session.commit()
        
        return jsonify({
            'message': 'File uploaded and processed successfully',
            'filename': file.filename,
            'data_id': route_data.id,
            'summary': processed_data.get('summary', {})
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Upload error: {e}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@route_analysis_bp.route('/charts/top-routes')
def get_top_routes():
    """Get top 10 routes by passenger count"""
    try:
        active_data = RouteAnalysisData.query.filter_by(is_active=True).first()
        if not active_data:
            return jsonify({'error': 'No active dataset found'}), 404
        
        data = active_data.get_data()
        routes = data.get('routes', [])
        
        # Sort by grand total and get top 10
        top_routes = sorted(routes, key=lambda x: x['grand_total'], reverse=True)[:10]
        
        return jsonify({
            'labels': [r['route'] for r in top_routes],
            'data': [r['grand_total'] for r in top_routes],
            'previous_week': [r['previous_week'] for r in top_routes]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@route_analysis_bp.route('/charts/daily-trend')
def get_daily_trend():
    """Get daily passenger trend"""
    try:
        active_data = RouteAnalysisData.query.filter_by(is_active=True).first()
        if not active_data:
            return jsonify({'error': 'No active dataset found'}), 404
        
        data = active_data.get_data()
        daily_totals = data.get('daily_totals', {})
        
        # Sort by date
        sorted_days = sorted(daily_totals.items())
        
        return jsonify({
            'labels': [day[0] for day in sorted_days],
            'data': [day[1] for day in sorted_days]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@route_analysis_bp.route('/charts/growth')
def get_growth_chart():
    """Get routes with highest growth (variance)"""
    try:
        active_data = RouteAnalysisData.query.filter_by(is_active=True).first()
        if not active_data:
            return jsonify({'error': 'No active dataset found'}), 404
        
        data = active_data.get_data()
        routes = data.get('routes', [])
        
        # Filter routes with variance and sort by variance percentage
        routes_with_variance = [r for r in routes if r.get('variance_pct') is not None]
        sorted_routes = sorted(routes_with_variance, key=lambda x: abs(x['variance_pct']), reverse=True)[:10]
        
        return jsonify({
            'labels': [r['route'] for r in sorted_routes],
            'data': [r['variance_pct'] for r in sorted_routes],
            'variance': [r['variance'] for r in sorted_routes]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@route_analysis_bp.route('/charts/distribution')
def get_distribution():
    """Get passenger distribution by route (top 10)"""
    try:
        active_data = RouteAnalysisData.query.filter_by(is_active=True).first()
        if not active_data:
            return jsonify({'error': 'No active dataset found'}), 404
        
        data = active_data.get_data()
        routes = data.get('routes', [])
        
        # Get top 10 routes
        top_routes = sorted(routes, key=lambda x: x['grand_total'], reverse=True)[:10]
        
        # Calculate "Others"
        top_total = sum(r['grand_total'] for r in top_routes)
        all_total = sum(r['grand_total'] for r in routes)
        others = all_total - top_total
        
        labels = [r['route'] for r in top_routes]
        data_values = [r['grand_total'] for r in top_routes]
        
        if others > 0:
            labels.append('Others')
            data_values.append(others)
        
        return jsonify({
            'labels': labels,
            'data': data_values
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@route_analysis_bp.route('/debug/data')
def debug_data():
    """Debug endpoint to check data structure"""
    try:
        active_data = RouteAnalysisData.query.filter_by(is_active=True).first()
        if not active_data:
            return jsonify({'error': 'No active dataset found'}), 404
        
        data = active_data.get_data()
        
        # Return structure info
        debug_info = {
            'sheet_name': data.get('sheet_name'),
            'total_routes': len(data.get('routes', [])),
            'sample_route': data.get('routes', [{}])[0] if data.get('routes') else {},
            'summary': data.get('summary', {})
        }
        
        return jsonify({
            'filename': active_data.filename,
            'upload_date': active_data.upload_date.isoformat(),
            'debug_info': debug_info
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

