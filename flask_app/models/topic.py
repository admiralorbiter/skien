# flask_app/models/topic.py

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Index, CheckConstraint
from .base import db, BaseModel
import re


class Topic(BaseModel):
    """Model for top-level organizational categories"""
    __tablename__ = 'topics'
    
    # Core fields
    name = db.Column(db.String(200), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    color = db.Column(db.String(7), nullable=True)  # Hex color code
    
    # Relationships
    events = db.relationship('EventClaim', backref='topic_obj', lazy='dynamic')
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_topic_name', 'name'),
        CheckConstraint('length(name) > 0', name='ck_topic_name_not_empty'),
        CheckConstraint('length(name) <= 200', name='ck_topic_name_length'),
    )
    
    def __repr__(self):
        return f'<Topic {self.id}: {self.name}>'
    
    def validate(self):
        """Validate topic instance"""
        errors = super().validate()
        
        # Name validation
        if self.name and len(self.name.strip()) == 0:
            errors.append("Topic name cannot be empty")
        
        if self.name and len(self.name) > 200:
            errors.append("Topic name is too long (max 200 characters)")
        
        # Color validation
        if self.color and not self._is_valid_hex_color(self.color):
            errors.append("Color must be a valid hex color code (e.g., #FF0000)")
        
        return errors
    
    def _is_valid_hex_color(self, color):
        """Check if color is a valid hex color code"""
        if not color:
            return True
        
        pattern = r'^#[0-9A-Fa-f]{6}$'
        return bool(re.match(pattern, color))
    
    def get_thread_count(self):
        """Get number of threads in this topic"""
        try:
            return self.threads.count()
        except Exception:
            return 0
    
    def get_event_count(self):
        """Get number of events in this topic"""
        try:
            return self.events.count()
        except Exception:
            return 0
    
    def get_unsorted_events(self):
        """Get events that don't belong to any thread"""
        try:
            return self.events.filter_by(thread_id=None).all()
        except Exception:
            return []
    
    def get_threads_by_date(self):
        """Get threads ordered by start date"""
        try:
            return self.threads.order_by(Thread.start_date.asc()).all()
        except Exception:
            return []
    
    def get_events_by_date(self):
        """Get events ordered by event date"""
        try:
            return self.events.order_by(EventClaim.event_date.asc()).all()
        except Exception:
            return []
    
    def get_events_by_importance(self):
        """Get events ordered by importance (descending)"""
        try:
            return self.events.order_by(EventClaim.importance.desc().nullslast()).all()
        except Exception:
            return []
    
    @classmethod
    def find_by_name(cls, name):
        """Find topic by name with error handling"""
        try:
            return cls.query.filter_by(name=name).first()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error finding topic by name {name}: {str(e)}")
            return None
    
    @classmethod
    def search_by_name(cls, search_term):
        """Search topics by name (case-insensitive partial match)"""
        try:
            return cls.query.filter(
                cls.name.ilike(f'%{search_term}%')
            ).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error searching topics by name {search_term}: {str(e)}")
            return []
    
    @classmethod
    def get_all_ordered(cls):
        """Get all topics ordered by name"""
        try:
            return cls.query.order_by(cls.name.asc()).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error getting all topics: {str(e)}")
            return []
    
    def to_dict(self, include_counts=False):
        """Convert topic to dictionary with optional counts"""
        data = super().to_dict()
        
        if include_counts:
            data['thread_count'] = self.get_thread_count()
            data['event_count'] = self.get_event_count()
            data['unsorted_event_count'] = len(self.get_unsorted_events())
        
        return data
