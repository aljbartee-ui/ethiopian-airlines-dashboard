from flask import Blueprint, request, jsonify, session
from src.models.user import db
from src.models.flight_load import FlightLoadRecord
import pandas as pd
from io import BytesIO
from datetime import datetime
from collections import defaultdict

flight_load_bp = Blueprint('flight_load', __name__)

def safe_int(value):
    """Safely convert value to int, handling non-numeric values"""
    if value is None or value == '' or pd.isna(value):
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        if value.strip().upper() in ['X', 'N/A', 'NA', '-', '']:
            return 0
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return 0
    return 0

def safe_float(value):
    """Safely convert value to float, handling non-numeric values"""
    if value is None or value == '' or pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        if value.strip().upper() in ['X', 'N/A', 'NA', '-', '']:
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    return 0.0

def parse_date(value):
    """Parse date from various formats"""
    if value is None or pd.isna(value):
        return None
    
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d')
    
    if isinstance(value, pd.Timestamp):
        return value.strftime('%Y-%m-%d')
    
    if isinstance(value, str):
        value = value.strip()
        if not value or value in ['', ' ', 'NaT']:
            return None
        
        # Try various date formats
        formats = ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']
        for fmt in formats:
            try:
                return datetime.strptime(value.split(' ')[0], fmt).strftime('%Y-%m-%d')
            except:
                continue
    
    return None

def process_flight_load_excel(file_content, filename):
    """Process Flight Load Excel file using pandas"""
    try:
        # Read Excel file with pandas
        xlsx = pd.ExcelFile(BytesIO(file_content))
        
        if not xlsx.sheet_names:
            raise ValueError("No sheets found in Excel file")
        
        # Use first sheet
        sheet_name = xlsx.sheet_names[0]
        df = pd.read_excel(xlsx, sheet_name=sheet_name)
        
        print(f"Processing sheet: {sheet_name}")
        print(f"Columns: {list(df.columns)}")
        print(f"Total rows: {len(df)}")
        
        processed_data = {
            'inbound': [],   # Flight 620: ADD to KWI
            'outbound': []   # Flight 621: KWI to ADD
        }
        
        # Process each row
        for idx, row in df.iterrows():
            # Process inbound flight (ET620) - columns 0-11
            if pd.notna(row.iloc[0]) and pd.notna(row.iloc[1]):
                travel_date = parse_date(row.iloc[1])
                if travel_date:
                    inbound_record = {
                        'flight_no': str(int(row.iloc[0])) if isinstance(row.iloc[0], (int, float)) else str(row.iloc[0]),
                        'travel_date': travel_date,
                        'day': str(row.iloc[2]) if pd.notna(row.iloc[2]) else '',
                        'c_cap': safe_int(row.iloc[3]),
                        'y_cap': safe_int(row.iloc[4]),
                        'tot_cap': safe_int(row.iloc[5]),
                        'pax_c': safe_int(row.iloc[6]),
                        'pax_y': safe_int(row.iloc[7]),
                        'pax': safe_int(row.iloc[8]),
                        'lf_c': safe_float(row.iloc[9]) * 100 if safe_float(row.iloc[9]) <= 1 else safe_float(row.iloc[9]),
                        'lf_y': safe_float(row.iloc[10]) * 100 if safe_float(row.iloc[10]) <= 1 else safe_float(row.iloc[10]),
                        'lf': safe_float(row.iloc[11]) * 100 if safe_float(row.iloc[11]) <= 1 else safe_float(row.iloc[11])
                    }
                    processed_data['inbound'].append(inbound_record)
            
            # Process outbound flight (ET621) - columns 14-25
            if len(row) > 14 and pd.notna(row.iloc[14]) and pd.notna(row.iloc[15]):
                travel_date = parse_date(row.iloc[15])
                if travel_date:
                    outbound_record = {
                        'flight_no': str(int(row.iloc[14])) if isinstance(row.iloc[14], (int, float)) else str(row.iloc[14]),
                        'travel_date': travel_date,
                        'day': str(row.iloc[16]) if pd.notna(row.iloc[16]) else '',
                        'c_cap': safe_int(row.iloc[17]),
                        'y_cap': safe_int(row.iloc[18]),
                        'tot_cap': safe_int(row.iloc[19]),
                        'pax_c': safe_int(row.iloc[20]),
                        'pax_y': safe_int(row.iloc[21]),
                        'pax': safe_int(row.iloc[22]),
                        'lf_c': safe_float(row.iloc[23]) * 100 if safe_float(row.iloc[23]) <= 1 else safe_float(row.iloc[23]),
                        'lf_y': safe_float(row.iloc[24]) * 100 if safe_float(row.iloc[24]) <= 1 else safe_float(row.iloc[24]),
                        'lf': safe_float(row.iloc[25]) * 100 if safe_float(row.iloc[25]) <= 1 else safe_float(row.iloc[25])
                    }
                    processed_data['outbound'].append(outbound_record)
        
        print(f"Processed {len(processed_data['inbound'])} inbound records")
        print(f"Processed {len(processed_data['outbound'])} outbound records")
        
        return processed_data
        
    except Exception as e:
        print(f"Error processing flight load Excel file: {e}")
        import traceback
        traceback.print_exc()
        raise e

@flight_load_bp.route('/upload', methods=['POST'])
def upload_flight_load():
    """Handle Load Factor Excel file upload - Forecast Data"""
    
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
            return jsonify({'error': 'No valid flight load data found in Excel file'}), 400
        
        all_records = processed_data['inbound'] + processed_data['outbound']
        records_saved = 0
        records_updated = 0
        
        for record in all_records:
            try:
                travel_date = datetime.strptime(record['travel_date'], '%Y-%m-%d').date()
                flight_no = record['flight_no']
                
                # Check if record exists
                existing_record = FlightLoadRecord.query.filter_by(
                    travel_date=travel_date,
                    flight_no=flight_no
                ).first()
                
                if existing_record:
                    # Update existing record (unless it's from manifest)
                    if existing_record.data_source != 'manifest':
                        existing_record.update_from_dict(record)
                        existing_record.data_source = 'forecast'
                        records_updated += 1
                else:
                    # Create new record
                    new_record = FlightLoadRecord(
                        travel_date=travel_date,
                        flight_no=flight_no,
                        data_source='forecast'
                    )
                    new_record.update_from_dict(record)
                    db.session.add(new_record)
                    records_saved += 1
            except Exception as e:
                print(f"Error saving record: {e}")
                continue
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Load Factor data uploaded successfully',
            'records_saved': records_saved,
            'records_updated': records_updated,
            'total_inbound': len(processed_data['inbound']),
            'total_outbound': len(processed_data['outbound'])
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to process file: {str(e)}'}), 500

@flight_load_bp.route('/upload-excel', methods=['POST'])
def upload_excel():
    """Alias for upload endpoint"""
    return upload_flight_load()

@flight_load_bp.route('/data')
def get_flight_load_data():
    """Get flight load data with optional filters"""
    try:
        # Get filter parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        flight = request.args.get('flight', 'all')
        
        query = FlightLoadRecord.query
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            query = query.filter(FlightLoadRecord.travel_date >= start_date)
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            query = query.filter(FlightLoadRecord.travel_date <= end_date)
        
        if flight and flight != 'all':
            # Handle ET620/ET621 format
            flight_no = flight.replace('ET', '')
            query = query.filter(FlightLoadRecord.flight_no == flight_no)
            
        all_records = query.order_by(FlightLoadRecord.travel_date.desc()).all()
        
        records = []
        for record in all_records:
            records.append({
                'date': record.travel_date.strftime('%Y-%m-%d'),
                'flight': f"ET{record.flight_no}",
                'capacity': record.tot_cap,
                'forecast': record.pax if record.data_source == 'forecast' else 0,
                'actual': record.pax if record.data_source == 'manifest' else 0,
                'load_factor': record.lf,
                'data_source': record.data_source
            })
        
        # Calculate stats
        total_passengers = sum(r['actual'] or r['forecast'] for r in records)
        avg_load_factor = sum(r['load_factor'] for r in records) / len(records) if records else 0
        
        return jsonify({
            'success': True,
            'records': records,
            'record_count': len(records),
            'total_passengers': total_passengers,
            'avg_load_factor': avg_load_factor
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@flight_load_bp.route('/summary')
def get_flight_load_summary():
    """Get summary statistics for flight load data"""
    try:
        all_records = FlightLoadRecord.query.all()
        
        inbound = [r for r in all_records if r.flight_no == '620']
        outbound = [r for r in all_records if r.flight_no == '621']
        
        def calc_stats(records):
            if not records:
                return {
                    'avg_lf': 0.0,
                    'total_pax': 0,
                    'total_capacity': 0,
                    'flights_count': 0
                }
            
            total_pax = sum(r.pax for r in records)
            total_capacity = sum(r.tot_cap for r in records)
            avg_lf = (total_pax / total_capacity) * 100 if total_capacity > 0 else 0.0
            
            return {
                'avg_lf': round(avg_lf, 2),
                'total_pax': total_pax,
                'total_capacity': total_capacity,
                'flights_count': len(records)
            }
        
        return jsonify({
            'success': True,
            'summary': {
                'inbound': calc_stats(inbound),
                'outbound': calc_stats(outbound),
                'combined': calc_stats(inbound + outbound)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
