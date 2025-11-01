"""
Daily Manifest Database Models
Stores compact summaries of flight manifests for long-term analytics
"""

from src.models.sales import db
from datetime import datetime
import json

class DailyManifest(db.Model):
    """
    Stores daily manifest summary data
    Compact storage: ~500 bytes per day
    """
    __tablename__ = 'daily_manifests'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Flight Information
    flight_number = db.Column(db.String(10), nullable=False)  # e.g., "ET 620"
    flight_date = db.Column(db.Date, nullable=False, index=True)
    direction = db.Column(db.String(10), nullable=False)  # "INBOUND" or "OUTBOUND"
    
    # Route Information
    origin = db.Column(db.String(3), nullable=False)  # e.g., "ADD"
    destination = db.Column(db.String(3), nullable=False)  # e.g., "KWI"
    
    # Passenger Counts
    total_passengers = db.Column(db.Integer, default=0)
    c_class_passengers = db.Column(db.Integer, default=0)
    y_class_passengers = db.Column(db.Integer, default=0)
    
    # Demographics (optional)
    male_count = db.Column(db.Integer, default=0)
    female_count = db.Column(db.Integer, default=0)
    child_count = db.Column(db.Integer, default=0)
    infant_count = db.Column(db.Integer, default=0)
    
    # Baggage
    total_bags = db.Column(db.Integer, default=0)
    total_weight = db.Column(db.Integer, default=0)
    
    # Origin/Destination Breakdown (JSON - compact storage)
    # For inbound: {"ACC": 34, "LOS": 9, "ABV": 9, ...}
    # For outbound: {"ACC": 25, "LOS": 12, "ABV": 8, ...}
    route_breakdown = db.Column(db.Text, nullable=True)
    
    # Metadata
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.String(100), default='admin')
    
    # Unique constraint: one manifest per flight per date per direction
    __table_args__ = (
        db.UniqueConstraint('flight_number', 'flight_date', 'direction', name='unique_manifest'),
    )
    
    def set_route_breakdown(self, breakdown_dict):
        """Store route breakdown as JSON"""
        self.route_breakdown = json.dumps(breakdown_dict)
    
    def get_route_breakdown(self):
        """Retrieve route breakdown as dictionary"""
        if self.route_breakdown:
            return json.loads(self.route_breakdown)
        return {}
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'flight_number': self.flight_number,
            'flight_date': self.flight_date.isoformat() if self.flight_date else None,
            'direction': self.direction,
            'origin': self.origin,
            'destination': self.destination,
            'total_passengers': self.total_passengers,
            'c_class_passengers': self.c_class_passengers,
            'y_class_passengers': self.y_class_passengers,
            'male_count': self.male_count,
            'female_count': self.female_count,
            'child_count': self.child_count,
            'infant_count': self.infant_count,
            'total_bags': self.total_bags,
            'total_weight': self.total_weight,
            'route_breakdown': self.get_route_breakdown(),
            'upload_date': self.upload_date.isoformat() if self.upload_date else None
        }
    
    def __repr__(self):
        return f'<DailyManifest {self.flight_number} {self.flight_date} {self.direction}>'
