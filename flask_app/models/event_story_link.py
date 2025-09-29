# flask_app/models/event_story_link.py

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Index, CheckConstraint, ForeignKey, UniqueConstraint
from .base import db, BaseModel


class EventStoryLink(BaseModel):
    """Junction table for many-to-many relationship between events and stories"""
    __tablename__ = 'event_story_links'
    
    # Foreign keys
    event_id = db.Column(db.Integer, ForeignKey('event_claims.id'), nullable=False, index=True)
    story_id = db.Column(db.Integer, ForeignKey('stories.id'), nullable=False, index=True)
    
    # Additional fields
    note = db.Column(db.Text, nullable=True)
    
    # Relationships
    event = db.relationship('EventClaim')
    story = db.relationship('Story')
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('event_id', 'story_id', name='uk_event_story_unique'),
        Index('idx_event_story_event', 'event_id'),
        Index('idx_event_story_story', 'story_id'),
    )
    
    def __repr__(self):
        return f'<EventStoryLink {self.event_id} -> {self.story_id}>'
    
    def validate(self):
        """Validate event-story link instance"""
        errors = super().validate()
        
        # Event validation
        if not self.event_id:
            errors.append("Event ID is required")
        
        # Story validation
        if not self.story_id:
            errors.append("Story ID is required")
        
        # Check for self-reference (event and story are the same)
        if self.event_id == self.story_id:
            errors.append("Event and story cannot be the same")
        
        return errors
    
    @classmethod
    def find_by_event(cls, event_id):
        """Find all story links for an event"""
        try:
            return cls.query.filter_by(event_id=event_id).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error finding story links by event {event_id}: {str(e)}")
            return []
    
    @classmethod
    def find_by_story(cls, story_id):
        """Find all event links for a story"""
        try:
            return cls.query.filter_by(story_id=story_id).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error finding event links by story {story_id}: {str(e)}")
            return []
    
    @classmethod
    def find_by_event_and_story(cls, event_id, story_id):
        """Find specific event-story link"""
        try:
            return cls.query.filter_by(event_id=event_id, story_id=story_id).first()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error finding event-story link: {str(e)}")
            return None
    
    @classmethod
    def create_link(cls, event, story, note=None):
        """Create a link between an event and a story"""
        # Check if link already exists
        existing = cls.find_by_event_and_story(event.id, story.id)
        if existing:
            return existing, "Link already exists"
        
        # Create the link
        link = cls(
            event_id=event.id,
            story_id=story.id,
            note=note
        )
        
        if not link.is_valid():
            return None, link.validate()
        
        try:
            db.session.add(link)
            db.session.commit()
            return link, None
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error creating event-story link: {str(e)}")
            return None, str(e)
    
    @classmethod
    def remove_link(cls, event, story):
        """Remove a link between an event and a story"""
        try:
            link = cls.find_by_event_and_story(event.id, story.id)
            if link:
                db.session.delete(link)
                db.session.commit()
                return True, None
            else:
                return False, "Link does not exist"
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error removing event-story link: {str(e)}")
            return False, str(e)
    
    @classmethod
    def get_event_story_stats(cls):
        """Get statistics about event-story relationships"""
        try:
            from sqlalchemy import func
            stats = db.session.query(
                func.count(cls.id).label('total_links'),
                func.count(func.distinct(cls.event_id)).label('events_with_stories'),
                func.count(func.distinct(cls.story_id)).label('stories_with_events')
            ).first()
            
            return {
                'total_links': stats.total_links or 0,
                'events_with_stories': stats.events_with_stories or 0,
                'stories_with_events': stats.stories_with_events or 0
            }
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error getting event-story stats: {str(e)}")
            return {
                'total_links': 0,
                'events_with_stories': 0,
                'stories_with_events': 0
            }
    
    def to_dict(self, include_related=False):
        """Convert link to dictionary with optional related objects"""
        data = super().to_dict()
        
        if include_related:
            data['event'] = self.event.to_dict() if self.event else None
            data['story'] = self.story.to_dict() if self.story else None
        
        return data
