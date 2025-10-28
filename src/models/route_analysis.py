"""
Route Analysis Model
Stores route analysis data with date filtering support
"""

from src.models.user import db
from datetime import datetime
import json

class RouteAnalysis(db.Model):
    """Model for storing individual route analysis records with date support"""
    __tablename__ = 'route_analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    route_code = db.Column(db.String(10), nullable=False)
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))
    total_passengers = db.Column(db.Integer, default=0)
    previous_week = db.Column(db.Integer, default=0)
    variance = db.Column(db.Integer, default=0)
    variance_pct = db.Column(db.Float, default=0.0)
    daily_data = db.Column(db.JSON)  # Store daily passenger counts as JSON
    week_identifier = db.Column(db.String(100))  # Week/sheet name
    week_start_date = db.Column(db.String(20))  # Store week start date for filtering
    week_end_date = db.Column(db.String(20))    # Store week end date for filtering
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.String(100), default='default')
    
    def __repr__(self):
        return f'<RouteAnalysis {self.route_code} - {self.total_passengers} pax>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'route_code': self.route_code,
            'city': self.city,
            'country': self.country,
            'total_passengers': self.total_passengers,
            'previous_week': self.previous_week,
            'variance': self.variance,
            'variance_pct': self.variance_pct,
            'daily_data': self.daily_data,
            'week_identifier': self.week_identifier,
            'week_start_date': self.week_start_date,
            'week_end_date': self.week_end_date,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'session_id': self.session_id
        }
