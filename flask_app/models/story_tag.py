# flask_app/models/story_tag.py

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Index, ForeignKey, UniqueConstraint
from .base import db, BaseModel


class StoryTag(BaseModel):
    """Junction table for many-to-many relationship between stories and tags"""
    __tablename__ = 'story_tags'
    
    # Foreign keys
    story_id = db.Column(db.Integer, ForeignKey('stories.id'), nullable=False, index=True)
    tag_id = db.Column(db.Integer, ForeignKey('tags.id'), nullable=False, index=True)
    
    # Relationships
    story = db.relationship('Story')
    tag = db.relationship('Tag')
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('story_id', 'tag_id', name='uk_story_tag_unique'),
        Index('idx_story_tag_story', 'story_id'),
        Index('idx_story_tag_tag', 'tag_id'),
    )
    
    def __repr__(self):
        return f'<StoryTag {self.story_id} -> {self.tag_id}>'
    
    def validate(self):
        """Validate story-tag link instance"""
        errors = super().validate()
        
        # Story validation
        if not self.story_id:
            errors.append("Story ID is required")
        
        # Tag validation
        if not self.tag_id:
            errors.append("Tag ID is required")
        
        return errors
    
    @classmethod
    def find_by_story(cls, story_id):
        """Find all tag links for a story"""
        try:
            return cls.query.filter_by(story_id=story_id).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error finding tag links by story {story_id}: {str(e)}")
            return []
    
    @classmethod
    def find_by_tag(cls, tag_id):
        """Find all story links for a tag"""
        try:
            return cls.query.filter_by(tag_id=tag_id).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error finding story links by tag {tag_id}: {str(e)}")
            return []
    
    @classmethod
    def find_by_story_and_tag(cls, story_id, tag_id):
        """Find specific story-tag link"""
        try:
            return cls.query.filter_by(story_id=story_id, tag_id=tag_id).first()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error finding story-tag link: {str(e)}")
            return None
    
    @classmethod
    def create_link(cls, story, tag):
        """Create a link between a story and a tag"""
        # Check if link already exists
        existing = cls.find_by_story_and_tag(story.id, tag.id)
        if existing:
            return existing, "Link already exists"
        
        # Create the link
        link = cls(
            story_id=story.id,
            tag_id=tag.id
        )
        
        if not link.is_valid():
            return None, link.validate()
        
        try:
            db.session.add(link)
            db.session.commit()
            return link, None
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error creating story-tag link: {str(e)}")
            return None, str(e)
    
    @classmethod
    def remove_link(cls, story, tag):
        """Remove a link between a story and a tag"""
        try:
            link = cls.find_by_story_and_tag(story.id, tag.id)
            if link:
                db.session.delete(link)
                db.session.commit()
                return True, None
            else:
                return False, "Link does not exist"
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error removing story-tag link: {str(e)}")
            return False, str(e)
    
    @classmethod
    def get_story_tag_stats(cls):
        """Get statistics about story-tag relationships"""
        try:
            from sqlalchemy import func
            stats = db.session.query(
                func.count(cls.id).label('total_links'),
                func.count(func.distinct(cls.story_id)).label('stories_with_tags'),
                func.count(func.distinct(cls.tag_id)).label('tags_with_stories')
            ).first()
            
            return {
                'total_links': stats.total_links or 0,
                'stories_with_tags': stats.stories_with_tags or 0,
                'tags_with_stories': stats.tags_with_stories or 0
            }
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error getting story-tag stats: {str(e)}")
            return {
                'total_links': 0,
                'stories_with_tags': 0,
                'tags_with_stories': 0
            }
    
    @classmethod
    def get_tags_for_stories(cls, story_ids):
        """Get all tags for a list of stories"""
        try:
            return cls.query.filter(cls.story_id.in_(story_ids)).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error getting tags for stories: {str(e)}")
            return []
    
    @classmethod
    def get_stories_for_tags(cls, tag_ids):
        """Get all stories for a list of tags"""
        try:
            return cls.query.filter(cls.tag_id.in_(tag_ids)).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error getting stories for tags: {str(e)}")
            return []
    
    def to_dict(self, include_related=False):
        """Convert link to dictionary with optional related objects"""
        data = super().to_dict()
        
        if include_related:
            data['story'] = self.story.to_dict() if self.story else None
            data['tag'] = self.tag.to_dict() if self.tag else None
        
        return data
