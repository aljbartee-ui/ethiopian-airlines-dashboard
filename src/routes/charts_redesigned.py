from flask import Blueprint, request, jsonify, session
from src.models.user import db
from src.models.sales import SalesData
import base64
import json
from datetime import datetime
from collections import defaultdict, Counter
import math

charts_bp = Blueprint('charts', __name__)

def create_chart_svg(title, data, chart_type='bar', width=700, height=450, data_mode='revenue'):
    """Create SVG charts without external dependencies"""
    
    if not data or len(data) == 0:
        return f"""
        <svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
            <rect width="{width}" height="{height}" fill="white" stroke="#ddd"/>
            <text x="{width//2}" y="{height//2}" text-anchor="middle" font-family="Arial" font-size="16" fill="#666">
                {title} - No Data Available
            </text>
        </svg>
        """
    
    colors = ['#4080FF', '#57A9FB', '#37D4CF', '#23C343', '#FBE842', '#FF9A2E', '#A9AEB8']
    
    if chart_type == 'bar':
        return create_bar_chart_svg(title, data, colors, width, height, data_mode)
    elif chart_type == 'line':
        return create_line_chart_svg(title, data, colors, width, height, data_mode)
    
    return f'<svg width="{width}" height="{height}"><text x="{width//2}" y="{height//2}" text-anchor="middle">Chart: {title}</text></svg>'

def create_bar_chart_svg(title, data, colors, width, height, data_mode):
    """Create bar chart SVG"""
    margin = 100
    chart_width = width - 2 * margin
    chart_height = height - 2 * margin
    
    max_val = max(data.values()) if data else 1
    num_bars = len(data)
    bar_width = min(chart_width / num_bars * 0.7, 60)
    bar_spacing = chart_width / num_bars
    
    # Format values based on data mode
    def format_value(val):
        if data_mode == 'revenue':
            return f"KWD {val:,.0f}"
        else:
            return f"{int(val)}"
    
    y_label = "Revenue (KWD)" if data_mode == 'revenue' else "Tickets Count"
    
    svg = f"""
    <svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
        <rect width="{width}" height="{height}" fill="white"/>
        <text x="{width//2}" y="30" text-anchor="middle" font-family="Arial" font-size="20" font-weight="bold" fill="#333">
            {title}
        </text>
        
        <!-- Y-axis label -->
        <text x="20" y="{height//2}" text-anchor="middle" font-family="Arial" font-size="14" fill="#666" 
              transform="rotate(-90 20 {height//2})">
            {y_label}
        </text>
        
        <!-- Grid lines -->
        <defs>
            <pattern id="grid-{id(data)}" width="50" height="50" patternUnits="userSpaceOnUse">
                <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#f5f5f5" stroke-width="1" stroke-dasharray="5,5"/>
            </pattern>
        </defs>
        <rect x="{margin}" y="{margin-40}" width="{chart_width}" height="{chart_height}" fill="url(#grid-{id(data)})"/>
        
        <!-- Y-axis -->
        <line x1="{margin}" y1="{margin-40}" x2="{margin}" y2="{height-margin}" stroke="#999" stroke-width="2"/>
        <!-- X-axis -->
        <line x1="{margin}" y1="{height-margin}" x2="{width-margin}" y2="{height-margin}" stroke="#999" stroke-width="2"/>
    """
    
    for i, (label, value) in enumerate(data.items()):
        x = margin + i * bar_spacing + (bar_spacing - bar_width) / 2
        bar_height_px = (value / max_val) * chart_height if max_val > 0 else 0
        y = height - margin - bar_height_px
        color = colors[i % len(colors)]
        
        svg += f"""
        <rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height_px}" fill="{color}" opacity="0.85" rx="4"/>
        <text x="{x + bar_width/2}" y="{height-margin+20}" text-anchor="middle" font-family="Arial" font-size="11" fill="#333">
            {str(label)[:10]}
        </text>
        <text x="{x + bar_width/2}" y="{y-8}" text-anchor="middle" font-family="Arial" font-size="11" font-weight="600" fill="#333">
            {format_value(value)}
        </text>
        """
    
    svg += "</svg>"
    return svg

def create_line_chart_svg(title, data, colors, width, height, data_mode):
    """Create line chart SVG"""
    margin = 100
    chart_width = width - 2 * margin
    chart_height = height - 2 * margin
    
    max_val = max(data.values()) if data else 1
    point_spacing = chart_width / max(len(data) - 1, 1)
    
    y_label = "Revenue (KWD)" if data_mode == 'revenue' else "Tickets Count"
    
    svg = f"""
    <svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
        <rect width="{width}" height="{height}" fill="white"/>
        <text x="{width//2}" y="30" text-anchor="middle" font-family="Arial" font-size="20" font-weight="bold" fill="#333">
            {title}
        </text>
        
        <!-- Y-axis label -->
        <text x="20" y="{height//2}" text-anchor="middle" font-family="Arial" font-size="14" fill="#666" 
              transform="rotate(-90 20 {height//2})">
            {y_label}
        </text>
        
        <!-- Grid lines -->
        <defs>
            <pattern id="grid-line-{id(data)}" width="50" height="50" patternUnits="userSpaceOnUse">
                <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#f5f5f5" stroke-width="1" stroke-dasharray="5,5"/>
            </pattern>
        </defs>
        <rect x="{margin}" y="{margin-40}" width="{chart_width}" height="{chart_height}" fill="url(#grid-line-{id(data)})"/>
        
        <!-- Axes -->
        <line x1="{margin}" y1="{margin-40}" x2="{margin}" y2="{height-margin}" stroke="#999" stroke-width="2"/>
        <line x1="{margin}" y1="{height-margin}" x2="{width-margin}" y2="{height-margin}" stroke="#999" stroke-width="2"/>
    """
    
    points = []
    for i, (label, value) in enumerate(data.items()):
        x = margin + i * point_spacing
        y = height - margin - (value / max_val) * chart_height if max_val > 0 else height - margin
        points.append(f"{x},{y}")
        
        # Add point
        svg += f'<circle cx="{x}" cy="{y}" r="5" fill="{colors[0]}" opacity="0.9"/>'
        
        # Add label
        svg += f'<text x="{x}" y="{height-margin+20}" text-anchor="middle" font-family="Arial" font-size="10" fill="#333">{str(label)[:10]}</text>'
    
    # Add line
    if len(points) > 1:
        svg += f'<polyline points="{" ".join(points)}" fill="none" stroke="{colors[0]}" stroke-width="3" opacity="0.8"/>'
    
    svg += "</svg>"
    return svg

def safe_float(value):
    """Safely convert value to float"""
    if value is None:
        return 0.0
    try:
        if isinstance(value, str):
            value = value.replace(',', '').replace('$', '').strip()
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def process_chart_data(data, chart_type, data_mode='revenue', time_mode='daily', start_date=None, end_date=None):
    """Process sales data for specific chart type"""
    try:
        sheet_name = list(data.keys())[0]
        sheet_data = data[sheet_name]['data']
        
        if not sheet_data:
            return {}
        
        # Filter by date range if provided
        filtered_data = sheet_data
        if start_date or end_date:
            filtered_data = []
            for row in sheet_data:
                date_val = row.get('DATE')
                if date_val:
                    try:
                        if isinstance(date_val, str):
                            date_str = date_val.split(' ')[0]
                        else:
                            date_str = str(date_val).split(' ')[0]
                        
                        include = True
                        if start_date and date_str < start_date:
                            include = False
                        if end_date and date_str > end_date:
                            include = False
                        
                        if include:
                            filtered_data.append(row)
                    except:
                        pass
        
        # Chart 1: By Report (Time-based - daily or monthly)
        if chart_type == 'by_report':
            time_data = defaultdict(float)
            for row in filtered_data:
                date_val = row.get('DATE')
                if date_val:
                    try:
                        if isinstance(date_val, str):
                            date_str = date_val.split(' ')[0]
                        else:
                            date_str = str(date_val).split(' ')[0]
                        
                        # Group by daily or monthly
                        if time_mode == 'monthly':
                            # Extract YYYY-MM
                            key = date_str[:7] if len(date_str) >= 7 else date_str
                        else:  # daily
                            key = date_str
                        
                        if data_mode == 'revenue':
                            value = safe_float(row.get('INCOME', 0))
                        else:  # tickets
                            value = 1
                        time_data[key] += value
                    except:
                        pass
            
            sorted_data = sorted(time_data.items(), key=lambda x: x[0])
            return dict(sorted_data)
        
        # Chart 2: By Agent
        elif chart_type == 'by_agent':
            agent_data = defaultdict(float)
            for row in filtered_data:
                agent = row.get('Issuing agent', 'Unknown')
                if data_mode == 'revenue':
                    value = safe_float(row.get('INCOME', 0))
                else:  # tickets
                    value = 1
                agent_data[agent] += value
            
            # Sort by value and get top 10
            sorted_agents = sorted(agent_data.items(), key=lambda x: x[1], reverse=True)[:10]
            return dict(sorted_agents)
        
        # Chart 3: By Days of Week
        elif chart_type == 'by_days':
            days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            days_data = defaultdict(float)
            
            for row in filtered_data:
                date_val = row.get('DATE')
                if date_val:
                    try:
                        if isinstance(date_val, str):
                            date_str = date_val.split(' ')[0]
                        else:
                            date_str = str(date_val).split(' ')[0]
                        
                        # Parse date and get day of week
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        day_name = date_obj.strftime('%A')
                        
                        if data_mode == 'revenue':
                            value = safe_float(row.get('INCOME', 0))
                        else:  # tickets
                            value = 1
                        days_data[day_name] += value
                    except:
                        pass
            
            # Return in order Mon-Sun
            ordered_data = {day: days_data.get(day, 0) for day in days_order}
            return ordered_data
        
        # Chart 4: By Hours
        elif chart_type == 'by_hours':
            hourly_data = defaultdict(float)
            for row in filtered_data:
                hour_int = None
                
                # Try column G 'Time' first (integer format like 1422, 23, 1513)
                time_val = row.get('Time')
                if time_val is not None:
                    try:
                        time_int = int(time_val)
                        # Extract hour: 1422 -> 14, 23 -> 0, 148 -> 1, 1513 -> 15
                        if time_int >= 100:
                            hour_int = time_int // 100
                        else:
                            hour_int = 0  # Values like 23, 33 are in the first hour (00:xx)
                    except (ValueError, TypeError):
                        pass
                
                # Fallback to TIME 24HRS column if Time column failed
                if hour_int is None:
                    time_24 = row.get('TIME 24HRS')
                    if time_24:
                        try:
                            # Handle datetime strings like '1900-01-01 14:22:00'
                            time_str = str(time_24)
                            if ' ' in time_str:
                                time_str = time_str.split(' ')[1]
                            
                            # Extract hour from time string
                            if ':' in time_str:
                                hour = time_str.split(':')[0]
                                hour_int = int(hour)
                        except (ValueError, AttributeError, IndexError):
                            pass
                
                # Add to hourly data if we successfully extracted an hour
                if hour_int is not None and 0 <= hour_int <= 23:
                    if data_mode == 'revenue':
                        value = safe_float(row.get('INCOME', 0))
                    else:  # tickets
                        value = 1
                    hourly_data[f"{hour_int:02d}:00"] += value
            
            # Sort by hour
            sorted_hours = sorted(hourly_data.items(), key=lambda x: x[0])
            return dict(sorted_hours)
        
        return {}
        
    except Exception as e:
        print(f"Error processing chart data: {e}")
        return {}

@charts_bp.route('/charts/generate/<chart_id>')
def generate_single_chart(chart_id):
    """Generate a single chart with specific configuration"""
    try:
        # Get parameters
        data_mode = request.args.get('data_mode', 'revenue')  # 'revenue' or 'tickets'
        time_mode = request.args.get('time_mode', 'daily')  # 'daily' or 'monthly' (for by_report only)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Get active sales data
        active_data = SalesData.query.filter_by(is_active=True).first()
        if not active_data:
            return jsonify({'error': 'No active sales data found'}), 404
        
        data = active_data.get_data()
        if not data:
            return jsonify({'error': 'No data available for chart generation'}), 404
        
        # Process data for the specific chart
        chart_data = process_chart_data(data, chart_id, data_mode, time_mode, start_date, end_date)
        
        if not chart_data:
            return jsonify({'error': 'Unable to process data for chart'}), 500
        
        # Determine chart title and type
        titles = {
            'by_report': f'Sales Report - {"Monthly" if time_mode == "monthly" else "Daily"} Trend',
            'by_agent': 'Sales by Agent',
            'by_days': 'Sales by Day of Week',
            'by_hours': 'Sales by Hour of Day'
        }
        
        chart_types = {
            'by_report': 'line',
            'by_agent': 'bar',
            'by_days': 'bar',
            'by_hours': 'bar'
        }
        
        title = titles.get(chart_id, 'Chart')
        chart_type = chart_types.get(chart_id, 'bar')
        
        # Generate SVG chart
        svg_content = create_chart_svg(title, chart_data, chart_type, data_mode=data_mode)
        
        # Convert SVG to base64
        svg_bytes = svg_content.encode('utf-8')
        svg_base64 = base64.b64encode(svg_bytes).decode('utf-8')
        
        return jsonify({
            'success': True,
            'chart': {
                'id': chart_id,
                'title': title,
                'image': svg_base64,
                'type': 'svg',
                'data_mode': data_mode,
                'time_mode': time_mode if chart_id == 'by_report' else None
            }
        })
        
    except Exception as e:
        print(f"Error generating chart: {e}")
        return jsonify({'error': f'Chart generation failed: {str(e)}'}), 500

@charts_bp.route('/charts/options')
def get_chart_options():
    """Get available chart options"""
    return jsonify({
        'charts': [
            {
                'id': 'by_report',
                'name': 'By Report (Time-based)',
                'has_time_toggle': True,
                'time_modes': ['daily', 'monthly']
            },
            {
                'id': 'by_agent',
                'name': 'By Agent',
                'has_time_toggle': False
            },
            {
                'id': 'by_days',
                'name': 'By Days of Week',
                'has_time_toggle': False
            },
            {
                'id': 'by_hours',
                'name': 'By Hours (24h)',
                'has_time_toggle': False
            }
        ]
    })




# New JSON endpoints for interactive charts (added for Chart.js support)
@charts_bp.route('/charts/data/<chart_id>')
def get_chart_data_json(chart_id):
    """Get chart data as JSON for Chart.js (keeps SVG endpoints working too)"""
    try:
        # Get parameters
        data_mode = request.args.get('data_mode', 'revenue')
        time_mode = request.args.get('time_mode', 'daily')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Get active sales data
        active_data = SalesData.query.filter_by(is_active=True).first()
        if not active_data:
            return jsonify({'error': 'No active sales data found', 'labels': [], 'data': []}), 200
        
        data = active_data.get_data()
        if not data:
            return jsonify({'error': 'No data available', 'labels': [], 'data': []}), 200
        
        # Process data for the specific chart
        chart_data = process_chart_data(data, chart_id, data_mode, time_mode, start_date, end_date)
        
        if not chart_data:
            return jsonify({'labels': [], 'data': []}), 200
        
        # Convert to Chart.js format
        labels = list(chart_data.keys())
        values = list(chart_data.values())
        
        # Calculate total for current data_mode
        total = sum(values)
        
        # Also calculate total for the other data_mode
        other_mode = 'tickets' if data_mode == 'revenue' else 'revenue'
        other_chart_data = process_chart_data(data, chart_id, other_mode, time_mode, start_date, end_date)
        other_total = sum(other_chart_data.values()) if other_chart_data else 0
        
        return jsonify({
            'success': True,
            'labels': labels,
            'data': values,
            'total': total,
            'total_revenue': total if data_mode == 'revenue' else other_total,
            'total_tickets': total if data_mode == 'tickets' else other_total,
            'data_mode': data_mode,
            'time_mode': time_mode if chart_id == 'by_report' else None,
            'chart_id': chart_id
        })
        
    except Exception as e:
        print(f"Error getting chart data: {e}")
        return jsonify({'error': str(e), 'labels': [], 'data': []}), 200

