from flask import Blueprint, request, jsonify, session
from src.models.user import db
from src.models.sales import SalesData, AdminUser
import os
import json
from datetime import datetime
import base64

sales_bp = Blueprint('sales', __name__)

@sales_bp.route('/data')
def get_current_data():
    """Get information about the current active dataset"""
    try:
        active_data = SalesData.query.filter_by(is_active=True).first()
        if active_data:
            return jsonify({
                'filename': active_data.filename,
                'upload_date': active_data.upload_date.isoformat(),
                'sheets': ['Sheet1']  # Simplified for now
            })
        else:
            return jsonify({'error': 'No data available'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sales_bp.route('/upload', methods=['POST'])
def upload_file():
    """Handle Excel file upload (admin only)"""
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
        # For now, just store basic file info
        # Deactivate all previous data
        SalesData.query.update({'is_active': False})
        
        # Create new sales data entry
        sales_data = SalesData(
            filename=file.filename,
            data_json=json.dumps({'sample': 'data'}),  # Simplified for now
            is_active=True
        )
        
        db.session.add(sales_data)
        db.session.commit()
        
        return jsonify({
            'message': 'File uploaded and processed successfully',
            'filename': file.filename,
            'data_id': sales_data.id,
            'sheets': ['Sheet1']
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@sales_bp.route('/charts/default')
def generate_default_charts():
    """Generate default charts from the active dataset"""
    try:
        active_data = SalesData.query.filter_by(is_active=True).first()
        if not active_data:
            return jsonify({'error': 'No active dataset found'}), 404
        
        # For now, return sample chart data
        sample_charts = {
            'bar_chart': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
            'line_chart': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
            'pie_chart': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
            'histogram': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
        }
        
        return jsonify(sample_charts)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
