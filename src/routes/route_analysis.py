from src.models.user import db
from datetime import datetime
import json

class RouteAnalysisWeek(db.Model):
    """Model for storing weekly route analysis data"""
    __tablename__ = 'route_analysis_weeks'
    
    id = db.Column(db.Integer, primary_key=True)
    sheet_name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    
    # Outbound data (destinations from ADD)
    outbound_routes = db.Column(db.JSON)  # List of route objects
    outbound_total_routes = db.Column(db.Integer, default=0)
    outbound_total_passengers = db.Column(db.Integer, default=0)
    outbound_dates = db.Column(db.JSON)  # List of dates
    outbound_top_route_code = db.Column(db.String(10))
    outbound_top_route_name = db.Column(db.String(200))
    outbound_top_route_passengers = db.Column(db.Integer, default=0)
    outbound_busiest_day = db.Column(db.String(20))
    outbound_busiest_day_passengers = db.Column(db.Integer, default=0)
    
    # Inbound data (origins to ADD)
    inbound_routes = db.Column(db.JSON)  # List of route objects
    inbound_total_routes = db.Column(db.Integer, default=0)
    inbound_total_passengers = db.Column(db.Integer, default=0)
    inbound_dates = db.Column(db.JSON)  # List of dates
    inbound_top_route_code = db.Column(db.String(10))
    inbound_top_route_name = db.Column(db.String(200))
    inbound_top_route_passengers = db.Column(db.Integer, default=0)
    inbound_busiest_day = db.Column(db.String(20))
    inbound_busiest_day_passengers = db.Column(db.Integer, default=0)
    
    # Combined totals
    total_passengers = db.Column(db.Integer, default=0)
    total_routes = db.Column(db.Integer, default=0)
    
    # Metadata
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<RouteAnalysisWeek {self.sheet_name} - {self.total_passengers} pax>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'sheet_name': self.sheet_name,
            'total_passengers': self.total_passengers,
            'total_routes': self.total_routes,
            'outbound': {
                'routes': json.loads(self.outbound_routes) if self.outbound_routes else [],
                'total_routes': self.outbound_total_routes,
                'total_passengers': self.outbound_total_passengers,
                'dates': json.loads(self.outbound_dates) if self.outbound_dates else [],
                'top_route': {
                    'code': self.outbound_top_route_code,
                    'display_name': self.outbound_top_route_name,
                    'passengers': self.outbound_top_route_passengers
                } if self.outbound_top_route_code else None,
                'busiest_day': {
                    'date': self.outbound_busiest_day,
                    'passengers': self.outbound_busiest_day_passengers
                } if self.outbound_busiest_day else None
            },
            'inbound': {
                'routes': json.loads(self.inbound_routes) if self.inbound_routes else [],
                'total_routes': self.inbound_total_routes,
                'total_passengers': self.inbound_total_passengers,
                'dates': json.loads(self.inbound_dates) if self.inbound_dates else [],
                'top_route': {
                    'code': self.inbound_top_route_code,
                    'display_name': self.inbound_top_route_name,
                    'passengers': self.inbound_top_route_passengers
                } if self.inbound_top_route_code else None,
                'busiest_day': {
                    'date': self.inbound_busiest_day,
                    'passengers': self.inbound_busiest_day_passengers
                } if self.inbound_busiest_day else None
            },
            'upload_date': self.upload_date.isoformat() if self.upload_date else None
        }


class RouteAnalysisUpload(db.Model):
    """Model for tracking upload history"""
    __tablename__ = 'route_analysis_uploads'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    total_weeks_processed = db.Column(db.Integer, default=0)
    total_weeks_skipped = db.Column(db.Integer, default=0)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    processing_time_seconds = db.Column(db.Float)
    
    def __repr__(self):
        return f'<RouteAnalysisUpload {self.filename} - {self.total_weeks_processed} weeks>'

