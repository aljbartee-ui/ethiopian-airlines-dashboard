from flask import Blueprint, jsonify, request, session
from werkzeug.utils import secure_filename
from src.models.sales import SalesData
from src.models.user import db
from src.routes.admin import admin_required
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import os
from datetime import datetime

sales_bp = Blueprint('sales', __name__)

# Set up matplotlib for better rendering
plt.rcParams['font.family'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'

# Define color scheme
COLORS = ['#4080FF', '#57A9FB', '#37D4CF', '#23C343', '#FBE842', '#FF9A2E', '#A9AEB8']

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'xlsx', 'xls'}

def process_excel_data(file_path):
    """Process Excel file and extract meaningful data"""
    try:
        # Read Excel file
        excel_file = pd.ExcelFile(file_path, engine='openpyxl')
        processed_data = {}
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Convert data types and clean data
            for col in df.columns:
                if df[col].dtype == 'object':
                    # Try to convert to datetime
                    if any(keyword in col.lower() for keyword in ['date', 'time']):
                        try:
                            df[col] = pd.to_datetime(df[col], errors='ignore')
                        except:
                            pass
                    # Try to convert to numeric
                    elif any(keyword in col.lower() for keyword in ['amount', 'price', 'income', 'total', 'qty', 'quantity']):
                        df[col] = pd.to_numeric(df[col], errors='ignore')
            
            # Store processed data
            processed_data[sheet_name] = {
                'columns': list(df.columns),
                'data': df.to_dict('records'),
                'dtypes': df.dtypes.astype(str).to_dict(),
                'shape': df.shape,
                'numeric_columns': df.select_dtypes(include=[np.number]).columns.tolist(),
                'categorical_columns': df.select_dtypes(include=['object']).columns.tolist(),
                'datetime_columns': df.select_dtypes(include=['datetime']).columns.tolist()
            }
        
        return processed_data
    except Exception as e:
        raise Exception(f"Error processing Excel file: {str(e)}")

def create_chart_image(data, chart_type, sheet_name, x_col=None, y_col=None, group_col=None):
    """Create a chart image and return as base64 string"""
    try:
        # Convert data back to DataFrame
        df = pd.DataFrame(data['data'])
        
        # Set up the plot
        plt.figure(figsize=(12, 8))
        plt.style.use('default')
        
        if chart_type == 'bar' and x_col and y_col:
            # Bar chart
            if group_col and group_col in df.columns:
                grouped = df.groupby(group_col)[y_col].sum().head(10)
            else:
                grouped = df.groupby(x_col)[y_col].sum().head(10)
            
            bars = plt.bar(range(len(grouped)), grouped.values, color=COLORS[:len(grouped)])
            plt.title(f'{y_col} by {group_col or x_col}', fontsize=14, fontweight='bold')
            plt.xlabel(group_col or x_col)
            plt.ylabel(y_col)
            plt.xticks(range(len(grouped)), grouped.index, rotation=45, ha='right')
            
        elif chart_type == 'line' and x_col and y_col:
            # Line chart
            df_sorted = df.sort_values(x_col)
            plt.plot(df_sorted[x_col], df_sorted[y_col], color=COLORS[0], linewidth=2, marker='o', markersize=4)
            plt.title(f'{y_col} Over {x_col}', fontsize=14, fontweight='bold')
            plt.xlabel(x_col)
            plt.ylabel(y_col)
            plt.xticks(rotation=45)
            
        elif chart_type == 'pie' and x_col:
            # Pie chart
            value_counts = df[x_col].value_counts().head(7)
            plt.pie(value_counts.values, labels=value_counts.index, colors=COLORS[:len(value_counts)], autopct='%1.1f%%')
            plt.title(f'Distribution of {x_col}', fontsize=14, fontweight='bold')
            
        elif chart_type == 'histogram' and y_col:
            # Histogram
            plt.hist(df[y_col].dropna(), bins=20, color=COLORS[1], alpha=0.7)
            plt.title(f'Distribution of {y_col}', fontsize=14, fontweight='bold')
            plt.xlabel(y_col)
            plt.ylabel('Frequency')
            
        else:
            # Default: summary statistics
            numeric_cols = data['numeric_columns']
            if numeric_cols:
                stats = df[numeric_cols].describe()
                plt.axis('tight')
                plt.axis('off')
                table = plt.table(cellText=stats.round(2).values,
                                rowLabels=stats.index,
                                colLabels=stats.columns,
                                cellLoc='center',
                                loc='center')
                table.auto_set_font_size(False)
                table.set_fontsize(10)
                plt.title(f'Summary Statistics - {sheet_name}', fontsize=14, fontweight='bold')
        
        # Add grid and styling
        if chart_type not in ['pie', 'table']:
            plt.grid(True, alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        
        # Convert to base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        
        return img_base64
        
    except Exception as e:
        plt.close()
        raise Exception(f"Error creating chart: {str(e)}")

@sales_bp.route('/upload', methods=['POST'])
@admin_required
def upload_sales_data():
    """Upload and process Excel sales data"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only Excel files (.xlsx, .xls) are allowed'}), 400
    
    try:
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_path = f'/tmp/{filename}'
        file.save(temp_path)
        
        # Process the Excel data
        processed_data = process_excel_data(temp_path)
        
        # Deactivate previous data
        SalesData.query.update({'is_active': False})
        
        # Create new sales data record
        sales_data = SalesData(
            filename=filename,
            is_active=True
        )
        sales_data.set_data(processed_data)
        
        db.session.add(sales_data)
        db.session.commit()
        
        # Clean up temp file
        os.remove(temp_path)
        
        return jsonify({
            'message': 'File uploaded and processed successfully',
            'data_id': sales_data.id,
            'filename': filename,
            'sheets': list(processed_data.keys())
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sales_bp.route('/data', methods=['GET'])
def get_current_data():
    """Get the current active sales data structure"""
    sales_data = SalesData.query.filter_by(is_active=True).first()
    
    if not sales_data:
        return jsonify({'error': 'No data available'}), 404
    
    data = sales_data.get_data()
    
    # Return structure info without full data
    structure = {}
    for sheet_name, sheet_data in data.items():
        structure[sheet_name] = {
            'columns': sheet_data['columns'],
            'shape': sheet_data['shape'],
            'numeric_columns': sheet_data['numeric_columns'],
            'categorical_columns': sheet_data['categorical_columns'],
            'datetime_columns': sheet_data['datetime_columns']
        }
    
    return jsonify({
        'filename': sales_data.filename,
        'upload_date': sales_data.upload_date.isoformat(),
        'structure': structure
    })

@sales_bp.route('/chart', methods=['POST'])
def generate_chart():
    """Generate a chart based on the current data"""
    sales_data = SalesData.query.filter_by(is_active=True).first()
    
    if not sales_data:
        return jsonify({'error': 'No data available'}), 404
    
    data = sales_data.get_data()
    
    # Get chart parameters
    chart_params = request.json
    sheet_name = chart_params.get('sheet', list(data.keys())[0])
    chart_type = chart_params.get('type', 'bar')
    x_col = chart_params.get('x_column')
    y_col = chart_params.get('y_column')
    group_col = chart_params.get('group_column')
    
    if sheet_name not in data:
        return jsonify({'error': 'Sheet not found'}), 404
    
    try:
        chart_image = create_chart_image(data[sheet_name], chart_type, sheet_name, x_col, y_col, group_col)
        
        return jsonify({
            'chart_image': chart_image,
            'chart_type': chart_type,
            'sheet_name': sheet_name
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sales_bp.route('/charts/default', methods=['GET'])
def get_default_charts():
    """Generate a set of default charts for the current data"""
    sales_data = SalesData.query.filter_by(is_active=True).first()
    
    if not sales_data:
        return jsonify({'error': 'No data available'}), 404
    
    data = sales_data.get_data()
    charts = []
    
    try:
        for sheet_name, sheet_data in data.items():
            numeric_cols = sheet_data['numeric_columns']
            categorical_cols = sheet_data['categorical_columns']
            datetime_cols = sheet_data['datetime_columns']
            
            # Chart 1: Bar chart if we have categorical and numeric data
            if categorical_cols and numeric_cols:
                chart_image = create_chart_image(sheet_data, 'bar', sheet_name, 
                                               categorical_cols[0], numeric_cols[0])
                charts.append({
                    'title': f'{numeric_cols[0]} by {categorical_cols[0]}',
                    'type': 'bar',
                    'sheet': sheet_name,
                    'image': chart_image
                })
            
            # Chart 2: Line chart if we have datetime and numeric data
            if datetime_cols and numeric_cols:
                chart_image = create_chart_image(sheet_data, 'line', sheet_name,
                                               datetime_cols[0], numeric_cols[0])
                charts.append({
                    'title': f'{numeric_cols[0]} Over Time',
                    'type': 'line',
                    'sheet': sheet_name,
                    'image': chart_image
                })
            
            # Chart 3: Pie chart for categorical distribution
            if categorical_cols:
                chart_image = create_chart_image(sheet_data, 'pie', sheet_name,
                                               categorical_cols[0])
                charts.append({
                    'title': f'Distribution of {categorical_cols[0]}',
                    'type': 'pie',
                    'sheet': sheet_name,
                    'image': chart_image
                })
            
            # Chart 4: Histogram for numeric distribution
            if numeric_cols:
                chart_image = create_chart_image(sheet_data, 'histogram', sheet_name,
                                               None, numeric_cols[0])
                charts.append({
                    'title': f'Distribution of {numeric_cols[0]}',
                    'type': 'histogram',
                    'sheet': sheet_name,
                    'image': chart_image
                })
        
        return jsonify({
            'filename': sales_data.filename,
            'charts': charts
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
