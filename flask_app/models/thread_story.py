# flask_app/models/thread_story.py

from .base import db
from sqlalchemy import ForeignKey, UniqueConstraint, Table
from datetime import datetime

# Define the table separately
thread_stories_table = Table(
    'thread_stories',
    db.metadata,
    db.Column('thread_id', db.Integer, ForeignKey('threads.id', ondelete='CASCADE'), primary_key=True),
    db.Column('story_id', db.Integer, ForeignKey('stories.id', ondelete='CASCADE'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow, nullable=False),
    db.Column('updated_at', db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False),
    UniqueConstraint('thread_id', 'story_id', name='_thread_story_uc')
)

class ThreadStory:
    """Junction table for many-to-many relationship between Thread and Story"""
    __table__ = thread_stories_table

    def __repr__(self):
        return f'<ThreadStory Thread_ID: {self.thread_id} Story_ID: {self.story_id}>'
