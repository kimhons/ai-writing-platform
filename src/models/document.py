from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
import json

db = SQLAlchemy()

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(100), nullable=False)  # book, contract, paper, etc.
    owner_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    content_s3_key = db.Column(db.String(500))
    metadata = db.Column(db.Text)  # JSON string for metadata
    privacy_level = db.Column(db.String(50), default='private')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    versions = db.relationship('DocumentVersion', backref='document', lazy=True, cascade='all, delete-orphan')
    collaborations = db.relationship('Collaboration', backref='document', lazy=True, cascade='all, delete-orphan')
    ai_interactions = db.relationship('AIInteraction', backref='document', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Document {self.title}>'
    
    def to_dict(self):
        metadata_dict = {}
        if self.metadata:
            try:
                metadata_dict = json.loads(self.metadata)
            except json.JSONDecodeError:
                metadata_dict = {}
                
        return {
            'id': self.id,
            'title': self.title,
            'type': self.type,
            'owner_id': self.owner_id,
            'content_s3_key': self.content_s3_key,
            'metadata': metadata_dict,
            'privacy_level': self.privacy_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def set_metadata(self, metadata_dict):
        """Set metadata as JSON string"""
        self.metadata = json.dumps(metadata_dict)
    
    def get_metadata(self):
        """Get metadata as dictionary"""
        if self.metadata:
            try:
                return json.loads(self.metadata)
            except json.JSONDecodeError:
                return {}
        return {}

class DocumentVersion(db.Model):
    __tablename__ = 'document_versions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = db.Column(db.String(36), db.ForeignKey('documents.id'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    content_s3_key = db.Column(db.String(500))
    changes_summary = db.Column(db.Text)
    author_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<DocumentVersion {self.document_id} v{self.version_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'version_number': self.version_number,
            'content_s3_key': self.content_s3_key,
            'changes_summary': self.changes_summary,
            'author_id': self.author_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Collaboration(db.Model):
    __tablename__ = 'collaborations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = db.Column(db.String(36), db.ForeignKey('documents.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    permission_level = db.Column(db.String(50), nullable=False)  # read, write, admin
    invited_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Collaboration {self.user_id} on {self.document_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'user_id': self.user_id,
            'permission_level': self.permission_level,
            'invited_by': self.invited_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AIInteraction(db.Model):
    __tablename__ = 'ai_interactions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    document_id = db.Column(db.String(36), db.ForeignKey('documents.id'))
    interaction_type = db.Column(db.String(100))  # analyze, generate, edit
    model_used = db.Column(db.String(100))
    input_tokens = db.Column(db.Integer)
    output_tokens = db.Column(db.Integer)
    cost_usd = db.Column(db.Numeric(10, 4))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AIInteraction {self.interaction_type} by {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'document_id': self.document_id,
            'interaction_type': self.interaction_type,
            'model_used': self.model_used,
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'cost_usd': float(self.cost_usd) if self.cost_usd else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

