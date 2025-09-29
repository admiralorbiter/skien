# flask_app/models/thread.py

from datetime import date
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Index, CheckConstraint, ForeignKey
from .base import db, BaseModel


class Thread(BaseModel):
    """Model for chronological sequences within topics"""
    __tablename__ = 'threads'
    
    # Core fields
    topic_id = db.Column(db.Integer, ForeignKey('topics.id'), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=True, index=True)
    
    # Relationships
    topic = db.relationship('Topic')
    events = db.relationship('EventClaim', backref='thread_obj', lazy='dynamic')
    
    # Many-to-many relationship with stories
    stories = db.relationship('Story', secondary='thread_stories', backref='threads', lazy='dynamic')
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_thread_topic', 'topic_id'),
        Index('idx_thread_start_date', 'start_date'),
        CheckConstraint('length(name) > 0', name='ck_thread_name_not_empty'),
        CheckConstraint('length(name) <= 200', name='ck_thread_name_length'),
    )
    
    def add_event(self, event):
        """Add an event to this thread"""
        try:
            event.thread_id = self.id
            event.save()
            return True, None
        except Exception as e:
            return False, str(e)
    
    @classmethod
    def find_by_topic(cls, topic_id):
        """Find all threads for a given topic"""
        return cls.query.filter_by(topic_id=topic_id).all()
    
    def __repr__(self):
        return f'<Thread {self.id}: {self.name}>'
    
    def validate(self):
        """Validate thread instance"""
        errors = super().validate()
        
        # Name validation
        if self.name and len(self.name.strip()) == 0:
            errors.append("Thread name cannot be empty")
        
        if self.name and len(self.name) > 200:
            errors.append("Thread name is too long (max 200 characters)")
        
        # Date validation
        if self.start_date and self.start_date > date.today():
            errors.append("Start date cannot be in the future")
        
        # Topic validation
        if not self.topic_id:
            errors.append("Thread must belong to a topic")
        
        return errors
    
    def get_event_count(self):
        """Get number of events in this thread"""
        try:
            return self.events.count()
        except Exception:
            return 0
    
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
    
    def get_first_event_date(self):
        """Get the date of the first event in this thread"""
        try:
            first_event = self.events.order_by(EventClaim.event_date.asc()).first()
            return first_event.event_date if first_event else None
        except Exception:
            return None
    
    def get_last_event_date(self):
        """Get the date of the last event in this thread"""
        try:
            last_event = self.events.order_by(EventClaim.event_date.desc()).first()
            return last_event.event_date if last_event else None
        except Exception:
            return None
    
    def update_start_date_from_events(self):
        """Update start_date based on the earliest event in the thread"""
        first_date = self.get_first_event_date()
        if first_date:
            self.start_date = first_date
            return True
        return False
    
    def get_date_range(self):
        """Get the date range of events in this thread"""
        first_date = self.get_first_event_date()
        last_date = self.get_last_event_date()
        return first_date, last_date
    
    def get_events_in_date_range(self, start_date, end_date):
        """Get events within a specific date range"""
        try:
            return self.events.filter(
                EventClaim.event_date >= start_date,
                EventClaim.event_date <= end_date
            ).order_by(EventClaim.event_date.asc()).all()
        except Exception:
            return []
    
    def add_event(self, event):
        """Add an event to this thread"""
        if event.topic_id != self.topic_id:
            return False, "Event must be in the same topic as the thread"
        
        event.thread_id = self.id
        return True, None
    
    def remove_event(self, event):
        """Remove an event from this thread"""
        if event.thread_id == self.id:
            event.thread_id = None
            return True, None
        return False, "Event is not in this thread"
    
    def move_event_to_thread(self, event, new_thread):
        """Move an event from this thread to another thread"""
        if event.thread_id != self.id:
            return False, "Event is not in this thread"
        
        if new_thread.topic_id != self.topic_id:
            return False, "New thread must be in the same topic"
        
        event.thread_id = new_thread.id
        return True, None
    
    @classmethod
    def find_by_topic(cls, topic_id):
        """Find threads by topic"""
        try:
            return cls.query.filter_by(topic_id=topic_id).order_by(cls.start_date.asc()).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error finding threads by topic {topic_id}: {str(e)}")
            return []
    
    @classmethod
    def find_by_name(cls, name, topic_id=None):
        """Find thread by name, optionally within a topic"""
        try:
            query = cls.query.filter_by(name=name)
            if topic_id:
                query = query.filter_by(topic_id=topic_id)
            return query.first()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error finding thread by name {name}: {str(e)}")
            return None
    
    @classmethod
    def search_by_name(cls, search_term, topic_id=None):
        """Search threads by name (case-insensitive partial match)"""
        try:
            query = cls.query.filter(cls.name.ilike(f'%{search_term}%'))
            if topic_id:
                query = query.filter_by(topic_id=topic_id)
            return query.order_by(cls.start_date.asc()).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error searching threads by name {search_term}: {str(e)}")
            return []
    
    @classmethod
    def find_unsorted_threads(cls, topic_id=None):
        """Find threads without start dates"""
        try:
            query = cls.query.filter(cls.start_date.is_(None))
            if topic_id:
                query = query.filter_by(topic_id=topic_id)
            return query.order_by(cls.name.asc()).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error finding unsorted threads: {str(e)}")
            return []
    
    def to_dict(self, include_counts=False, include_dates=False):
        """Convert thread to dictionary with optional metadata"""
        data = super().to_dict()
        
        if include_counts:
            data['event_count'] = self.get_event_count()
        
        if include_dates:
            first_date, last_date = self.get_date_range()
            data['first_event_date'] = first_date.isoformat() if first_date else None
            data['last_event_date'] = last_date.isoformat() if last_date else None
        
        return data
    
    def get_stories(self):
        """Get all stories associated with this thread"""
        try:
            return list(self.stories)
        except Exception as e:
            current_app.logger.error(f"Error getting stories for thread {self.id}: {str(e)}")
            return []
    
    def add_story(self, story):
        """Add a story to this thread"""
        try:
            from .thread_story import thread_stories_table

            # Check if relationship already exists
            existing = db.session.execute(
                db.select(thread_stories_table).where(
                    (thread_stories_table.c.thread_id == self.id) & 
                    (thread_stories_table.c.story_id == story.id)
                )
            ).first()
            if existing:
                return True, "Story already associated with this thread"

            # Create new relationship
            db.session.execute(
                thread_stories_table.insert().values(
                    thread_id=self.id,
                    story_id=story.id
                )
            )
            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding story {story.id} to thread {self.id}: {str(e)}")
            return False, str(e)

    def remove_story(self, story):
        """Remove a story from this thread"""
        try:
            from .thread_story import thread_stories_table

            # Find and delete the relationship
            result = db.session.execute(
                thread_stories_table.delete().where(
                    (thread_stories_table.c.thread_id == self.id) & 
                    (thread_stories_table.c.story_id == story.id)
                )
            )
            db.session.commit()
            if result.rowcount > 0:
                return True, None
            return True, "Story not associated with this thread"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error removing story {story.id} from thread {self.id}: {str(e)}")
            return False, str(e)

    def set_stories(self, story_ids):
        """Set stories for this thread (replaces existing stories)"""
        try:
            from .story import Story
            from .thread_story import thread_stories_table

            # Remove existing story relationships
            db.session.execute(
                thread_stories_table.delete().where(
                    thread_stories_table.c.thread_id == self.id
                )
            )

            # Add new stories
            for story_id in story_ids:
                story = Story.query.get(story_id)
                if story:
                    # Create new thread-story relationship
                    db.session.execute(
                        thread_stories_table.insert().values(
                            thread_id=self.id,
                            story_id=story.id
                        )
                    )

            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error setting stories for thread {self.id}: {str(e)}")
            return False, str(e)
    
    def get_story_count(self):
        """Get number of stories in this thread"""
        try:
            return self.stories.count()
        except Exception:
            return 0
