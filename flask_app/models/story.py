# flask_app/models/story.py

from datetime import datetime, date
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Index, CheckConstraint
from .base import db, BaseModel
import re
from urllib.parse import urlparse


class Story(BaseModel):
    """Model for news articles and content"""
    __tablename__ = 'stories'
    
    # Core fields
    url = db.Column(db.String(2048), unique=True, nullable=False, index=True)
    title = db.Column(db.String(500), nullable=False)
    source_name = db.Column(db.String(200), nullable=False, index=True)
    author = db.Column(db.String(200), nullable=True)
    published_at = db.Column(db.Date, nullable=True, index=True)
    captured_at = db.Column(db.DateTime, default=lambda: datetime.now(), nullable=False, index=True)
    summary = db.Column(db.Text, nullable=True)
    raw_text = db.Column(db.Text, nullable=True)
    
    # Relationships
    primary_events = db.relationship('EventClaim', lazy='dynamic', foreign_keys='EventClaim.story_primary_id')
    event_links = db.relationship('EventStoryLink', backref='story_obj', lazy='dynamic', cascade='all, delete-orphan')
    story_tags = db.relationship('StoryTag', backref='story_obj', lazy='dynamic', cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        Index('idx_story_url', 'url'),
        Index('idx_story_published_at', 'published_at'),
        Index('idx_story_source', 'source_name'),
        Index('idx_story_captured_at', 'captured_at'),
        CheckConstraint('length(url) > 0', name='ck_story_url_not_empty'),
        CheckConstraint('length(title) > 0', name='ck_story_title_not_empty'),
        CheckConstraint('length(source_name) > 0', name='ck_story_source_not_empty'),
    )
    
    @classmethod
    def find_by_url(cls, url):
        """Find a story by URL"""
        return cls.query.filter_by(url=url).first()
    
    def __repr__(self):
        return f'<Story {self.id}: {self.title[:50]}...>'
    
    def validate(self, exclude_auto_fields=True):
        """Validate story instance"""
        errors = super().validate(exclude_auto_fields=exclude_auto_fields)
        
        # URL validation
        if self.url:
            if not self._is_valid_url(self.url):
                errors.append("URL format is invalid")
            if len(self.url) > 2048:
                errors.append("URL is too long (max 2048 characters)")
        
        # Title validation
        if self.title and len(self.title) > 500:
            errors.append("Title is too long (max 500 characters)")
        
        # Source validation
        if self.source_name and len(self.source_name) > 200:
            errors.append("Source name is too long (max 200 characters)")
        
        # Author validation
        if self.author and len(self.author) > 200:
            errors.append("Author name is too long (max 200 characters)")
        
        # Date validation
        if self.published_at and self.published_at > date.today():
            errors.append("Published date cannot be in the future")
        
        return errors
    
    def _is_valid_url(self, url):
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def canonicalize_url(self):
        """Canonicalize URL by removing UTM parameters and normalizing"""
        if not self.url:
            return
        
        try:
            parsed = urlparse(self.url)
            # Remove UTM parameters
            query_params = []
            if parsed.query:
                for param in parsed.query.split('&'):
                    if not param.startswith(('utm_', 'fbclid', 'gclid')):
                        query_params.append(param)
            
            # Rebuild URL
            new_query = '&'.join(query_params) if query_params else ''
            self.url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if new_query:
                self.url += f"?{new_query}"
            if parsed.fragment:
                self.url += f"#{parsed.fragment}"
                
        except Exception as e:
            current_app.logger.warning(f"Failed to canonicalize URL {self.url}: {str(e)}")
    
    def get_domain(self):
        """Get domain from URL"""
        try:
            parsed = urlparse(self.url)
            return parsed.netloc
        except Exception:
            return None
    
    def get_tags(self):
        """Get all tags associated with this story"""
        return [link.tag for link in self.story_tags]
    
    def add_tag(self, tag):
        """Add a tag to this story"""
        from .tag import Tag
        from .story_tag import StoryTag
        
        if isinstance(tag, str):
            # Find or create tag by name
            tag_obj = Tag.query.filter_by(name=tag).first()
            if not tag_obj:
                tag_obj = Tag(name=tag)
                db.session.add(tag_obj)
                db.session.flush()  # Get the ID
        else:
            tag_obj = tag
        
        # Check if relationship already exists
        existing = StoryTag.query.filter_by(story_id=self.id, tag_id=tag_obj.id).first()
        if not existing:
            story_tag = StoryTag(story_id=self.id, tag_id=tag_obj.id)
            db.session.add(story_tag)
    
    def remove_tag(self, tag):
        """Remove a tag from this story"""
        from .story_tag import StoryTag
        
        if isinstance(tag, str):
            # Find tag by name
            tag_obj = Tag.query.filter_by(name=tag).first()
            if tag_obj:
                StoryTag.query.filter_by(story_id=self.id, tag_id=tag_obj.id).delete()
        else:
            StoryTag.query.filter_by(story_id=self.id, tag_id=tag.id).delete()
    
    @classmethod
    def find_by_url(cls, url):
        """Find story by URL with error handling"""
        try:
            return cls.query.filter_by(url=url).first()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error finding story by URL {url}: {str(e)}")
            return None
    
    @classmethod
    def find_by_source(cls, source_name):
        """Find stories by source name"""
        try:
            return cls.query.filter_by(source_name=source_name).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error finding stories by source {source_name}: {str(e)}")
            return []
    
    @classmethod
    def find_by_date_range(cls, start_date, end_date):
        """Find stories within date range"""
        try:
            return cls.query.filter(
                cls.published_at >= start_date,
                cls.published_at <= end_date
            ).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error finding stories by date range: {str(e)}")
            return []
    
    @classmethod
    def find_duplicates(cls, story, similarity_threshold=0.92):
        """Find potential duplicate stories"""
        try:
            from difflib import SequenceMatcher
            
            duplicates = []
            
            # Check for exact URL match
            exact_match = cls.query.filter_by(url=story.url).first()
            if exact_match and exact_match.id != story.id:
                duplicates.append({
                    'story': exact_match,
                    'reason': 'exact_url',
                    'confidence': 1.0
                })
            
            # Check for title similarity
            if story.title:
                all_stories = cls.query.filter(cls.id != story.id).all()
                for other_story in all_stories:
                    if other_story.title:
                        similarity = SequenceMatcher(None, story.title.lower(), other_story.title.lower()).ratio()
                        if similarity >= similarity_threshold:
                            duplicates.append({
                                'story': other_story,
                                'reason': 'title_similarity',
                                'confidence': similarity
                            })
            
            # Check for same source within 3 days
            if story.source_name and story.published_at:
                from datetime import timedelta
                date_range_start = story.published_at - timedelta(days=3)
                date_range_end = story.published_at + timedelta(days=3)
                
                same_source_stories = cls.query.filter(
                    cls.source_name == story.source_name,
                    cls.published_at >= date_range_start,
                    cls.published_at <= date_range_end,
                    cls.id != story.id
                ).all()
                
                for other_story in same_source_stories:
                    duplicates.append({
                        'story': other_story,
                        'reason': 'same_source_date',
                        'confidence': 0.8
                    })
            
            return duplicates
            
        except Exception as e:
            current_app.logger.error(f"Error finding duplicates for story {story.id}: {str(e)}")
            return []
