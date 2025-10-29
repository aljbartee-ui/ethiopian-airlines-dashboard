from src.models.user import db
from datetime import datetime
import json

class RouteAnalysisData(db.Model):
    """Model for storing route analysis data from Excel uploads"""
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

