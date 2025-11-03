from src.models.user import db
from datetime import datetime

class DailyManifest(db.Model):
    """
    Daily flight manifest with actual passenger data
    This overrides Excel forecast data when uploaded
    """
    __tablename__ = 'daily_manifests'
    
    id = db.Column(db.Integer, primary_key=True)
    flight_date = db.Column(db.Date, nullable=False, index=True)
    flight_number = db.Column(db.String(10), nullable=False)  # '620' or '621'
    direction = db.Column(db.String(20), nullable=False)  # 'inbound' or 'outbound'
    
    # Total passengers
    total_passengers = db.Column(db.Integer, nullable=False, default=0)
    business_passengers = db.Column(db.Integer, nullable=False, default=0)
    economy_passengers = db.Column(db.Integer, nullable=False, default=0)
    
    # Capacity (from aircraft configuration)
    total_capacity = db.Column(db.Integer, nullable=False, default=0)
    business_capacity = db.Column(db.Integer, nullable=False, default=0)
    economy_capacity = db.Column(db.Integer, nullable=False, default=0)
    
    # Calculated load factors
    load_factor = db.Column(db.Float, nullable=False, default=0.0)
    business_load_factor = db.Column(db.Float, nullable=False, default=0.0)
    economy_load_factor = db.Column(db.Float, nullable=False, default=0.0)
    
    # Route breakdown (JSON field storing origin/destination data)
    route_breakdown = db.Column(db.JSON, nullable=True)
    # Format: {"ADD": 45, "DXB": 23, "JED": 12, ...}
    
    # Metadata
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    uploaded_by = db.Column(db.String(100), nullable=True)
    source = db.Column(db.String(50), nullable=False, default='manifest')  # 'manifest' or 'excel_forecast'
    
    # Unique constraint: one manifest per flight per date
    __table_args__ = (
        db.UniqueConstraint('flight_date', 'flight_number', name='unique_flight_manifest'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'flight_date': self.flight_date.strftime('%Y-%m-%d'),
            'flight_number': self.flight_number,
            'direction': self.direction,
            'total_passengers': self.total_passengers,
            'business_passengers': self.business_passengers,
            'economy_passengers': self.economy_passengers,
            'total_capacity': self.total_capacity,
            'business_capacity': self.business_capacity,
            'economy_capacity': self.economy_capacity,
            'load_factor': round(self.load_factor, 2),
            'business_load_factor': round(self.business_load_factor, 2),
            'economy_load_factor': round(self.economy_load_factor, 2),
            'route_breakdown': self.route_breakdown or {},
            'uploaded_at': self.uploaded_at.strftime('%Y-%m-%d %H:%M:%S'),
            'uploaded_by': self.uploaded_by,
            'source': self.source
        }

class RouteForecast(db.Model):
    """
    Manual route forecast data entered by admin
    This is separate from manifest (actual) data
    """
    __tablename__ = 'route_forecasts'
    
    id = db.Column(db.Integer, primary_key=True)
    forecast_date = db.Column(db.Date, nullable=False, index=True)
    airport_code = db.Column(db.String(10), nullable=False)  # 'ADD', 'DXB', etc.
    direction = db.Column(db.String(20), nullable=False)  # 'inbound' or 'outbound'
    
    # Forecast passenger count
    passengers = db.Column(db.Integer, nullable=False, default=0)
    
    # Metadata
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(100), nullable=True)
    
    # Notes
    notes = db.Column(db.Text, nullable=True)
    
    # Unique constraint: one forecast per airport per date per direction
    __table_args__ = (
        db.UniqueConstraint('forecast_date', 'airport_code', 'direction', name='unique_route_forecast'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'forecast_date': self.forecast_date.strftime('%Y-%m-%d'),
            'airport_code': self.airport_code,
            'direction': self.direction,
            'passengers': self.passengers,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'created_by': self.created_by,
            'notes': self.notes
        }

class AirportMaster(db.Model):
    """
    Master list of airport codes for dropdown
    """
    __tablename__ = 'airport_master'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), nullable=False, unique=True)  # 'ADD', 'DXB', etc.
    name = db.Column(db.String(200), nullable=True)  # 'Addis Ababa', 'Dubai', etc.
    country = db.Column(db.String(100), nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'country': self.country,
            'active': self.active
        }

