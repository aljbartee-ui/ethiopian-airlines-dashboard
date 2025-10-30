from flask import Blueprint, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import openpyxl
import os
import time
from datetime import datetime
from src.models.sales import SalesData
from src.models.sales import db

flight_load_bp = Blueprint('flight_load', __name__)

ALLOWED_EXTENSIONS = {'.xlsx', '.xls'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_flight_load_excel(filepath):
    """
    Parse flight load Excel file and extract data
    Expected columns: Travel Date, C cap, Y cap, Tot cap, Pax C, Pax Y, Pax, LF C, LF Y, Load Factor
    """
    wb = openpyxl.load_workbook(filepath, data_only=True)
    
    # Use first sheet
    ws = wb.worksheets[0]
    
    processed_data = {
        'flight_620': [],  # Inbound
        'flight_621': []   # Outbound
    }
    
    # Process Flight 620 (columns A-L)
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[1]:  # If Travel Date exists
            flight_620_data = {
                'travel_date': str(row[1]) if row[1] else None,
                'c_cap': row[3] if row[3] is not None else 0,
                'y_cap': row[4] if row[4] is not None else 0,
                'tot_cap': row[5] if row[5] is not None else 0,
                'pax_c': row[6] if row[6] is not None else 0,
                'pax_y': row[7] if row[7] is not None else 0,
                'pax': row[8] if row[8] is not None else 0,
                'lf_c': row[9] if row[9] is not None else 0,
                'lf_y': row[10] if row[10] is not None else 0,
                'load_factor': row[11] if row[11] is not None else 0
            }
            processed_data['flight_620'].append(flight_620_data)
    
    # Process Flight 621 (columns O-AA)
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[15]:  # If Travel Date exists (column P, index 15)
            flight_621_data = {
                'travel_date': str(row[15]) if row[15] else None,
                'c_cap': row[17] if row[17] is not None else 0,
                'y_cap': row[18] if row[18] is not None else 0,
                'tot_cap': row[19] if row[19] is not None else 0,
                'pax_c': row[20] if row[20] is not None else 0,
                'pax_y': row[21] if row[21] is not None else 0,
                'pax': row[22] if row[22] is not None else 0,
                'lf_c': row[23] if row[23] is not None else 0,
                'lf_y': row[24] if row[24] is not None else 0,
                'load_factor': row[25] if row[25] is not None else 0
            }
            processed_data['flight_621'].append(flight_621_data)
    
    wb.close()
    return processed_data

@flight_load_bp.route('/upload', methods=['POST'])
def upload_flight_load():
    """Handle flight load Excel file upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type. Please upload .xlsx or .xls'}), 400
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        upload_folder = '/tmp'
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        # Process Excel file
        start_time = time.time()
        processed_data = parse_flight_load_excel(filepath)
        processing_time = round(time.time() - start_time, 2)
        
        # Delete existing flight load data
        SalesData.query.filter_by(filename='FLIGHT_LOAD_DATA').delete()
        
        # Create new flight load data entry
        new_data = SalesData(
            filename='FLIGHT_LOAD_DATA',
            is_active=True
        )
        new_data.set_data(processed_data)
        
        db.session.add(new_data)
        db.session.commit()
        
        # Clean up temp file
        os.remove(filepath)
        
        flight_620_count = len(processed_data.get('flight_620', []))
        flight_621_count = len(processed_data.get('flight_621', []))
        
        return jsonify({
            'success': True,
            'message': f'Successfully processed {flight_620_count} records for Flight 620 and {flight_621_count} records for Flight 621',
            'processing_time': processing_time,
            'flight_620_records': flight_620_count,
            'flight_621_records': flight_621_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@flight_load_bp.route('/data', methods=['GET'])
def get_flight_load_data():
    """Get flight load data"""
    try:
        flight_load_data = SalesData.query.filter_by(filename='FLIGHT_LOAD_DATA', is_active=True).first()
        
        if not flight_load_data:
            return jsonify({'success': False, 'error': 'No flight load data available'}), 404
        
        data = flight_load_data.get_data()
        
        return jsonify({
            'success': True,
            'data': data,
            'upload_date': flight_load_data.upload_date.isoformat() if flight_load_data.upload_date else None
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@flight_load_bp.route('/charts/load-factor', methods=['GET'])
def get_load_factor_chart():
    """Get load factor chart data"""
    try:
        flight_load_data = SalesData.query.filter_by(filename='FLIGHT_LOAD_DATA', is_active=True).first()
        
        if not flight_load_data:
            return jsonify({'success': False, 'error': 'No data available'}), 404
        
        data = flight_load_data.get_data()
        
        # Prepare chart data for Flight 620 and 621
        flight_620 = data.get('flight_620', [])
        flight_621 = data.get('flight_621', [])
        
        chart_data = {
            'flight_620': {
                'dates': [record['travel_date'] for record in flight_620],
                'load_factors': [record['load_factor'] for record in flight_620],
                'passengers': [record['pax'] for record in flight_620],
                'capacity': [record['tot_cap'] for record in flight_620]
            },
            'flight_621': {
                'dates': [record['travel_date'] for record in flight_621],
                'load_factors': [record['load_factor'] for record in flight_621],
                'passengers': [record['pax'] for record in flight_621],
                'capacity': [record['tot_cap'] for record in flight_621]
            }
        }
        
        return jsonify({
            'success': True,
            'data': chart_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
