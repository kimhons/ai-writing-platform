from flask import Blueprint, request, jsonify, session
from src.models.user import User, db
from src.models.document import Document, DocumentVersion, Collaboration
from src.routes.auth import require_auth
import json
from datetime import datetime

documents_bp = Blueprint('documents', __name__)

@documents_bp.route('/', methods=['POST'])
@require_auth
def create_document():
    """Create a new document"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        title = data.get('title', '').strip()
        doc_type = data.get('type', '').strip()
        content = data.get('content', '')
        privacy_level = data.get('privacy_level', 'private')
        metadata = data.get('metadata', {})
        
        # Validation
        if not title:
            return jsonify({'error': 'Title is required'}), 400
        
        if not doc_type:
            return jsonify({'error': 'Document type is required'}), 400
        
        valid_types = ['book', 'contract', 'paper', 'novel', 'technical', 'article', 'report']
        if doc_type not in valid_types:
            return jsonify({'error': f'Invalid document type. Must be one of: {", ".join(valid_types)}'}), 400
        
        valid_privacy = ['private', 'shared', 'public']
        if privacy_level not in valid_privacy:
            return jsonify({'error': f'Invalid privacy level. Must be one of: {", ".join(valid_privacy)}'}), 400
        
        # Create document
        document = Document(
            title=title,
            type=doc_type,
            owner_id=request.current_user.id,
            privacy_level=privacy_level
        )
        
        # Set metadata
        if metadata:
            document.set_metadata(metadata)
        
        db.session.add(document)
        db.session.flush()  # Get the document ID
        
        # Create initial version if content provided
        if content:
            version = DocumentVersion(
                document_id=document.id,
                version_number=1,
                changes_summary="Initial version",
                author_id=request.current_user.id
            )
            # In a real implementation, we would save content to S3
            # For now, we'll store a placeholder
            version.content_s3_key = f"documents/{document.id}/versions/1.txt"
            
            db.session.add(version)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Document created successfully',
            'document': document.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create document: {str(e)}'}), 500

@documents_bp.route('/', methods=['GET'])
@require_auth
def get_documents():
    """Get user's documents"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        doc_type = request.args.get('type')
        privacy_level = request.args.get('privacy')
        
        # Base query for user's own documents
        query = Document.query.filter_by(owner_id=request.current_user.id)
        
        # Add filters
        if doc_type:
            query = query.filter_by(type=doc_type)
        
        if privacy_level:
            query = query.filter_by(privacy_level=privacy_level)
        
        # Also include documents where user is a collaborator
        collaboration_docs = db.session.query(Document).join(Collaboration).filter(
            Collaboration.user_id == request.current_user.id
        )
        
        # Combine queries
        all_docs = query.union(collaboration_docs)
        
        # Paginate
        paginated = all_docs.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        documents = [doc.to_dict() for doc in paginated.items]
        
        return jsonify({
            'documents': documents,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': paginated.total,
                'pages': paginated.pages,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get documents: {str(e)}'}), 500

@documents_bp.route('/<document_id>', methods=['GET'])
@require_auth
def get_document(document_id):
    """Get a specific document"""
    try:
        document = Document.query.get(document_id)
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        # Check permissions
        if document.owner_id != request.current_user.id:
            # Check if user is a collaborator
            collaboration = Collaboration.query.filter_by(
                document_id=document_id,
                user_id=request.current_user.id
            ).first()
            
            if not collaboration:
                return jsonify({'error': 'Access denied'}), 403
        
        # Get document with versions
        doc_dict = document.to_dict()
        doc_dict['versions'] = [v.to_dict() for v in document.versions]
        doc_dict['collaborators'] = [c.to_dict() for c in document.collaborations]
        
        return jsonify({'document': doc_dict}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get document: {str(e)}'}), 500

@documents_bp.route('/<document_id>', methods=['PUT'])
@require_auth
def update_document(document_id):
    """Update a document"""
    try:
        document = Document.query.get(document_id)
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        # Check permissions (only owner or collaborators with write access)
        has_permission = False
        if document.owner_id == request.current_user.id:
            has_permission = True
        else:
            collaboration = Collaboration.query.filter_by(
                document_id=document_id,
                user_id=request.current_user.id
            ).first()
            
            if collaboration and collaboration.permission_level in ['write', 'admin']:
                has_permission = True
        
        if not has_permission:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update allowed fields
        if 'title' in data:
            title = data['title'].strip()
            if not title:
                return jsonify({'error': 'Title cannot be empty'}), 400
            document.title = title
        
        if 'type' in data:
            doc_type = data['type'].strip()
            valid_types = ['book', 'contract', 'paper', 'novel', 'technical', 'article', 'report']
            if doc_type not in valid_types:
                return jsonify({'error': f'Invalid document type. Must be one of: {", ".join(valid_types)}'}), 400
            document.type = doc_type
        
        if 'privacy_level' in data and document.owner_id == request.current_user.id:
            privacy_level = data['privacy_level']
            valid_privacy = ['private', 'shared', 'public']
            if privacy_level not in valid_privacy:
                return jsonify({'error': f'Invalid privacy level. Must be one of: {", ".join(valid_privacy)}'}), 400
            document.privacy_level = privacy_level
        
        if 'metadata' in data:
            document.set_metadata(data['metadata'])
        
        document.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Document updated successfully',
            'document': document.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update document: {str(e)}'}), 500

@documents_bp.route('/<document_id>', methods=['DELETE'])
@require_auth
def delete_document(document_id):
    """Delete a document (owner only)"""
    try:
        document = Document.query.get(document_id)
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        # Only owner can delete
        if document.owner_id != request.current_user.id:
            return jsonify({'error': 'Only the document owner can delete it'}), 403
        
        db.session.delete(document)
        db.session.commit()
        
        return jsonify({'message': 'Document deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete document: {str(e)}'}), 500

@documents_bp.route('/<document_id>/versions', methods=['GET'])
@require_auth
def get_document_versions(document_id):
    """Get document versions"""
    try:
        document = Document.query.get(document_id)
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        # Check permissions
        if document.owner_id != request.current_user.id:
            collaboration = Collaboration.query.filter_by(
                document_id=document_id,
                user_id=request.current_user.id
            ).first()
            
            if not collaboration:
                return jsonify({'error': 'Access denied'}), 403
        
        versions = DocumentVersion.query.filter_by(document_id=document_id).order_by(
            DocumentVersion.version_number.desc()
        ).all()
        
        return jsonify({
            'versions': [v.to_dict() for v in versions]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get versions: {str(e)}'}), 500

@documents_bp.route('/<document_id>/versions', methods=['POST'])
@require_auth
def create_document_version(document_id):
    """Create a new document version"""
    try:
        document = Document.query.get(document_id)
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        # Check permissions
        has_permission = False
        if document.owner_id == request.current_user.id:
            has_permission = True
        else:
            collaboration = Collaboration.query.filter_by(
                document_id=document_id,
                user_id=request.current_user.id
            ).first()
            
            if collaboration and collaboration.permission_level in ['write', 'admin']:
                has_permission = True
        
        if not has_permission:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        changes_summary = data.get('changes_summary', '').strip()
        content = data.get('content', '')
        
        if not changes_summary:
            return jsonify({'error': 'Changes summary is required'}), 400
        
        # Get next version number
        last_version = DocumentVersion.query.filter_by(document_id=document_id).order_by(
            DocumentVersion.version_number.desc()
        ).first()
        
        next_version = (last_version.version_number + 1) if last_version else 1
        
        # Create new version
        version = DocumentVersion(
            document_id=document_id,
            version_number=next_version,
            changes_summary=changes_summary,
            author_id=request.current_user.id
        )
        
        # In a real implementation, we would save content to S3
        if content:
            version.content_s3_key = f"documents/{document_id}/versions/{next_version}.txt"
        
        db.session.add(version)
        
        # Update document timestamp
        document.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Version created successfully',
            'version': version.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create version: {str(e)}'}), 500

@documents_bp.route('/<document_id>/share', methods=['POST'])
@require_auth
def share_document(document_id):
    """Share a document with another user"""
    try:
        document = Document.query.get(document_id)
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        # Only owner can share
        if document.owner_id != request.current_user.id:
            return jsonify({'error': 'Only the document owner can share it'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_email = data.get('user_email', '').strip().lower()
        permission_level = data.get('permission_level', 'read')
        
        if not user_email:
            return jsonify({'error': 'User email is required'}), 400
        
        valid_permissions = ['read', 'write', 'admin']
        if permission_level not in valid_permissions:
            return jsonify({'error': f'Invalid permission level. Must be one of: {", ".join(valid_permissions)}'}), 400
        
        # Find user to share with
        target_user = User.query.filter_by(email=user_email).first()
        if not target_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if already shared
        existing_collaboration = Collaboration.query.filter_by(
            document_id=document_id,
            user_id=target_user.id
        ).first()
        
        if existing_collaboration:
            # Update permission level
            existing_collaboration.permission_level = permission_level
            message = 'Permission level updated successfully'
        else:
            # Create new collaboration
            collaboration = Collaboration(
                document_id=document_id,
                user_id=target_user.id,
                permission_level=permission_level,
                invited_by=request.current_user.id
            )
            db.session.add(collaboration)
            message = 'Document shared successfully'
        
        db.session.commit()
        
        return jsonify({'message': message}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to share document: {str(e)}'}), 500

@documents_bp.route('/<document_id>/collaborators', methods=['GET'])
@require_auth
def get_collaborators(document_id):
    """Get document collaborators"""
    try:
        document = Document.query.get(document_id)
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        # Check permissions
        if document.owner_id != request.current_user.id:
            collaboration = Collaboration.query.filter_by(
                document_id=document_id,
                user_id=request.current_user.id
            ).first()
            
            if not collaboration:
                return jsonify({'error': 'Access denied'}), 403
        
        collaborations = Collaboration.query.filter_by(document_id=document_id).all()
        
        collaborators = []
        for collab in collaborations:
            user = User.query.get(collab.user_id)
            if user:
                collaborators.append({
                    'user': user.to_dict(),
                    'permission_level': collab.permission_level,
                    'invited_by': collab.invited_by,
                    'created_at': collab.created_at.isoformat() if collab.created_at else None
                })
        
        return jsonify({'collaborators': collaborators}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get collaborators: {str(e)}'}), 500

