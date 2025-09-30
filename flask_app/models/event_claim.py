# flask_app/models/event_claim.py

from datetime import date
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Index, CheckConstraint, ForeignKey
from .base import db, BaseModel


class EventClaim(BaseModel):
    """Model for trackable events or claims"""
    __tablename__ = 'event_claims'
    
    # Core fields
    topic_id = db.Column(db.Integer, ForeignKey('topics.id'), nullable=False, index=True)
    story_primary_id = db.Column(db.Integer, ForeignKey('stories.id'), nullable=True, index=True)
    claim_text = db.Column(db.Text, nullable=False)
    event_date = db.Column(db.Date, nullable=False, index=True)
    importance = db.Column(db.Integer, nullable=True, index=True)
    
    # Relationships
    topic = db.relationship('Topic', backref='topic_events')
    primary_story = db.relationship('Story', foreign_keys=[story_primary_id])
    
    # Edges (relationships to other events)
    outgoing_edges = db.relationship('Edge', backref='source_event_obj', 
                                   foreign_keys='Edge.src_event_id', lazy='dynamic')
    incoming_edges = db.relationship('Edge', backref='target_event_obj', 
                                   foreign_keys='Edge.dst_event_id', lazy='dynamic')
    
    # Event-story links
    event_story_links = db.relationship('EventStoryLink', backref='event_obj', lazy='dynamic', cascade='all, delete-orphan')
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_event_topic', 'topic_id'),
        Index('idx_event_date', 'event_date'),
        Index('idx_event_importance', 'importance'),
        CheckConstraint('length(claim_text) > 0', name='ck_event_claim_text_not_empty'),
        CheckConstraint('importance >= 1 AND importance <= 5', name='ck_event_importance_range'),
    )
    
    def __repr__(self):
        return f'<EventClaim {self.id}: {self.claim_text[:50]}...>'
    
    def validate(self):
        """Validate event claim instance"""
        errors = super().validate()
        
        # Claim text validation
        if self.claim_text and len(self.claim_text.strip()) == 0:
            errors.append("Claim text cannot be empty")
        
        # Date validation
        if self.event_date and self.event_date > date.today():
            errors.append("Event date cannot be in the future")
        
        # Importance validation
        if self.importance is not None and (self.importance < 1 or self.importance > 5):
            errors.append("Importance must be between 1 and 5")
        
        # Topic validation
        if not self.topic_id:
            errors.append("Event must belong to a topic")
        
        return errors
    
    def get_all_stories(self):
        """Get all stories associated with this event (primary + linked)"""
        stories = []
        
        # Add primary story if exists
        if self.primary_story:
            stories.append(self.primary_story)
        
        # Add linked stories
        for link in self.event_story_links:
            if link.story not in stories:  # Avoid duplicates
                stories.append(link.story)
        
        return stories
    
    def add_story(self, story, note=None):
        """Add a story to this event"""
        from .event_story_link import EventStoryLink
        
        # Check if relationship already exists
        existing = EventStoryLink.query.filter_by(
            event_id=self.id, 
            story_id=story.id
        ).first()
        
        if not existing:
            link = EventStoryLink(
                event_id=self.id,
                story_id=story.id,
                note=note
            )
            db.session.add(link)
    
    def remove_story(self, story):
        """Remove a story from this event"""
        from .event_story_link import EventStoryLink
        
        EventStoryLink.query.filter_by(
            event_id=self.id,
            story_id=story.id
        ).delete()
    
    def get_related_events(self, relation_type=None):
        """Get events related to this one through edges"""
        related = []
        
        # Outgoing relationships
        for edge in self.outgoing_edges:
            if relation_type is None or edge.relation == relation_type:
                related.append({
                    'event': edge.target_event,
                    'relation': edge.relation,
                    'direction': 'outgoing'
                })
        
        # Incoming relationships
        for edge in self.incoming_edges:
            if relation_type is None or edge.relation == relation_type:
                related.append({
                    'event': edge.source_event,
                    'relation': edge.relation,
                    'direction': 'incoming'
                })
        
        return related
    
    def can_connect_to(self, other_event):
        """Check if this event can be connected to another event"""
        if not other_event:
            return False, "Target event is required"
        
        if self.id == other_event.id:
            return False, "Cannot connect event to itself"
        
        if self.topic_id != other_event.topic_id:
            return False, "Events must be in the same topic to connect"
        
        return True, None
    
    @classmethod
    def find_by_topic(cls, topic_id):
        """Find events by topic"""
        try:
            return cls.query.filter_by(topic_id=topic_id).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error finding events by topic {topic_id}: {str(e)}")
            return []
    
    @classmethod
    def find_by_thread(cls, thread_id):
        """Find events by thread"""
        try:
            return cls.query.filter_by(thread_id=thread_id).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error finding events by thread {thread_id}: {str(e)}")
            return []
    
    @classmethod
    def find_by_date_range(cls, start_date, end_date):
        """Find events within date range"""
        try:
            return cls.query.filter(
                cls.event_date >= start_date,
                cls.event_date <= end_date
            ).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error finding events by date range: {str(e)}")
            return []
    
    @classmethod
    def find_by_importance(cls, importance_level):
        """Find events by importance level"""
        try:
            return cls.query.filter_by(importance=importance_level).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error finding events by importance {importance_level}: {str(e)}")
            return []
    
    @classmethod
    def find_unsorted(cls):
        """Find events that don't belong to any thread"""
        try:
            return cls.query.filter(cls.thread_id.is_(None)).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error finding unsorted events: {str(e)}")
            return []
