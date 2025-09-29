# flask_app/models/tag.py

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Index, CheckConstraint
from .base import db, BaseModel


class Tag(BaseModel):
    """Model for categorization labels"""
    __tablename__ = 'tags'
    
    # Core fields
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    
    # Relationships
    story_tags = db.relationship('StoryTag', backref='tag_obj', lazy='dynamic', cascade='all, delete-orphan')
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_tag_name', 'name'),
        CheckConstraint('length(name) > 0', name='ck_tag_name_not_empty'),
        CheckConstraint('length(name) <= 100', name='ck_tag_name_length'),
    )
    
    def __repr__(self):
        return f'<Tag {self.id}: {self.name}>'
    
    def validate(self):
        """Validate tag instance"""
        errors = super().validate()
        
        # Name validation
        if self.name and len(self.name.strip()) == 0:
            errors.append("Tag name cannot be empty")
        
        if self.name and len(self.name) > 100:
            errors.append("Tag name is too long (max 100 characters)")
        
        # Check for duplicate name (case-insensitive)
        if self.name:
            existing = Tag.query.filter(
                Tag.name.ilike(self.name),
                Tag.id != self.id
            ).first()
            if existing:
                errors.append("Tag name already exists")
        
        return errors
    
    def get_story_count(self):
        """Get number of stories with this tag"""
        try:
            return self.story_tags.count()
        except Exception:
            return 0
    
    def get_stories(self):
        """Get all stories with this tag"""
        try:
            return [link.story for link in self.story_tags]
        except Exception:
            return []
    
    def normalize_name(self):
        """Normalize tag name (lowercase, trim, replace spaces with underscores)"""
        if self.name:
            self.name = self.name.strip().lower().replace(' ', '_')
    
    @classmethod
    def find_by_name(cls, name):
        """Find tag by name (case-insensitive)"""
        try:
            return cls.query.filter(cls.name.ilike(name)).first()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error finding tag by name {name}: {str(e)}")
            return None
    
    @classmethod
    def search_by_name(cls, search_term):
        """Search tags by name (case-insensitive partial match)"""
        try:
            return cls.query.filter(
                cls.name.ilike(f'%{search_term}%')
            ).order_by(cls.name.asc()).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error searching tags by name {search_term}: {str(e)}")
            return []
    
    @classmethod
    def get_all_ordered(cls):
        """Get all tags ordered by name"""
        try:
            return cls.query.order_by(cls.name.asc()).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error getting all tags: {str(e)}")
            return []
    
    @classmethod
    def get_popular_tags(cls, limit=10):
        """Get most popular tags by usage count"""
        try:
            from sqlalchemy import func
            return db.session.query(
                cls,
                func.count(StoryTag.id).label('usage_count')
            ).join(StoryTag).group_by(cls.id).order_by(
                func.count(StoryTag.id).desc()
            ).limit(limit).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error getting popular tags: {str(e)}")
            return []
    
    @classmethod
    def find_or_create(cls, name):
        """Find existing tag or create new one"""
        if not name or not name.strip():
            return None, "Tag name is required"
        
        # Normalize the name
        normalized_name = name.strip().lower().replace(' ', '_')
        
        # Try to find existing tag
        tag = cls.find_by_name(normalized_name)
        if tag:
            return tag, None
        
        # Create new tag
        tag = cls(name=normalized_name)
        if not tag.is_valid():
            return None, tag.validate()
        
        try:
            db.session.add(tag)
            db.session.commit()
            return tag, None
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error creating tag {normalized_name}: {str(e)}")
            return None, str(e)
    
    @classmethod
    def get_usage_stats(cls):
        """Get usage statistics for all tags"""
        try:
            from sqlalchemy import func
            stats = db.session.query(
                cls.name,
                func.count(StoryTag.id).label('usage_count')
            ).outerjoin(StoryTag).group_by(cls.id, cls.name).order_by(
                func.count(StoryTag.id).desc()
            ).all()
            
            return [{'name': stat.name, 'usage_count': stat.usage_count} for stat in stats]
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error getting tag usage stats: {str(e)}")
            return []
    
    def to_dict(self, include_counts=False):
        """Convert tag to dictionary with optional usage count"""
        data = super().to_dict()
        
        if include_counts:
            data['usage_count'] = self.get_story_count()
        
        return data
