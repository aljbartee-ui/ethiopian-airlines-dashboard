from flask import Blueprint, request, jsonify, session
from src.models.user import db
from src.models.sales import SalesData
import openpyxl
from io import BytesIO
from datetime import datetime
from collections import defaultdict

flight_load_bp = Blueprint('flight_load', __name__)

def process_flight_load_excel(file_content, filename):
    """Process Flight Load Excel file and extract LF 620-621 data"""
    try:
        # Load workbook with data_only=True to read formula values
        workbook = openpyxl.load_workbook(BytesIO(file_content), data_only=True)
        
        # Get the LF 620-621 sheet
        if 'LF 620-621' not in workbook.sheetnames:
            raise ValueError("Sheet 'LF 620-621' not found in Excel file")
        
        sheet = workbook['LF 620-621']
        
        processed_data = {
            'inbound': [],  # Flight 620: ADD to KWI
            'outbound': []  # Flight 621: KWI to ADD
        }
        
        # Process inbound flights (columns A to L)
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if row[0]:  # If flight number exists
                inbound_record = {
                    'flight_no': row[0],
                    'travel_date': row[1].strftime('%Y-%m-%d') if isinstance(row[1], datetime) else str(row[1]),
                    'day': row[2],
                    'c_cap': row[3] or 0,  # Business capacity
                    'y_cap': row[4] or 0,  # Economy capacity
                    'tot_cap': row[5] or 0,  # Total capacity
                    'pax_c': row[6] or 0,  # Business passengers
                    'pax_y': row[7] or 0,  # Economy passengers
                    'pax': row[8] or 0,  # Total passengers
                    'lf_c': float(row[9]) if row[9] else 0,  # Business load factor
                    'lf_y': float(row[10]) if row[10] else 0,  # Economy load factor
                    'lf': float(row[11]) if row[11] else 0  # Total load factor
                }
                processed_data['inbound'].append(inbound_record)
        
        # Process outbound flights (columns O to AA, indices 14 to 26)
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if len(row) > 14 and row[14]:  # If outbound flight number exists
                outbound_record = {
                    'flight_no': row[14],
                    'travel_date': row[15].strftime('%Y-%m-%d') if isinstance(row[15], datetime) else str(row[15]),
                    'day': row[16],
                    'c_cap': row[17] or 0,
                    'y_cap': row[18] or 0,
                    'tot_cap': row[19] or 0,
                    'pax_c': row[20] or 0,
                    'pax_y': row[21] or 0,
                    'pax': row[22] or 0,
                    'lf_c': float(row[23]) if row[23] else 0,
                    'lf_y': float(row[24]) if row[24] else 0,
                    'lf': float(row[25]) if row[25] else 0
                }
                processed_data['outbound'].append(outbound_record)
        
        return processed_data
        
    except Exception as e:
        print(f"Error processing flight load Excel file: {e}")
        raise e

@flight_load_bp.route('/upload', methods=['POST'])
def upload_flight_load():
    """Handle Flight Load Excel file upload (admin only)"""
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
        processed_data = process_flight_load_excel(file_content, file.filename)
        
        if not processed_data['inbound'] and not processed_data['outbound']:
            return jsonify({'error': 'No flight load data found in Excel file'}), 400
        
        # Store in database (reusing SalesData model with a different identifier)
        # Deactivate previous flight load data
        SalesData.query.filter_by(filename='FLIGHT_LOAD_DATA').update({'is_active': False})
        
        # Create new flight load data entry
        new_data = SalesData(
            filename='FLIGHT_LOAD_DATA',
            data=processed_data,
            is_active=True
        )
        
        db.session.add(new_data)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Flight load data uploaded successfully',
            'inbound_records': len(processed_data['inbound']),
            'outbound_records': len(processed_data['outbound'])
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to process file: {str(e)}'}), 500

@flight_load_bp.route('/data')
def get_flight_load_data():
    """Get flight load data with optional filters"""
    # Check authentication
    is_admin = session.get('admin_logged_in', False)
    is_public = session.get('public_authenticated', False)
    
    if not is_admin and not is_public:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        # Get active flight load data
        flight_data = SalesData.query.filter_by(filename='FLIGHT_LOAD_DATA', is_active=True).first()
        
        if not flight_data:
            return jsonify({'error': 'No flight load data available'}), 404
        
        data = flight_data.get_data()
        
        # Get filter parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        flight_type = request.args.get('flight_type', 'both')  # inbound, outbound, or both
        
        # Filter data
        filtered_data = {
            'inbound': data.get('inbound', []),
            'outbound': data.get('outbound', [])
        }
        
        # Apply date filters
        if start_date:
            filtered_data['inbound'] = [r for r in filtered_data['inbound'] if r['travel_date'] >= start_date]
            filtered_data['outbound'] = [r for r in filtered_data['outbound'] if r['travel_date'] >= start_date]
        
        if end_date:
            filtered_data['inbound'] = [r for r in filtered_data['inbound'] if r['travel_date'] <= end_date]
            filtered_data['outbound'] = [r for r in filtered_data['outbound'] if r['travel_date'] <= end_date]
        
        # Apply flight type filter
        if flight_type == 'inbound':
            filtered_data['outbound'] = []
        elif flight_type == 'outbound':
            filtered_data['inbound'] = []
        
        return jsonify({
            'success': True,
            'data': filtered_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@flight_load_bp.route('/summary')
def get_flight_load_summary():
    """Get summary statistics for flight load data"""
    # Check authentication
    is_admin = session.get('admin_logged_in', False)
    is_public = session.get('public_authenticated', False)
    
    if not is_admin and not is_public:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        # Get active flight load data
        flight_data = SalesData.query.filter_by(filename='FLIGHT_LOAD_DATA', is_active=True).first()
        
        if not flight_data:
            return jsonify({'error': 'No flight load data available'}), 404
        
        data = flight_data.get_data()
        
        # Get filter parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        inbound = data.get('inbound', [])
        outbound = data.get('outbound', [])
        
        # Apply date filters
        if start_date:
            inbound = [r for r in inbound if r['travel_date'] >= start_date]
            outbound = [r for r in outbound if r['travel_date'] >= start_date]
        
        if end_date:
            inbound = [r for r in inbound if r['travel_date'] <= end_date]
            outbound = [r for r in outbound if r['travel_date'] <= end_date]
        
        # Calculate summary statistics
        def calc_stats(records):
            if not records:
                return {
                    'avg_lf': 0,
                    'avg_lf_c': 0,
                    'avg_lf_y': 0,
                    'total_pax': 0,
                    'total_pax_c': 0,
                    'total_pax_y': 0,
                    'total_capacity': 0,
                    'flights_count': 0
                }
            
            return {
                'avg_lf': sum(r['lf'] for r in records) / len(records) * 100,
                'avg_lf_c': sum(r['lf_c'] for r in records) / len(records) * 100,
                'avg_lf_y': sum(r['lf_y'] for r in records) / len(records) * 100,
                'total_pax': sum(r['pax'] for r in records),
                'total_pax_c': sum(r['pax_c'] for r in records),
                'total_pax_y': sum(r['pax_y'] for r in records),
                'total_capacity': sum(r['tot_cap'] for r in records),
                'flights_count': len(records)
            }
        
        summary = {
            'inbound': calc_stats(inbound),
            'outbound': calc_stats(outbound),
            'combined': calc_stats(inbound + outbound)
        }
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


