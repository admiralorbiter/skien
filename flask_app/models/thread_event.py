# flask_app/models/thread_event.py

from .base import db
from sqlalchemy import ForeignKey, UniqueConstraint, Table
from datetime import datetime

# Define the table separately
thread_events_table = Table(
    'thread_events',
    db.metadata,
    db.Column('thread_id', db.Integer, ForeignKey('threads.id', ondelete='CASCADE'), primary_key=True),
    db.Column('event_id', db.Integer, ForeignKey('event_claims.id', ondelete='CASCADE'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow, nullable=False),
    db.Column('updated_at', db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False),
    UniqueConstraint('thread_id', 'event_id', name='_thread_event_uc')
)

class ThreadEvent:
    """Junction table for many-to-many relationship between Thread and Event"""
    __table__ = thread_events_table

    def __repr__(self):
        return f'<ThreadEvent Thread_ID: {self.thread_id} Event_ID: {self.event_id}>'
