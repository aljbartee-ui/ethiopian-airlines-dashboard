from flask import Blueprint, request, jsonify, session
from src.models.user import db
from src.models.sales import SalesData, AdminUser
from werkzeug.security import generate_password_hash
import os
import json
from datetime import datetime
import base64
import io
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# Set style for charts
plt.style.use('default')
sns.set_palette(['#4080FF', '#57A9FB', '#37D4CF', '#23C343', '#FBE842', '#FF9A2E', '#A9AEB8'])

sales_bp = Blueprint('sales', __name__)

def create_admin_user():
    """Create default admin user if it doesn't exist"""
    try:
        admin = AdminUser.query.filter_by(username='admin').first()
        if not admin:
            admin = AdminUser(
                username='admin',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully")
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.session.rollback()

# Create admin user on module import
with db.session.begin():
    create_admin_user()

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
            
            # Convert date/time columns
            for col in df.columns:
                if 'date' in col.lower() or 'time' in col.lower():
                    df[col] = pd.to_datetime(df[col], errors='ignore')
            
            # Convert numeric columns
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = pd.to_numeric(df[col], errors='ignore')
            
            # Store processed data
            processed_data[sheet_name] = {
                'data': df.to_dict('records'),
                'columns': list(df.columns),
                'shape': df.shape,
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()}
            }
        
        return processed_data
    
    except Exception as e:
        raise Exception(f"Error processing Excel file: {str(e)}")

def generate_chart_base64(fig):
    """Convert matplotlib figure to base64 string"""
    img_buffer = io.BytesIO()
    fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    plt.close(fig)
    return f"data:image/png;base64,{img_base64}"

def create_charts_from_data(data):
    """Generate various charts from the processed data"""
    charts = {}
    
    try:
        # Get the first sheet's data
        sheet_name = list(data.keys())[0]
        df_data = data[sheet_name]['data']
        df = pd.DataFrame(df_data)
        
        # Chart 1: Bar Chart - Tickets by Ticket Number
        if len(df) > 0:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Find a suitable column for grouping
            categorical_cols = []
            for col in df.columns:
                if df[col].dtype == 'object' or df[col].nunique() < 20:
                    categorical_cols.append(col)
            
            if categorical_cols:
                col_to_plot = categorical_cols[0]
                value_counts = df[col_to_plot].value_counts().head(10)
                
                bars = ax.bar(range(len(value_counts)), value_counts.values)
                ax.set_xlabel('Ticket Number')
                ax.set_ylabel('Count')
                ax.set_title('Tickets by Ticket Number', fontsize=16, fontweight='bold')
                ax.set_xticks(range(len(value_counts)))
                ax.set_xticklabels(value_counts.index, rotation=45, ha='right')
                
                # Color bars with the specified palette
                colors = ['#4080FF', '#57A9FB', '#37D4CF', '#23C343', '#FBE842', '#FF9A2E', '#A9AEB8']
                for i, bar in enumerate(bars):
                    bar.set_color(colors[i % len(colors)])
                
                ax.grid(True, alpha=0.3, linestyle='--')
                plt.tight_layout()
                charts['bar_chart'] = generate_chart_base64(fig)
        
        # Chart 2: Line Chart - Tickets Over Time
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Find date columns
        date_cols = []
        for col in df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                try:
                    pd.to_datetime(df[col])
                    date_cols.append(col)
                except:
                    pass
        
        if date_cols and len(df) > 1:
            date_col = date_cols[0]
            df_temp = df.copy()
            df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors='coerce')
            df_temp = df_temp.dropna(subset=[date_col])
            
            if len(df_temp) > 0:
                df_temp = df_temp.sort_values(date_col)
                df_temp['count'] = 1
                daily_counts = df_temp.groupby(df_temp[date_col].dt.date)['count'].sum()
                
                ax.plot(daily_counts.index, daily_counts.values, marker='o', linewidth=2, color='#4080FF')
                ax.set_xlabel('Date')
                ax.set_ylabel('Tickets')
                ax.set_title('Tickets Over DATE', fontsize=16, fontweight='bold')
                ax.grid(True, alpha=0.3, linestyle='--')
                plt.xticks(rotation=45)
        else:
            # Fallback: simple line chart
            ax.plot(range(min(10, len(df))), [1] * min(10, len(df)), marker='o', linewidth=2, color='#4080FF')
            ax.set_xlabel('Index')
            ax.set_ylabel('Tickets')
            ax.set_title('Tickets Over TIME', fontsize=16, fontweight='bold')
            ax.grid(True, alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        charts['line_chart'] = generate_chart_base64(fig)
        
        # Chart 3: Pie Chart - Distribution of Ticket Numbers
        fig, ax = plt.subplots(figsize=(10, 10))
        
        if categorical_cols and len(df) > 0:
            col_to_plot = categorical_cols[0]
            value_counts = df[col_to_plot].value_counts().head(7)
            
            colors = ['#4080FF', '#57A9FB', '#37D4CF', '#23C343', '#FBE842', '#FF9A2E', '#A9AEB8']
            wedges, texts, autotexts = ax.pie(value_counts.values, labels=value_counts.index, 
                                            autopct='%1.1f%%', colors=colors, startangle=90)
            
            ax.set_title('Distribution of Ticket Number', fontsize=16, fontweight='bold')
            
            # Add value labels
            for i, (wedge, autotext) in enumerate(zip(wedges, autotexts)):
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                # Add actual values as text
                angle = (wedge.theta2 + wedge.theta1) / 2
                x = wedge.r * 0.7 * np.cos(np.radians(angle))
                y = wedge.r * 0.7 * np.sin(np.radians(angle))
                ax.text(x, y, str(value_counts.iloc[i]), ha='center', va='center', 
                       fontweight='bold', fontsize=10)
        
        plt.tight_layout()
        charts['pie_chart'] = generate_chart_base64(fig)
        
        # Chart 4: Histogram - Distribution of Tickets
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Find numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if numeric_cols and len(df) > 0:
            col_to_plot = numeric_cols[0]
            ax.hist(df[col_to_plot].dropna(), bins=20, color='#57A9FB', alpha=0.7, edgecolor='black')
            ax.set_xlabel('Values')
            ax.set_ylabel('Frequency')
            ax.set_title('Distribution of Tickets', fontsize=16, fontweight='bold')
            ax.grid(True, alpha=0.3, linestyle='--')
        else:
            # Fallback histogram
            ax.hist(range(len(df)), bins=10, color='#57A9FB', alpha=0.7, edgecolor='black')
            ax.set_xlabel('Index')
            ax.set_ylabel('Frequency')
            ax.set_title('Distribution of Tickets', fontsize=16, fontweight='bold')
            ax.grid(True, alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        charts['histogram'] = generate_chart_base64(fig)
        
    except Exception as e:
        print(f"Error generating charts: {e}")
        # Return empty charts on error
        for chart_type in ['bar_chart', 'line_chart', 'pie_chart', 'histogram']:
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.text(0.5, 0.5, f'Error generating {chart_type}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'{chart_type.replace("_", " ").title()}')
            charts[chart_type] = generate_chart_base64(fig)
    
    return charts

@sales_bp.route('/data')
def get_current_data():
    """Get information about the current active dataset"""
    try:
        active_data = SalesData.query.filter_by(is_active=True).first()
        if active_data:
            data = active_data.get_data()
            sheets = list(data.keys()) if data else ['Sheet1']
            return jsonify({
                'filename': active_data.filename,
                'upload_date': active_data.upload_date.isoformat(),
                'sheets': sheets
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
        # Save uploaded file temporarily
        upload_folder = '/tmp'
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, file.filename)
        file.save(file_path)
        
        # Process Excel data
        processed_data = process_excel_data(file_path)
        
        # Deactivate all previous data
        SalesData.query.update({'is_active': False})
        
        # Create new sales data entry
        sales_data = SalesData(
            filename=file.filename,
            is_active=True
        )
        sales_data.set_data(processed_data)
        
        db.session.add(sales_data)
        db.session.commit()
        
        # Clean up temporary file
        os.remove(file_path)
        
        return jsonify({
            'message': 'File uploaded and processed successfully',
            'filename': file.filename,
            'data_id': sales_data.id,
            'sheets': list(processed_data.keys())
        })
        
    except Exception as e:
        db.session.rollback()
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': f'Error processing Excel file: {str(e)}'}), 500

@sales_bp.route('/charts/default')
def generate_default_charts():
    """Generate default charts from the active dataset"""
    try:
        active_data = SalesData.query.filter_by(is_active=True).first()
        if not active_data:
            return jsonify({'error': 'No active dataset found'}), 404
        
        # Get processed data
        data = active_data.get_data()
        
        # Generate charts
        charts = create_charts_from_data(data)
        
        return jsonify(charts)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
