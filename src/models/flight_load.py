from src.models.user import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class FlightLoadRecord(db.Model):
    """
    Stores a single flight's load data, which can be a forecast from Excel 
    or an actual load from a manifest.
    """
    __tablename__ = 'flight_load_records'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Key identifiers
    travel_date = db.Column(db.Date, nullable=False, index=True)
    flight_no = db.Column(db.String(10), nullable=False) # e.g., "620" or "621"
    
    # Data Source: 'forecast' (from Excel) or 'manifest' (from actual upload)
    data_source = db.Column(db.String(10), nullable=False, default='forecast')
    
    # Data fields (from Excel columns)
    day = db.Column(db.String(10))
    c_cap = db.Column(db.Integer, default=0)
    y_cap = db.Column(db.Integer, default=0)
    tot_cap = db.Column(db.Integer, default=0)
    pax_c = db.Column(db.Integer, default=0)
    pax_y = db.Column(db.Integer, default=0)
    pax = db.Column(db.Integer, default=0)
    lf_c = db.Column(db.Float, default=0.0)
    lf_y = db.Column(db.Float, default=0.0)
    lf = db.Column(db.Float, default=0.0)
    
    # Metadata
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint: one record per flight per date
    __table_args__ = (
        db.UniqueConstraint('travel_date', 'flight_no', name='unique_flight_load'),
    )
    
    def update_from_dict(self, data):
        """Update model fields from a dictionary"""
        self.day = data.get('day', self.day)
        self.c_cap = data.get('c_cap', self.c_cap)
        self.y_cap = data.get('y_cap', self.y_cap)
        self.tot_cap = data.get('tot_cap', self.tot_cap)
        self.pax_c = data.get('pax_c', self.pax_c)
        self.pax_y = data.get('pax_y', self.pax_y)
        self.pax = data.get('pax', self.pax)
        self.lf_c = data.get('lf_c', self.lf_c)
        self.lf_y = data.get('lf_y', self.lf_y)
        self.lf = data.get('lf', self.lf)
        self.upload_date = datetime.utcnow()
        
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'travel_date': self.travel_date.isoformat(),
            'flight_no': self.flight_no,
            'data_source': self.data_source,
            'day': self.day,
            'c_cap': self.c_cap,
            'y_cap': self.y_cap,
            'tot_cap': self.tot_cap,
            'pax_c': self.pax_c,
            'pax_y': self.pax_y,
            'pax': self.pax,
            'lf_c': self.lf_c,
            'lf_y': self.lf_y,
            'lf': self.lf,
            'upload_date': self.upload_date.isoformat()
        }
        
    def __repr__(self):
        return f'<FlightLoadRecord {self.flight_no} {self.travel_date} ({self.data_source})>'
