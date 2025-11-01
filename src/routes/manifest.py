"""
Daily Manifest Routes
Handles manifest upload, parsing, and data retrieval
"""

from flask import Blueprint, request, jsonify, session
import re
from datetime import datetime, timedelta
from collections import Counter
from src.models.user import db
from src.models.manifest import DailyManifest
from src.utils.airport_lookup import get_airport_info

# UNIQUE blueprint name to avoid conflicts
manifest_bp = Blueprint('daily_manifest', __name__)

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
        'route_breakdown': {}
    }
    
    lines = manifest_text.strip().split('\n')
    
    # Extract flight number and date from first few lines
    for line in lines[:10]:
        # Look for flight number pattern (e.g., ET 620, ET620)
        flight_match = re.search(r'ET\s*(\d{3,4})', line, re.IGNORECASE)
        if flight_match and not result['flight_number']:
            result['flight_number'] = f"ET{flight_match.group(1)}"
        
        # Look for date patterns
        date_match = re.search(r'(\d{1,2}[/-]\w{3}[/-]\d{2,4})', line)
        if date_match and not result['flight_date']:
            try:
                date_str = date_match.group(1)
                result['flight_date'] = datetime.strptime(date_str, '%d-%b-%Y').strftime('%Y-%m-%d')
            except:
                try:
                    result['flight_date'] = datetime.strptime(date_str, '%d/%b/%Y').strftime('%Y-%m-%d')
                except:
                    pass
    
    # Extract passenger data and routes
    for line in lines:
        # Look for passenger entries with origin codes
        # Pattern: Name followed by 3-letter code
        passenger_match = re.findall(r'\b([A-Z]{3})\b', line)
        
        if passenger_match:
            for code in passenger_match:
                # Filter out common non-airport codes
                if code not in ['MR', 'MRS', 'MS', 'DR', 'ADD', 'ETH', 'PAX', 'SEQ', 'PNR']:
                    # Check if it's a valid airport code
                    airport_info = get_airport_info(code)
                    if airport_info:
                        result['route_breakdown'][code] = result['route_breakdown'].get(code, 0) + 1
                        result['total_passengers'] += 1
        
        # Count class passengers
        if 'C CLASS' in line.upper() or '/C' in line:
            result['c_class_passengers'] += 1
        elif 'Y CLASS' in line.upper() or '/Y' in line:
            result['y_class_passengers'] += 1
    
    return result

@manifest_bp.route('/upload', methods=['POST'])
def upload_manifest():
    """Upload and parse manifest file"""
    # Check authentication
    is_admin = session.get('admin_logged_in', False)
    if not is_admin:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    try:
        data = request.get_json()
        manifest_text = data.get('manifest_text', '')
        direction = data.get('direction', 'inbound')  # 'inbound' or 'outbound'
        
        if not manifest_text:
            return jsonify({'success': False, 'error': 'No manifest data provided'}), 400
        
        # Parse the manifest
        parsed_data = parse_manifest_text(manifest_text)
        
        if not parsed_data['flight_number'] or not parsed_data['flight_date']:
            return jsonify({'success': False, 'error': 'Could not extract flight number or date'}), 400
        
        # Check if record already exists
        existing = DailyManifest.query.filter_by(
            flight_number=parsed_data['flight_number'],
            flight_date=parsed_data['flight_date'],
            direction=direction
        ).first()
        
        if existing:
            # Update existing record
            existing.total_passengers = parsed_data['total_passengers']
            existing.route_breakdown = parsed_data['route_breakdown']
        else:
            # Create new record
            manifest = DailyManifest(
                flight_number=parsed_data['flight_number'],
                flight_date=parsed_data['flight_date'],
                direction=direction,
                total_passengers=parsed_data['total_passengers'],
                route_breakdown=parsed_data['route_breakdown']
            )
            db.session.add(manifest)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'flight_number': parsed_data['flight_number'],
                'flight_date': parsed_data['flight_date'],
                'direction': direction,
                'total_passengers': parsed_data['total_passengers'],
                'route_breakdown': parsed_data['route_breakdown']
            }
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@manifest_bp.route('/data', methods=['GET'])
def get_manifest_data():
    """Get manifest data for a specific period"""
    try:
        days = int(request.args.get('days', 30))
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Query data
        manifests = DailyManifest.query.filter(
            DailyManifest.flight_date >= start_date.strftime('%Y-%m-%d'),
            DailyManifest.flight_date <= end_date.strftime('%Y-%m-%d')
        ).order_by(DailyManifest.flight_date.desc()).all()
        
        data = []
        for manifest in manifests:
            data.append({
                'id': manifest.id,
                'flight_number': manifest.flight_number,
                'flight_date': manifest.flight_date,
                'direction': manifest.direction,
                'total_passengers': manifest.total_passengers,
                'route_breakdown': manifest.route_breakdown
            })
        
        return jsonify({'success': True, 'data': data})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@manifest_bp.route('/chart-data', methods=['GET'])
def get_chart_data():
    """Get aggregated data for charts"""
    try:
        days = int(request.args.get('days', 30))
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Query data
        manifests = DailyManifest.query.filter(
            DailyManifest.flight_date >= start_date.strftime('%Y-%m-%d'),
            DailyManifest.flight_date <= end_date.strftime('%Y-%m-%d')
        ).all()
        
        # Aggregate route breakdown
        all_origins = Counter()
        all_destinations = Counter()
        daily_totals = {}
        
        for manifest in manifests:
            if manifest.direction == 'inbound':
                for code, count in manifest.route_breakdown.items():
                    all_origins[code] += count
            else:
                for code, count in manifest.route_breakdown.items():
                    all_destinations[code] += count
            
            # Daily totals
            date_key = manifest.flight_date
            if date_key not in daily_totals:
                daily_totals[date_key] = {'inbound': 0, 'outbound': 0}
            daily_totals[date_key][manifest.direction] += manifest.total_passengers
        
        # Get top 10 origins and destinations with full names
        top_origins = []
        for code, count in all_origins.most_common(10):
            airport_info = get_airport_info(code)
            top_origins.append({
                'code': code,
                'name': airport_info['display_name'] if airport_info else code,
                'count': count
            })
        
        top_destinations = []
        for code, count in all_destinations.most_common(10):
            airport_info = get_airport_info(code)
            top_destinations.append({
                'code': code,
                'name': airport_info['display_name'] if airport_info else code,
                'count': count
            })
        
        # Format daily totals
        daily_data = []
        for date_key in sorted(daily_totals.keys()):
            daily_data.append({
                'date': date_key,
                'inbound': daily_totals[date_key]['inbound'],
                'outbound': daily_totals[date_key]['outbound']
            })
        
        return jsonify({
            'success': True,
            'data': {
                'top_origins': top_origins,
                'top_destinations': top_destinations,
                'daily_trend': daily_data
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@manifest_bp.route('/delete/<int:manifest_id>', methods=['DELETE'])
def delete_manifest(manifest_id):
    """Delete a manifest record"""
    # Check authentication
    is_admin = session.get('admin_logged_in', False)
    if not is_admin:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    try:
        manifest = DailyManifest.query.get(manifest_id)
        if not manifest:
            return jsonify({'success': False, 'error': 'Manifest not found'}), 404
        
        db.session.delete(manifest)
        db.session.commit()
        
        return jsonify({'success': True})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

