from flask import Blueprint, request, jsonify, session
from src.routes.auth import admin_required
from src.models.user import db
from src.models.route_analysis import ManualForecast
from datetime import datetime, timedelta
import json

manual_forecast_bp = Blueprint('manual_forecast', __name__)

@manual_forecast_bp.route('/data', methods=['GET'])
@admin_required
def get_manual_forecast_data():
    """
    Get manual forecast data for a date range and direction.
    Returns data in an Excel-friendly format (list of lists/rows).
    """
    try:
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        direction = request.args.get('direction', 'INBOUND').upper()
        
        if not start_date_str or not end_date_str:
            return jsonify({'error': 'start_date and end_date are required'}), 400
            
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # 1. Fetch all relevant data
        query = ManualForecast.query.filter(
            ManualForecast.travel_date.between(start_date, end_date),
            ManualForecast.direction == direction
        )
        records = query.all()
        
        # 2. Prepare the date range columns
        date_range = []
        current_date = start_date
        while current_date <= end_date:
            date_range.append(current_date.isoformat())
            current_date += timedelta(days=1)
            
        # 3. Group data by airport code
        data_by_airport = {}
        airport_codes = set()
        for record in records:
            airport_codes.add(record.airport_code)
            if record.airport_code not in data_by_airport:
                data_by_airport[record.airport_code] = {}
            data_by_airport[record.airport_code][record.travel_date.isoformat()] = {
                'pax': record.forecast_pax,
                'source': record.data_source
            }
            
        # 4. Construct the Excel-friendly table data
        # Header row: ['Destination', 'Date 1', 'Date 2', ...]
        header = ['Destination'] + date_range
        
        table_data = []
        for code in sorted(list(airport_codes)):
            row = [code]
            for date_str in date_range:
                cell_data = data_by_airport.get(code, {}).get(date_str, {'pax': '', 'source': 'manual'})
                row.append({
                    'value': cell_data['pax'],
                    'source': cell_data['source']
                })
            table_data.append(row)
            
        return jsonify({
            'success': True,
            'header': header,
            'data': table_data,
            'direction': direction,
            'start_date': start_date_str,
            'end_date': end_date_str
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@manual_forecast_bp.route('/data', methods=['POST'])
@admin_required
def save_manual_forecast_data():
    """
    Save manual forecast data from the Excel-friendly interface.
    Expects: {
        "direction": "INBOUND",
        "data": [
            {"airport_code": "KWI", "date": "2025-12-01", "pax": 150},
            ...
        ]
    }
    """
    try:
        data = request.get_json()
        direction = data.get('direction', 'INBOUND').upper()
        records_to_save = data.get('data', [])
        
        if not records_to_save:
            return jsonify({'error': 'No data provided to save'}), 400
            
        saved_count = 0
        
        with db.session.begin_nested():
            for record_data in records_to_save:
                airport_code = record_data.get('airport_code')
                date_str = record_data.get('date')
                pax = record_data.get('pax')
                
                if not airport_code or not date_str or pax is None:
                    continue
                    
                travel_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                # Check if a manifest record exists for this date/airport
                existing_record = ManualForecast.query.filter_by(
                    travel_date=travel_date,
                    airport_code=airport_code,
                    direction=direction
                ).first()
                
                if existing_record:
                    # If manifest data exists, DO NOT override it with manual forecast
                    if existing_record.data_source == 'manifest':
                        continue
                    
                    # Update existing manual forecast
                    existing_record.forecast_pax = int(pax)
                    existing_record.last_updated = datetime.utcnow()
                    existing_record.data_source = 'manual'
                else:
                    # Create new manual forecast
                    new_record = ManualForecast(
                        travel_date=travel_date,
                        airport_code=airport_code,
                        direction=direction,
                        forecast_pax=int(pax),
                        data_source='manual'
                    )
                    db.session.add(new_record)
                
                saved_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully saved {saved_count} manual forecast records.',
            'saved_count': saved_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to save data: {str(e)}'}), 500
