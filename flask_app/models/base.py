# app/models/base.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import inspect
import json

db = SQLAlchemy()

class BaseModel(db.Model):
    """Base model class with common functionality"""
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    @classmethod
    def safe_create(cls, **kwargs):
        """Safely create a new record with error handling"""
        try:
            instance = cls(**kwargs)
            db.session.add(instance)
            db.session.commit()
            return instance, None
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error creating {cls.__name__}: {str(e)}")
            return None, str(e)
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error creating {cls.__name__}: {str(e)}")
            return None, str(e)
    
    def safe_update(self, **kwargs):
        """Safely update record with error handling"""
        try:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            self.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            return True, None
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error updating {self.__class__.__name__}: {str(e)}")
            return False, str(e)
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error updating {self.__class__.__name__}: {str(e)}")
            return False, str(e)
    
    def safe_delete(self):
        """Safely delete record with error handling"""
        try:
            db.session.delete(self)
            db.session.commit()
            return True, None
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error deleting {self.__class__.__name__}: {str(e)}")
            return False, str(e)
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error deleting {self.__class__.__name__}: {str(e)}")
            return False, str(e)
    
    def to_dict(self, exclude_fields=None):
        """Convert model instance to dictionary"""
        if exclude_fields is None:
            exclude_fields = set()
        
        result = {}
        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)
                if isinstance(value, datetime):
                    result[column.name] = value.isoformat()
                else:
                    result[column.name] = value
        return result
    
    @classmethod
    def from_dict(cls, data, exclude_fields=None):
        """Create model instance from dictionary"""
        if exclude_fields is None:
            exclude_fields = set()
        
        # Filter out fields that shouldn't be set
        filtered_data = {k: v for k, v in data.items() 
                        if k not in exclude_fields and hasattr(cls, k)}
        
        return cls(**filtered_data)
    
    def update_from_dict(self, data, exclude_fields=None):
        """Update model instance from dictionary"""
        if exclude_fields is None:
            exclude_fields = set()
        
        for key, value in data.items():
            if (key not in exclude_fields and 
                hasattr(self, key) and 
                key not in ['id', 'created_at']):
                setattr(self, key, value)
        
        self.updated_at = datetime.now(timezone.utc)
    
    def validate(self, exclude_auto_fields=True):
        """Validate model instance - override in subclasses"""
        errors = []
        
        # Auto-generated fields that shouldn't be validated during import
        auto_fields = {'id', 'created_at', 'updated_at', 'captured_at'}
        
        # Check required fields
        for column in self.__table__.columns:
            if column.nullable is False and getattr(self, column.name) is None:
                # Skip auto-generated fields during import
                if exclude_auto_fields and column.name in auto_fields:
                    continue
                errors.append(f"{column.name} is required")
        
        return errors
    
    def is_valid(self):
        """Check if model instance is valid"""
        # For BaseModel, we only check if the object has been saved (has an id)
        # The actual validation of required fields is done in the validate() method
        return self.id is not None
    
    def save(self):
        """Save the model instance with validation"""
        if not self.is_valid():
            return False, self.validate()
        
        try:
            if self.id is None:
                db.session.add(self)
            db.session.commit()
            return True, None
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error saving {self.__class__.__name__}: {str(e)}")
            return False, str(e)
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error saving {self.__class__.__name__}: {str(e)}")
            return False, str(e)
    
    @classmethod
    def get_columns(cls):
        """Get all column names for the model"""
        return [column.name for column in cls.__table__.columns]
    
    @classmethod
    def get_relationships(cls):
        """Get all relationship names for the model"""
        return [rel.key for rel in cls.__mapper__.relationships]
    
    def __repr__(self):
        """String representation of the model"""
        return f'<{self.__class__.__name__} {self.id}>'
