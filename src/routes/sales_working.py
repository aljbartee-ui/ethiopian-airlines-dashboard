from flask import Blueprint, request, jsonify, session
from src.models.user import db
from src.models.sales import SalesData
from src.models.user import AdminUser
import os
import json
from datetime import datetime
import base64
import openpyxl
from io import BytesIO

sales_bp = Blueprint('sales', __name__)

def process_excel_file(file_content, filename):
    """Process Excel file and extract data"""
    try:
        # Load workbook from bytes with data_only=True to read formula values
        workbook = openpyxl.load_workbook(BytesIO(file_content), data_only=True)
        
        processed_data = {}
        
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            
            # Get headers from first row
            headers = []
            for cell in sheet[1]:
                headers.append(cell.value if cell.value is not None else '')
            
            # Get data rows
            data_rows = []
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if any(cell is not None for cell in row):  # Skip empty rows
                    row_dict = {}
                    for i, value in enumerate(row):
                        if i < len(headers):
                            # Convert datetime objects to strings
                            if hasattr(value, 'strftime'):
                                value = value.strftime('%Y-%m-%d %H:%M:%S')
                            row_dict[headers[i]] = value
                    data_rows.append(row_dict)
            
            processed_data[sheet_name] = {
                'headers': headers,
                'data': data_rows,
                'row_count': len(data_rows)
            }
        
        return processed_data
        
    except Exception as e:
        print(f"Error processing Excel file: {e}")
        raise e

@sales_bp.route('/data')
def get_current_data():
    """Get information about the current active dataset"""
    try:
        active_data = SalesData.query.filter_by(is_active=True).first()
        if active_data:
            data = active_data.get_data()
            sheets = list(data.keys()) if data else []
            return jsonify({
                'filename': active_data.filename,
                'upload_date': active_data.upload_date.isoformat(),
                'sheets': sheets,
                'total_rows': sum(sheet_data.get('row_count', 0) for sheet_data in data.values()) if data else 0
            })
        else:
            return jsonify({'error': 'No data available'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

from src.routes.auth import admin_required

@sales_bp.route('/upload', methods=['POST'])
@admin_required
def upload_file():
    """Handle Excel file upload (admin only)"""
    
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
        processed_data = process_excel_file(file_content, file.filename)
        
        if not processed_data:
            return jsonify({'error': 'No data found in Excel file'}), 400
        
        # Deactivate all previous data
        SalesData.query.update({'is_active': False})
        
        # Create new sales data entry
        sales_data = SalesData(
            filename=file.filename,
            data_json=json.dumps(processed_data),
            is_active=True
        )
        
        db.session.add(sales_data)
        db.session.commit()
        
        # Calculate summary statistics
        total_rows = sum(sheet_data.get('row_count', 0) for sheet_data in processed_data.values())
        sheets = list(processed_data.keys())
        
        return jsonify({
            'message': 'File uploaded and processed successfully',
            'filename': file.filename,
            'data_id': sales_data.id,
            'sheets': sheets,
            'total_rows': total_rows,
            'summary': {
                'sheets_processed': len(sheets),
                'total_data_rows': total_rows
            }
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Upload error: {e}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@sales_bp.route('/charts/default')
def generate_default_charts():
    """Generate default charts from the active dataset"""
    try:
        active_data = SalesData.query.filter_by(is_active=True).first()
        if not active_data:
            return jsonify({'error': 'No active dataset found'}), 404
        
        # Get the actual data
        data = active_data.get_data()
        if not data:
            return jsonify({'error': 'No data available'}), 404
        
        # Return success message for now - charts will be generated by the charts endpoint
        return jsonify({
            'message': 'Data is ready for chart generation',
            'sheets': list(data.keys()),
            'total_rows': sum(sheet_data.get('row_count', 0) for sheet_data in data.values())
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sales_bp.route('/debug/data')
def debug_data():
    """Debug endpoint to check data structure"""
    try:
        active_data = SalesData.query.filter_by(is_active=True).first()
        if not active_data:
            return jsonify({'error': 'No active dataset found'}), 404
        
        data = active_data.get_data()
        
        # Return structure info
        debug_info = {}
        for sheet_name, sheet_data in data.items():
            debug_info[sheet_name] = {
                'headers': sheet_data.get('headers', []),
                'row_count': sheet_data.get('row_count', 0),
                'sample_row': sheet_data.get('data', [{}])[0] if sheet_data.get('data') else {}
            }
        
        return jsonify({
            'filename': active_data.filename,
            'upload_date': active_data.upload_date.isoformat(),
            'debug_info': debug_info
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
