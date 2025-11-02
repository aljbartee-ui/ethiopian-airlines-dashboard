from flask import Blueprint, render_template, request, jsonify, session
from src.models.user import db
from src.models.sales import SalesData
from datetime import datetime
import openpyxl
from io import BytesIO

sales_bp = Blueprint('sales_working', __name__)

def admin_required(f):
    """Decorator to require admin authentication"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({'success': False, 'error': 'Admin authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@sales_bp.route('/dashboard')
def dashboard():
    """Sales dashboard page"""
    return render_template('sales_dashboard.html')

@sales_bp.route('/api/sales/login', methods=['POST'])
def admin_login():
    """Admin login endpoint"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Simple admin check (in production, use proper authentication)
    if username == 'al.jbartee@gmail.com' and password == 'B1m2a3i4!':
        session['admin_logged_in'] = True
        session['admin_username'] = username
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

@sales_bp.route('/api/sales/logout', methods=['POST'])
def admin_logout():
    """Admin logout endpoint"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return jsonify({'success': True})

@sales_bp.route('/api/sales/check-auth')
def check_auth():
    """Check if admin is logged in"""
    return jsonify({
        'authenticated': session.get('admin_logged_in', False),
        'username': session.get('admin_username')
    })

@sales_bp.route('/api/sales/upload', methods=['POST'])
@admin_required
def upload_sales():
    """Upload sales data - ADMIN ONLY"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    try:
        # Read file content
        file_content = file.read()
        workbook = openpyxl.load_workbook(BytesIO(file_content), data_only=True)
        sheet = workbook.active
        
        records_added = 0
        
        # Process Excel data (starting from row 2, assuming row 1 is headers)
        for row_idx in range(2, sheet.max_row + 1):
            date_val = sheet.cell(row_idx, 1).value
            revenue = sheet.cell(row_idx, 2).value
            passengers = sheet.cell(row_idx, 3).value
            
            if date_val and revenue is not None:
                # Convert date if needed
                if isinstance(date_val, datetime):
                    sale_date = date_val.date()
                else:
                    sale_date = datetime.strptime(str(date_val), '%Y-%m-%d').date()
                
                # Check if record exists
                existing = SalesData.query.filter_by(sale_date=sale_date).first()
                if existing:
                    existing.revenue = float(revenue)
                    existing.passengers = int(passengers) if passengers else 0
                else:
                    new_record = SalesData(
                        sale_date=sale_date,
                        revenue=float(revenue),
                        passengers=int(passengers) if passengers else 0
                    )
                    db.session.add(new_record)
                records_added += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully processed {records_added} records'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@sales_bp.route('/api/sales/data')
@admin_required
def get_sales_data():
    """Get sales data - ADMIN ONLY (FIXED: Added authentication)"""
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    query = SalesData.query
    
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        query = query.filter(SalesData.sale_date >= start_date)
    
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        query = query.filter(SalesData.sale_date <= end_date)
    
    records = query.order_by(SalesData.sale_date).all()
    
    return jsonify({
        'success': True,
        'data': [r.to_dict() for r in records],
        'total_revenue': sum(r.revenue for r in records),
        'total_passengers': sum(r.passengers for r in records),
        'record_count': len(records)
    })

