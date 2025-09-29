# flask_app/models/edge.py

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Index, CheckConstraint, ForeignKey, Enum
from .base import db, BaseModel
import enum


class EdgeRelation(enum.Enum):
    """Enum for edge relationship types"""
    FOLLOW_UP = "follow_up"
    REFUTES = "refutes"
    CLARIFIES = "clarifies"
    REPEATS = "repeats"
    ACTION = "action"
    OTHER = "other"


class Edge(BaseModel):
    """Model for relationships between events/claims"""
    __tablename__ = 'edges'
    
    # Core fields
    src_event_id = db.Column(db.Integer, ForeignKey('event_claims.id'), nullable=False, index=True)
    dst_event_id = db.Column(db.Integer, ForeignKey('event_claims.id'), nullable=False, index=True)
    relation = db.Column(Enum(EdgeRelation), nullable=False, index=True)
    
    # Relationships
    source_event = db.relationship('EventClaim', foreign_keys=[src_event_id])
    target_event = db.relationship('EventClaim', foreign_keys=[dst_event_id])
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_edge_src', 'src_event_id'),
        Index('idx_edge_dst', 'dst_event_id'),
        Index('idx_edge_relation', 'relation'),
        CheckConstraint('src_event_id != dst_event_id', name='ck_edge_no_self_loop'),
        db.UniqueConstraint('src_event_id', 'dst_event_id', 'relation', name='uk_edge_unique_relation'),
    )
    
    def __repr__(self):
        return f'<Edge {self.id}: {self.src_event_id} -> {self.dst_event_id} ({self.relation.value})>'
    
    def validate(self):
        """Validate edge instance"""
        errors = super().validate()
        
        # Self-loop validation
        if self.src_event_id == self.dst_event_id:
            errors.append("Event cannot be related to itself")
        
        # Event validation
        if not self.src_event_id or not self.dst_event_id:
            errors.append("Both source and destination events are required")
        
        # Relation validation
        if not self.relation:
            errors.append("Relationship type is required")
        
        return errors
    
    def get_relation_description(self):
        """Get human-readable description of the relationship"""
        descriptions = {
            EdgeRelation.FOLLOW_UP: "B happens after A and references/extends A",
            EdgeRelation.REFUTES: "B contradicts A",
            EdgeRelation.CLARIFIES: "B qualifies A without contradicting",
            EdgeRelation.REPEATS: "B restates A",
            EdgeRelation.ACTION: "B is a concrete policy/action following A",
            EdgeRelation.OTHER: "Other relationship type"
        }
        return descriptions.get(self.relation, "Unknown relationship")
    
    def is_directional(self):
        """Check if this relationship type is directional"""
        # All current relationship types are directional
        return True
    
    def can_reverse(self):
        """Check if this relationship can be reversed"""
        reversible_relations = {
            EdgeRelation.FOLLOW_UP,
            EdgeRelation.REPEATS,
            EdgeRelation.OTHER
        }
        return self.relation in reversible_relations
    
    def reverse(self):
        """Reverse the direction of this edge"""
        if not self.can_reverse():
            return False, "This relationship type cannot be reversed"
        
        self.src_event_id, self.dst_event_id = self.dst_event_id, self.src_event_id
        return True, None
    
    @classmethod
    def find_by_source_event(cls, event_id):
        """Find edges by source event"""
        try:
            return cls.query.filter_by(src_event_id=event_id).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error finding edges by source event {event_id}: {str(e)}")
            return []
    
    @classmethod
    def find_by_target_event(cls, event_id):
        """Find edges by target event"""
        try:
            return cls.query.filter_by(dst_event_id=event_id).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error finding edges by target event {event_id}: {str(e)}")
            return []
    
    @classmethod
    def find_by_event(cls, event_id):
        """Find all edges involving an event (both incoming and outgoing)"""
        try:
            return cls.query.filter(
                (cls.src_event_id == event_id) | (cls.dst_event_id == event_id)
            ).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error finding edges by event {event_id}: {str(e)}")
            return []
    
    @classmethod
    def find_by_relation(cls, relation):
        """Find edges by relationship type"""
        try:
            return cls.query.filter_by(relation=relation).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error finding edges by relation {relation}: {str(e)}")
            return []
    
    @classmethod
    def find_between_events(cls, src_event_id, dst_event_id):
        """Find edges between two specific events"""
        try:
            return cls.query.filter_by(
                src_event_id=src_event_id,
                dst_event_id=dst_event_id
            ).all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error finding edges between events: {str(e)}")
            return []
    
    @classmethod
    def create_relationship(cls, src_event, dst_event, relation):
        """Create a relationship between two events"""
        # Validate the relationship can be created
        can_connect, error = src_event.can_connect_to(dst_event)
        if not can_connect:
            return None, error
        
        # Check if relationship already exists
        existing = cls.find_between_events(src_event.id, dst_event.id)
        if existing:
            return None, "Relationship already exists between these events"
        
        # Create the edge
        edge = cls(
            src_event_id=src_event.id,
            dst_event_id=dst_event.id,
            relation=relation
        )
        
        if not edge.is_valid():
            return None, edge.validate()
        
        try:
            db.session.add(edge)
            db.session.commit()
            return edge, None
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error creating edge: {str(e)}")
            return None, str(e)
    
    @classmethod
    def get_relation_stats(cls):
        """Get statistics about relationship types"""
        try:
            from sqlalchemy import func
            stats = db.session.query(
                cls.relation,
                func.count(cls.id).label('count')
            ).group_by(cls.relation).all()
            
            return {stat.relation.value: stat.count for stat in stats}
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error getting relation stats: {str(e)}")
            return {}
    
    def to_dict(self, include_events=False):
        """Convert edge to dictionary with optional event details"""
        data = super().to_dict()
        
        if include_events:
            data['source_event'] = self.source_event.to_dict() if self.source_event else None
            data['target_event'] = self.target_event.to_dict() if self.target_event else None
        
        data['relation_description'] = self.get_relation_description()
        data['relation_value'] = self.relation.value if self.relation else None
        
        return data
