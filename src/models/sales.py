from src.models.user import db
from datetime import datetime
import json

class SalesData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    data_json = db.Column(db.Text, nullable=False)  # Store the processed data as JSON
    is_active = db.Column(db.Boolean, default=True)  # Only one dataset should be active at a time
    
    def __repr__(self):
        return f'<SalesData {self.filename}>'
    
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

class AdminUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AdminUser {self.username}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'created_date': self.created_date.isoformat()
        }
