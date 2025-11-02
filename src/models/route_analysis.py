from src.models.user import db
from datetime import datetime
import json

class RouteAnalysisData(db.Model):
    """Model for storing route analysis data from Excel uploads (Legacy)"""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    data_json = db.Column(db.Text, nullable=False)  # Store the processed data as JSON
    is_active = db.Column(db.Boolean, default=True)  # Only one dataset should be active at a time
    
    def __repr__(self):
        return f'<RouteAnalysisData {self.filename}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'upload_date': self.upload_date.isoformat(),
            'is_active': self.is_active
        }
    
    def get_data(self):
        """Return the stored data as a Python object"""
        return json.loads(self.data_json)
    
    def set_data(self, data):
        """Store data as JSON string"""
        self.data_json = json.dumps(data, default=str)

class ManualForecast(db.Model):
    """
    Stores manual forecast data for a specific route and date.
    This is the new model for the Excel-friendly manual data feeding page.
    """
    __tablename__ = 'manual_forecasts'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Key identifiers
    travel_date = db.Column(db.Date, nullable=False, index=True)
    airport_code = db.Column(db.String(3), nullable=False) # e.g., "KWI"
    direction = db.Column(db.String(10), nullable=False) # "INBOUND" or "OUTBOUND"
    
    # Forecast data
    forecast_pax = db.Column(db.Integer, default=0)
    
    # Data source: 'manual' or 'manifest'
    data_source = db.Column(db.String(10), nullable=False, default='manual')
    
    # Metadata
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint: one forecast per airport per date per direction
    __table_args__ = (
        db.UniqueConstraint('travel_date', 'airport_code', 'direction', name='unique_manual_forecast'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'travel_date': self.travel_date.isoformat(),
            'airport_code': self.airport_code,
            'direction': self.direction,
            'forecast_pax': self.forecast_pax,
            'data_source': self.data_source,
            'last_updated': self.last_updated.isoformat()
        }
        
    def __repr__(self):
        return f'<ManualForecast {self.direction} {self.airport_code} {self.travel_date} ({self.data_source})>'
