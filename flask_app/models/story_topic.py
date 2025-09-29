# flask_app/models/story_topic.py

from .base import db


class StoryTopic(db.Model):
    """Junction table for many-to-many relationship between stories and topics"""
    __tablename__ = 'story_topics'
    
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'), primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), primary_key=True)
    
    def __repr__(self):
        return f'<StoryTopic story_id={self.story_id} topic_id={self.topic_id}>'
