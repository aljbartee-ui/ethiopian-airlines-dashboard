from flask import Blueprint, request, jsonify, session
from src.models.user import db
from src.models.sales import SalesData
import base64
import json
from datetime import datetime
from collections import defaultdict, Counter
import math

charts_bp = Blueprint('charts', __name__)

def create_chart_svg(title, data, chart_type='bar', width=600, height=400, data_mode='revenue'):
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
    elif chart_type == 'pie':
        return create_pie_chart_svg(title, data, colors, width, height, data_mode)
    
    return f'<svg width="{width}" height="{height}"><text x="{width//2}" y="{height//2}" text-anchor="middle">Chart: {title}</text></svg>'

def create_bar_chart_svg(title, data, colors, width, height, data_mode):
    """Create bar chart SVG"""
    margin = 80
    chart_width = width - 2 * margin
    chart_height = height - 2 * margin
    
    max_val = max(data.values()) if data else 1
    bar_width = chart_width / len(data) * 0.8
    bar_spacing = chart_width / len(data)
    
    # Format values based on data mode
    def format_value(val):
        if data_mode == 'revenue':
            return f"${val:,.0f}"
        else:
            return f"{val:,.0f}"
    
    svg = f"""
    <svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
        <rect width="{width}" height="{height}" fill="white"/>
        <text x="{width//2}" y="30" text-anchor="middle" font-family="Arial" font-size="18" font-weight="bold" fill="#333">
            {title}
        </text>
        
        <!-- Y-axis -->
        <line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height-margin}" stroke="#ddd" stroke-width="1"/>
        <!-- X-axis -->
        <line x1="{margin}" y1="{height-margin}" x2="{width-margin}" y2="{height-margin}" stroke="#ddd" stroke-width="1"/>
    """
    
    for i, (label, value) in enumerate(list(data.items())[:10]):  # Limit to 10 bars
        x = margin + i * bar_spacing + (bar_spacing - bar_width) / 2
        bar_height = (value / max_val) * chart_height if max_val > 0 else 0
        y = height - margin - bar_height
        color = colors[i % len(colors)]
        
        svg += f"""
        <rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height}" fill="{color}" opacity="0.8"/>
        <text x="{x + bar_width/2}" y="{height-margin+15}" text-anchor="middle" font-family="Arial" font-size="10" fill="#333">
            {str(label)[:8]}
        </text>
        <text x="{x + bar_width/2}" y="{y-5}" text-anchor="middle" font-family="Arial" font-size="10" fill="#333">
            {format_value(value)}
        </text>
        """
    
    svg += "</svg>"
    return svg

def create_line_chart_svg(title, data, colors, width, height, data_mode):
    """Create line chart SVG"""
    margin = 80
    chart_width = width - 2 * margin
    chart_height = height - 2 * margin
    
    max_val = max(data.values()) if data else 1
    point_spacing = chart_width / max(len(data) - 1, 1)
    
    svg = f"""
    <svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
        <rect width="{width}" height="{height}" fill="white"/>
        <text x="{width//2}" y="30" text-anchor="middle" font-family="Arial" font-size="18" font-weight="bold" fill="#333">
            {title}
        </text>
        
        <!-- Grid lines -->
        <defs>
            <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
                <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#f0f0f0" stroke-width="1"/>
            </pattern>
        </defs>
        <rect x="{margin}" y="{margin}" width="{chart_width}" height="{chart_height}" fill="url(#grid)"/>
        
        <!-- Axes -->
        <line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height-margin}" stroke="#ddd" stroke-width="2"/>
        <line x1="{margin}" y1="{height-margin}" x2="{width-margin}" y2="{height-margin}" stroke="#ddd" stroke-width="2"/>
    """
    
    points = []
    for i, (label, value) in enumerate(data.items()):
        x = margin + i * point_spacing
        y = height - margin - (value / max_val) * chart_height if max_val > 0 else height - margin
        points.append(f"{x},{y}")
        
        # Add point
        svg += f'<circle cx="{x}" cy="{y}" r="4" fill="{colors[0]}" opacity="0.8"/>'
    
    # Add line
    if len(points) > 1:
        svg += f'<polyline points="{" ".join(points)}" fill="none" stroke="{colors[0]}" stroke-width="3" opacity="0.8"/>'
    
    svg += "</svg>"
    return svg

def create_pie_chart_svg(title, data, colors, width, height, data_mode):
    """Create pie chart SVG"""
    center_x, center_y = width // 2, height // 2 + 20
    radius = min(width, height) // 4
    
    total = sum(data.values()) if data else 1
    
    svg = f"""
    <svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
        <rect width="{width}" height="{height}" fill="white"/>
        <text x="{width//2}" y="30" text-anchor="middle" font-family="Arial" font-size="18" font-weight="bold" fill="#333">
            {title}
        </text>
    """
    
    start_angle = 0
    for i, (label, value) in enumerate(list(data.items())[:7]):  # Limit to 7 slices
        angle = (value / total) * 360
        end_angle = start_angle + angle
        
        # Convert to radians
        start_rad = start_angle * math.pi / 180
        end_rad = end_angle * math.pi / 180
        
        # Calculate arc endpoints
        x1 = center_x + radius * math.cos(start_rad)
        y1 = center_y + radius * math.sin(start_rad)
        x2 = center_x + radius * math.cos(end_rad)
        y2 = center_y + radius * math.sin(end_rad)
        
        large_arc = 1 if angle > 180 else 0
        color = colors[i % len(colors)]
        
        svg += f"""
        <path d="M {center_x} {center_y} L {x1} {y1} A {radius} {radius} 0 {large_arc} 1 {x2} {y2} Z" 
              fill="{color}" opacity="0.8" stroke="white" stroke-width="2"/>
        """
        
        # Add label
        label_angle = (start_angle + end_angle) / 2
        label_rad = label_angle * math.pi / 180
        label_x = center_x + (radius + 30) * math.cos(label_rad)
        label_y = center_y + (radius + 30) * math.sin(label_rad)
        
        percentage = value / total * 100
        svg += f"""
        <text x="{label_x}" y="{label_y}" text-anchor="middle" font-family="Arial" font-size="10" fill="#333">
            {str(label)[:6]}
        </text>
        <text x="{label_x}" y="{label_y + 12}" text-anchor="middle" font-family="Arial" font-size="9" fill="#666">
            {percentage:.1f}%
        </text>
        """
        
        start_angle = end_angle
    
    svg += "</svg>"
    return svg

def safe_float(value):
    """Safely convert value to float"""
    if value is None:
        return 0.0
    try:
        # Remove commas and convert to float
        if isinstance(value, str):
            value = value.replace(',', '').replace('$', '').strip()
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def process_sales_data_dynamic(data, data_mode='revenue', start_date=None, end_date=None):
    """Process sales data with dynamic data mode (revenue or tickets) and optional date filtering"""
    try:
        # Get the first sheet data
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
                        # Parse date
                        if isinstance(date_val, str):
                            date_str = date_val.split(' ')[0]
                        else:
                            date_str = str(date_val).split(' ')[0]
                        
                        # Check if within range
                        include = True
                        if start_date and date_str < start_date:
                            include = False
                        if end_date and date_str > end_date:
                            include = False
                        
                        if include:
                            filtered_data.append(row)
                    except:
                        pass
        
        charts = {}
        
        # Chart 1: By Agent
        agent_data = defaultdict(float)
        for row in filtered_data:
            agent = row.get('Issuing agent', 'Unknown')
            if data_mode == 'revenue':
                value = safe_float(row.get('INCOME', 0))
            else:  # tickets mode
                value = 1  # Count each row as 1 ticket
            agent_data[agent] += value
        
        # Sort and get top 10
        sorted_agents = sorted(agent_data.items(), key=lambda x: x[1], reverse=True)[:10]
        charts['by_agent'] = {
            'title': f'{"Revenue" if data_mode == "revenue" else "Tickets"} by Sales Agent',
            'data': dict(sorted_agents),
            'type': 'bar'
        }
        
        # Chart 2: Payment Method
        fop_data = defaultdict(float)
        for row in filtered_data:
            fop = row.get('FOP', 'Unknown')
            if data_mode == 'revenue':
                value = safe_float(row.get('INCOME', 0))
            else:  # tickets mode
                value = 1
            fop_data[fop] += value
        
        charts['by_payment'] = {
            'title': f'{"Revenue" if data_mode == "revenue" else "Tickets"} by Payment Method',
            'data': dict(fop_data),
            'type': 'pie'
        }
        
        # Chart 3: Hourly
        hourly_data = defaultdict(float)
        for row in filtered_data:
            time_24 = row.get('TIME 24HRS', '00:00:00')
            if isinstance(time_24, str) and ':' in time_24:
                hour = time_24.split(':')[0]
                try:
                    hour_int = int(hour)
                    if data_mode == 'revenue':
                        value = safe_float(row.get('INCOME', 0))
                    else:  # tickets mode
                        value = 1
                    hourly_data[f"{hour_int:02d}:00"] += value
                except ValueError:
                    pass
        
        # Sort by hour
        sorted_hours = sorted(hourly_data.items(), key=lambda x: x[0])
        charts['by_hour'] = {
            'title': f'{"Revenue" if data_mode == "revenue" else "Tickets"} by Hour of Day',
            'data': dict(sorted_hours),
            'type': 'bar'
        }
        
        # Chart 4: Daily
        daily_data = defaultdict(float)
        for row in filtered_data:
            date_val = row.get('DATE')
            if date_val:
                try:
                    # Handle different date formats
                    if isinstance(date_val, str):
                        date_str = date_val.split(' ')[0]  # Remove time part if present
                    else:
                        date_str = str(date_val).split(' ')[0]
                    
                    if data_mode == 'revenue':
                        value = safe_float(row.get('INCOME', 0))
                    else:  # tickets mode
                        value = 1
                    daily_data[date_str] += value
                except:
                    pass
        
        # Sort by date
        sorted_days = sorted(daily_data.items(), key=lambda x: x[0])
        charts['by_day'] = {
            'title': f'Daily {"Revenue" if data_mode == "revenue" else "Tickets"} Trend (Last 30 Days)',
            'data': dict(sorted_days),
            'type': 'line'
        }
        
        return charts
        
    except Exception as e:
        print(f"Error processing data: {e}")
        return {}

@charts_bp.route('/charts/generate')
def generate_charts():
    """Generate charts with dynamic options"""
    try:
        # Get parameters
        data_mode = request.args.get('data_mode', 'revenue')  # 'revenue' or 'tickets'
        chart_types = request.args.getlist('charts')  # List of chart types to generate
        start_date = request.args.get('start_date')  # Optional start date (YYYY-MM-DD)
        end_date = request.args.get('end_date')  # Optional end date (YYYY-MM-DD)
        
        # Default to all charts if none specified
        if not chart_types:
            chart_types = ['by_agent', 'by_payment', 'by_hour', 'by_day']
        
        # Get active sales data
        active_data = SalesData.query.filter_by(is_active=True).first()
        if not active_data:
            return jsonify({'error': 'No active sales data found'}), 404
        
        # Get processed data
        data = active_data.get_data()
        if not data:
            return jsonify({'error': 'No data available for chart generation'}), 404
        
        # Process data for charts
        chart_configs = process_sales_data_dynamic(data, data_mode, start_date, end_date)
        
        if not chart_configs:
            return jsonify({'error': 'Unable to process data for charts'}), 500
        
        # Generate only requested charts
        charts = []
        for chart_id in chart_types:
            if chart_id in chart_configs:
                config = chart_configs[chart_id]
                svg_content = create_chart_svg(
                    config['title'], 
                    config['data'], 
                    config['type'],
                    data_mode=data_mode
                )
                
                # Convert SVG to base64
                svg_bytes = svg_content.encode('utf-8')
                svg_base64 = base64.b64encode(svg_bytes).decode('utf-8')
                
                charts.append({
                    'id': chart_id,
                    'title': config['title'],
                    'image': svg_base64,
                    'type': 'svg',
                    'data_mode': data_mode
                })
        
        return jsonify({
            'success': True,
            'charts': charts,
            'total_charts': len(charts),
            'data_mode': data_mode,
            'available_charts': list(chart_configs.keys())
        })
        
    except Exception as e:
        print(f"Error generating charts: {e}")
        return jsonify({'error': f'Chart generation failed: {str(e)}'}), 500

@charts_bp.route('/charts/options')
def get_chart_options():
    """Get available chart options"""
    return jsonify({
        'data_modes': [
            {'id': 'revenue', 'name': 'Revenue ($)', 'description': 'Show dollar amounts'},
            {'id': 'tickets', 'name': 'Tickets Count', 'description': 'Show number of transactions'}
        ],
        'chart_types': [
            {'id': 'by_agent', 'name': 'By Sales Agent', 'type': 'bar'},
            {'id': 'by_payment', 'name': 'By Payment Method', 'type': 'pie'},
            {'id': 'by_hour', 'name': 'By Hour of Day', 'type': 'bar'},
            {'id': 'by_day', 'name': 'Daily Trend', 'type': 'line'}
        ]
    })

@charts_bp.route('/charts/data')
def get_chart_data():
    """Get raw chart data for debugging"""
    try:
        data_mode = request.args.get('data_mode', 'revenue')
        
        active_data = SalesData.query.filter_by(is_active=True).first()
        if not active_data:
            return jsonify({'error': 'No active sales data found'}), 404
        
        data = active_data.get_data()
        chart_configs = process_sales_data_dynamic(data, data_mode)
        
        return jsonify({
            'success': True,
            'chart_configs': chart_configs,
            'data_mode': data_mode,
            'data_shape': {sheet: len(sheet_data['data']) for sheet, sheet_data in data.items()}
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
