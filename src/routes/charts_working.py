from flask import Blueprint, request, jsonify, session
from src.models.user import db
from src.models.sales import SalesData
import pandas as pd
import base64
import io
import json
from datetime import datetime

charts_bp = Blueprint('charts', __name__)

def create_simple_chart_svg(title, data, chart_type='bar'):
    """Create simple SVG charts that work without matplotlib"""
    
    if not data or len(data) == 0:
        return f"""
        <svg width="600" height="400" xmlns="http://www.w3.org/2000/svg">
            <rect width="600" height="400" fill="white" stroke="#ddd"/>
            <text x="300" y="200" text-anchor="middle" font-family="Arial" font-size="16" fill="#666">
                {title} - No Data Available
            </text>
        </svg>
        """
    
    colors = ['#4080FF', '#57A9FB', '#37D4CF', '#23C343', '#FBE842', '#FF9A2E', '#A9AEB8']
    
    if chart_type == 'bar':
        # Create bar chart SVG
        max_val = max(data.values()) if data else 1
        bar_width = 500 / len(data)
        
        svg = f"""
        <svg width="600" height="400" xmlns="http://www.w3.org/2000/svg">
            <rect width="600" height="400" fill="white"/>
            <text x="300" y="30" text-anchor="middle" font-family="Arial" font-size="18" font-weight="bold" fill="#333">
                {title}
            </text>
        """
        
        for i, (label, value) in enumerate(data.items()):
            if i >= 10:  # Limit to 10 bars
                break
            x = 50 + i * bar_width
            height = (value / max_val) * 300 if max_val > 0 else 0
            y = 350 - height
            color = colors[i % len(colors)]
            
            svg += f"""
            <rect x="{x}" y="{y}" width="{bar_width-5}" height="{height}" fill="{color}" opacity="0.8"/>
            <text x="{x + bar_width/2}" y="370" text-anchor="middle" font-family="Arial" font-size="10" fill="#333">
                {label[:8]}
            </text>
            <text x="{x + bar_width/2}" y="{y-5}" text-anchor="middle" font-family="Arial" font-size="10" fill="#333">
                ${value:,.0f}
            </text>
            """
        
        svg += "</svg>"
        return svg
    
    elif chart_type == 'line':
        # Create line chart SVG
        max_val = max(data.values()) if data else 1
        point_width = 500 / max(len(data)-1, 1)
        
        svg = f"""
        <svg width="600" height="400" xmlns="http://www.w3.org/2000/svg">
            <rect width="600" height="400" fill="white"/>
            <text x="300" y="30" text-anchor="middle" font-family="Arial" font-size="18" font-weight="bold" fill="#333">
                {title}
            </text>
        """
        
        points = []
        for i, (label, value) in enumerate(data.items()):
            x = 50 + i * point_width
            y = 350 - (value / max_val) * 300 if max_val > 0 else 350
            points.append(f"{x},{y}")
            
            # Add point
            svg += f'<circle cx="{x}" cy="{y}" r="4" fill="{colors[0]}" opacity="0.8"/>'
        
        # Add line
        if len(points) > 1:
            svg += f'<polyline points="{" ".join(points)}" fill="none" stroke="{colors[0]}" stroke-width="2" opacity="0.8"/>'
        
        svg += "</svg>"
        return svg
    
    elif chart_type == 'pie':
        # Create pie chart SVG
        total = sum(data.values()) if data else 1
        center_x, center_y, radius = 300, 200, 100
        
        svg = f"""
        <svg width="600" height="400" xmlns="http://www.w3.org/2000/svg">
            <rect width="600" height="400" fill="white"/>
            <text x="300" y="30" text-anchor="middle" font-family="Arial" font-size="18" font-weight="bold" fill="#333">
                {title}
            </text>
        """
        
        start_angle = 0
        for i, (label, value) in enumerate(data.items()):
            if i >= 7:  # Limit to 7 slices
                break
            
            angle = (value / total) * 360
            end_angle = start_angle + angle
            
            # Calculate arc path
            start_x = center_x + radius * (start_angle * 3.14159 / 180).__cos__()
            start_y = center_y + radius * (start_angle * 3.14159 / 180).__sin__()
            end_x = center_x + radius * (end_angle * 3.14159 / 180).__cos__()
            end_y = center_y + radius * (end_angle * 3.14159 / 180).__sin__()
            
            large_arc = 1 if angle > 180 else 0
            color = colors[i % len(colors)]
            
            svg += f"""
            <path d="M {center_x} {center_y} L {start_x} {start_y} A {radius} {radius} 0 {large_arc} 1 {end_x} {end_y} Z" 
                  fill="{color}" opacity="0.8" stroke="white" stroke-width="2"/>
            """
            
            # Add label
            label_angle = (start_angle + end_angle) / 2
            label_x = center_x + (radius + 20) * (label_angle * 3.14159 / 180).__cos__()
            label_y = center_y + (radius + 20) * (label_angle * 3.14159 / 180).__sin__()
            
            svg += f"""
            <text x="{label_x}" y="{label_y}" text-anchor="middle" font-family="Arial" font-size="10" fill="#333">
                {label} ({value/total*100:.1f}%)
            </text>
            """
            
            start_angle = end_angle
        
        svg += "</svg>"
        return svg
    
    return f'<svg width="600" height="400"><text x="300" y="200" text-anchor="middle">Chart: {title}</text></svg>'

def process_sales_data_for_charts(data):
    """Process sales data and return chart data"""
    try:
        # Get the first sheet data
        sheet_name = list(data.keys())[0]
        df_data = data[sheet_name]['data']
        df = pd.DataFrame(df_data)
        
        charts = {}
        
        # Chart 1: Revenue by Agent (Top 10)
        if 'Issuing agent' in df.columns and 'INCOME' in df.columns:
            # Clean income data
            df['INCOME_CLEAN'] = pd.to_numeric(df['INCOME'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            agent_revenue = df.groupby('Issuing agent')['INCOME_CLEAN'].sum().sort_values(ascending=False).head(10)
            charts['revenue_by_agent'] = {
                'title': 'Revenue by Sales Agent',
                'data': agent_revenue.to_dict(),
                'type': 'bar'
            }
        
        # Chart 2: Daily Revenue Trend
        if 'DATE' in df.columns and 'INCOME_CLEAN' in df.columns:
            df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
            daily_revenue = df.groupby(df['DATE'].dt.date)['INCOME_CLEAN'].sum().tail(30)  # Last 30 days
            charts['daily_revenue'] = {
                'title': 'Daily Revenue Trend (Last 30 Days)',
                'data': {str(k): v for k, v in daily_revenue.to_dict().items()},
                'type': 'line'
            }
        
        # Chart 3: Payment Method Distribution
        if 'FOP' in df.columns and 'INCOME_CLEAN' in df.columns:
            fop_revenue = df.groupby('FOP')['INCOME_CLEAN'].sum()
            charts['payment_methods'] = {
                'title': 'Revenue by Payment Method',
                'data': fop_revenue.to_dict(),
                'type': 'pie'
            }
        
        # Chart 4: Hourly Sales
        if 'TIME 24HRS' in df.columns and 'INCOME_CLEAN' in df.columns:
            df['Hour'] = df['TIME 24HRS'].astype(str).str.split(':').str[0]
            df['Hour'] = pd.to_numeric(df['Hour'], errors='coerce').fillna(0).astype(int)
            hourly_revenue = df.groupby('Hour')['INCOME_CLEAN'].sum()
            charts['hourly_sales'] = {
                'title': 'Sales by Hour of Day',
                'data': {f"{k}:00": v for k, v in hourly_revenue.to_dict().items()},
                'type': 'bar'
            }
        
        return charts
        
    except Exception as e:
        print(f"Error processing data: {e}")
        return {}

@charts_bp.route('/charts/generate')
def generate_charts():
    """Generate charts from active sales data"""
    try:
        # Get active sales data
        active_data = SalesData.query.filter_by(is_active=True).first()
        if not active_data:
            return jsonify({'error': 'No active sales data found'}), 404
        
        # Get processed data
        data = active_data.get_data()
        if not data:
            return jsonify({'error': 'No data available for chart generation'}), 404
        
        # Process data for charts
        chart_configs = process_sales_data_for_charts(data)
        
        if not chart_configs:
            return jsonify({'error': 'Unable to process data for charts'}), 500
        
        # Generate SVG charts
        charts = []
        for chart_id, config in chart_configs.items():
            svg_content = create_simple_chart_svg(
                config['title'], 
                config['data'], 
                config['type']
            )
            
            # Convert SVG to base64
            svg_bytes = svg_content.encode('utf-8')
            svg_base64 = base64.b64encode(svg_bytes).decode('utf-8')
            
            charts.append({
                'id': chart_id,
                'title': config['title'],
                'image': svg_base64,
                'type': 'svg'
            })
        
        return jsonify({
            'success': True,
            'charts': charts,
            'total_charts': len(charts)
        })
        
    except Exception as e:
        print(f"Error generating charts: {e}")
        return jsonify({'error': f'Chart generation failed: {str(e)}'}), 500

@charts_bp.route('/charts/data')
def get_chart_data():
    """Get raw chart data for debugging"""
    try:
        active_data = SalesData.query.filter_by(is_active=True).first()
        if not active_data:
            return jsonify({'error': 'No active sales data found'}), 404
        
        data = active_data.get_data()
        chart_configs = process_sales_data_for_charts(data)
        
        return jsonify({
            'success': True,
            'chart_configs': chart_configs,
            'data_shape': {sheet: len(sheet_data['data']) for sheet, sheet_data in data.items()}
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
