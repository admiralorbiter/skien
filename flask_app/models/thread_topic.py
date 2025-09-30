# flask_app/models/thread_topic.py

from .base import db
from sqlalchemy import ForeignKey, UniqueConstraint, Table
from datetime import datetime

# Define the table separately
thread_topics_table = Table(
    'thread_topics',
    db.metadata,
    db.Column('thread_id', db.Integer, ForeignKey('threads.id', ondelete='CASCADE'), primary_key=True),
    db.Column('topic_id', db.Integer, ForeignKey('topics.id', ondelete='CASCADE'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow, nullable=False),
    db.Column('updated_at', db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False),
    UniqueConstraint('thread_id', 'topic_id', name='_thread_topic_uc')
)

class ThreadTopic:
    """Junction table for many-to-many relationship between Thread and Topic"""
    __table__ = thread_topics_table

    def __repr__(self):
        return f'<ThreadTopic Thread_ID: {self.thread_id} Topic_ID: {self.topic_id}>'
