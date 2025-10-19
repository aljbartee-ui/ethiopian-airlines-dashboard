from flask import Blueprint, jsonify, request, session
from src.models.sales import SalesData
from datetime import datetime
from collections import defaultdict
from sqlalchemy import func

charts_bp = Blueprint('charts', __name__)

@charts_bp.route('/charts/data/by_report', methods=['GET'])
def get_report_data():
    """Get time trend data as JSON for Chart.js"""
    try:
        view_type = request.args.get('view', 'daily')
        metric = request.args.get('metric', 'revenue')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = SalesData.query
        
        # Apply date filters
        if start_date:
            query = query.filter(SalesData.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(SalesData.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        records = query.all()
        
        if not records:
            return jsonify({'labels': [], 'data': [], 'count': 0})
        
        # Aggregate data
        aggregated = defaultdict(lambda: {'revenue': 0, 'tickets': 0})
        
        for record in records:
            if view_type == 'monthly':
                key = record.date.strftime('%Y-%m')
                label = record.date.strftime('%b %Y')
            else:  # daily
                key = record.date.strftime('%Y-%m-%d')
                label = record.date.strftime('%b %d')
            
            aggregated[key]['revenue'] += float(record.income or 0)
            aggregated[key]['tickets'] += 1
            aggregated[key]['label'] = label
        
        # Sort by key
        sorted_data = sorted(aggregated.items())
        
        labels = [item[1]['label'] for item in sorted_data]
        
        if metric == 'revenue':
            data = [round(item[1]['revenue'], 2) for item in sorted_data]
        elif metric == 'tickets':
            data = [item[1]['tickets'] for item in sorted_data]
        else:  # both
            revenue_data = [round(item[1]['revenue'], 2) for item in sorted_data]
            tickets_data = [item[1]['tickets'] for item in sorted_data]
            return jsonify({
                'labels': labels,
                'datasets': [
                    {'label': 'Revenue (KWD)', 'data': revenue_data, 'type': 'revenue'},
                    {'label': 'Tickets', 'data': tickets_data, 'type': 'tickets'}
                ],
                'count': len(records)
            })
        
        return jsonify({
            'labels': labels,
            'data': data,
            'metric': metric,
            'count': len(records)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@charts_bp.route('/charts/data/by_agent', methods=['GET'])
def get_agent_data():
    """Get sales by agent data as JSON"""
    try:
        metric = request.args.get('metric', 'revenue')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = SalesData.query
        
        if start_date:
            query = query.filter(SalesData.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(SalesData.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        records = query.all()
        
        if not records:
            return jsonify({'labels': [], 'data': []})
        
        # Aggregate by agent
        agent_data = defaultdict(lambda: {'revenue': 0, 'tickets': 0})
        
        for record in records:
            agent = record.issuing_agent or 'Unknown'
            agent_data[agent]['revenue'] += float(record.income or 0)
            agent_data[agent]['tickets'] += 1
        
        # Sort by revenue (top 10)
        if metric == 'revenue':
            sorted_agents = sorted(agent_data.items(), key=lambda x: x[1]['revenue'], reverse=True)[:10]
        else:
            sorted_agents = sorted(agent_data.items(), key=lambda x: x[1]['tickets'], reverse=True)[:10]
        
        labels = [agent for agent, _ in sorted_agents]
        
        if metric == 'revenue':
            data = [round(values['revenue'], 2) for _, values in sorted_agents]
        elif metric == 'tickets':
            data = [values['tickets'] for _, values in sorted_agents]
        else:  # both
            revenue_data = [round(values['revenue'], 2) for _, values in sorted_agents]
            tickets_data = [values['tickets'] for _, values in sorted_agents]
            return jsonify({
                'labels': labels,
                'datasets': [
                    {'label': 'Revenue (KWD)', 'data': revenue_data, 'type': 'revenue'},
                    {'label': 'Tickets', 'data': tickets_data, 'type': 'tickets'}
                ]
            })
        
        return jsonify({
            'labels': labels,
            'data': data,
            'metric': metric
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@charts_bp.route('/charts/data/by_day', methods=['GET'])
def get_day_data():
    """Get sales by day of week data as JSON"""
    try:
        metric = request.args.get('metric', 'revenue')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = SalesData.query
        
        if start_date:
            query = query.filter(SalesData.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(SalesData.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        records = query.all()
        
        if not records:
            return jsonify({'labels': [], 'data': []})
        
        # Aggregate by day of week
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_data = {day: {'revenue': 0, 'tickets': 0} for day in day_names}
        
        for record in records:
            day_name = day_names[record.date.weekday()]
            day_data[day_name]['revenue'] += float(record.income or 0)
            day_data[day_name]['tickets'] += 1
        
        labels = day_names
        
        if metric == 'revenue':
            data = [round(day_data[day]['revenue'], 2) for day in day_names]
        elif metric == 'tickets':
            data = [day_data[day]['tickets'] for day in day_names]
        else:  # both
            revenue_data = [round(day_data[day]['revenue'], 2) for day in day_names]
            tickets_data = [day_data[day]['tickets'] for day in day_names]
            return jsonify({
                'labels': labels,
                'datasets': [
                    {'label': 'Revenue (KWD)', 'data': revenue_data, 'type': 'revenue'},
                    {'label': 'Tickets', 'data': tickets_data, 'type': 'tickets'}
                ]
            })
        
        return jsonify({
            'labels': labels,
            'data': data,
            'metric': metric
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@charts_bp.route('/charts/data/by_hours', methods=['GET'])
def get_hours_data():
    """Get sales by hour data as JSON"""
    try:
        metric = request.args.get('metric', 'revenue')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = SalesData.query
        
        if start_date:
            query = query.filter(SalesData.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(SalesData.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        records = query.all()
        
        if not records:
            return jsonify({'labels': [], 'data': []})
        
        # Initialize all 24 hours
        hour_data = {f'{h:02d}:00': {'revenue': 0, 'tickets': 0} for h in range(24)}
        
        for record in records:
            # Try to extract hour from Time column (integer format like 1422 = 14:22)
            hour = None
            if record.time:
                try:
                    time_int = int(record.time)
                    hour = time_int // 100  # Extract hour from integer format
                    if 0 <= hour < 24:
                        hour_key = f'{hour:02d}:00'
                        hour_data[hour_key]['revenue'] += float(record.income or 0)
                        hour_data[hour_key]['tickets'] += 1
                except:
                    pass
            
            # Fallback to TIME 24HRS column if Time didn't work
            if hour is None and record.time_24hrs:
                try:
                    if isinstance(record.time_24hrs, str):
                        if ':' in record.time_24hrs:
                            hour = int(record.time_24hrs.split(':')[0])
                        else:
                            time_parts = record.time_24hrs.split()
                            if len(time_parts) > 1:
                                hour = int(time_parts[1].split(':')[0])
                    
                    if hour is not None and 0 <= hour < 24:
                        hour_key = f'{hour:02d}:00'
                        hour_data[hour_key]['revenue'] += float(record.income or 0)
                        hour_data[hour_key]['tickets'] += 1
                except:
                    pass
        
        # Sort by hour
        labels = [f'{h:02d}:00' for h in range(24)]
        
        if metric == 'revenue':
            data = [round(hour_data[label]['revenue'], 2) for label in labels]
        elif metric == 'tickets':
            data = [hour_data[label]['tickets'] for label in labels]
        else:  # both
            revenue_data = [round(hour_data[label]['revenue'], 2) for label in labels]
            tickets_data = [hour_data[label]['tickets'] for label in labels]
            return jsonify({
                'labels': labels,
                'datasets': [
                    {'label': 'Revenue (KWD)', 'data': revenue_data, 'type': 'revenue'},
                    {'label': 'Tickets', 'data': tickets_data, 'type': 'tickets'}
                ]
            })
        
        return jsonify({
            'labels': labels,
            'data': data,
            'metric': metric
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

