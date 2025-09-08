from flask import Blueprint, request, jsonify, session
from src.models.user import User, db
from src.models.document import Document, AIInteraction
from src.routes.auth import require_auth
import openai
import os
import json
from datetime import datetime
import asyncio
import aiohttp

ai_bp = Blueprint('ai', __name__)

# Initialize OpenAI client
openai.api_key = os.getenv('OPENAI_API_KEY')

class AIOrchestrator:
    def __init__(self):
        self.providers = {
            'openai': self._openai_provider,
            'anthropic': self._anthropic_provider
        }
    
    async def _openai_provider(self, task, content, options):
        """OpenAI provider implementation"""
        try:
            if task == 'analyze':
                return await self._openai_analyze(content, options)
            elif task == 'generate':
                return await self._openai_generate(content, options)
            elif task == 'edit':
                return await self._openai_edit(content, options)
            else:
                raise ValueError(f"Unsupported task: {task}")
        except Exception as e:
            raise Exception(f"OpenAI provider error: {str(e)}")
    
    async def _openai_analyze(self, content, options):
        """Analyze content using OpenAI"""
        document_type = options.get('document_type', 'general')
        
        prompt = f"""Analyze this {document_type} document and provide a comprehensive analysis in JSON format:

Document content:
{content}

Please provide analysis with the following structure:
{{
    "structure": {{
        "sections": ["list of main sections"],
        "word_count": number,
        "readability_score": number_between_0_and_100,
        "organization_score": number_between_0_and_100
    }},
    "quality": {{
        "overall_score": number_between_0_and_100,
        "strengths": ["list of strengths"],
        "weaknesses": ["list of weaknesses"],
        "clarity_score": number_between_0_and_100,
        "coherence_score": number_between_0_and_100
    }},
    "suggestions": [
        {{
            "type": "grammar|style|structure|content",
            "priority": "low|medium|high",
            "title": "Brief title",
            "description": "Detailed description",
            "suggested_change": "Specific suggestion",
            "reasoning": "Why this change is recommended"
        }}
    ],
    "risks": {{
        "level": "low|medium|high",
        "issues": ["list of potential issues"],
        "compliance_notes": ["relevant compliance considerations"]
    }},
    "metadata": {{
        "estimated_reading_time": "X minutes",
        "target_audience": "identified audience",
        "tone": "identified tone",
        "style": "identified style"
    }}
}}"""

        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000
        )
        
        try:
            result = json.loads(response.choices[0].message.content)
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "structure": {"sections": [], "word_count": len(content.split()), "readability_score": 70, "organization_score": 70},
                "quality": {"overall_score": 75, "strengths": ["Content provided"], "weaknesses": ["Analysis incomplete"], "clarity_score": 70, "coherence_score": 70},
                "suggestions": [],
                "risks": {"level": "low", "issues": [], "compliance_notes": []},
                "metadata": {"estimated_reading_time": f"{len(content.split()) // 200} minutes", "target_audience": "general", "tone": "neutral", "style": "standard"}
            }
    
    async def _openai_generate(self, prompt, options):
        """Generate content using OpenAI"""
        style_profile = options.get('style_profile', {})
        max_tokens = options.get('max_tokens', 1000)
        temperature = options.get('temperature', 0.7)
        
        system_prompt = f"""You are an expert writing assistant. Generate content with these characteristics:
- Tone: {style_profile.get('tone', 'professional')}
- Style: {style_profile.get('style', 'clear and engaging')}
- Audience: {style_profile.get('audience', 'general')}
- Format: {options.get('format', 'paragraph')}
- Document type: {options.get('document_type', 'general')}

Ensure the content is well-structured, engaging, and appropriate for the specified audience and purpose."""

        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            "content": response.choices[0].message.content,
            "metadata": {
                "model": "gpt-4",
                "tokens_used": response.usage.total_tokens,
                "style_profile": style_profile
            }
        }
    
    async def _openai_edit(self, content, options):
        """Edit content using OpenAI"""
        instructions = options.get('instructions', 'Improve the content')
        
        prompt = f"""Please edit the following content based on these instructions: {instructions}

Original content:
{content}

Please provide:
1. The edited content
2. A summary of changes made
3. Reasoning for the changes

Format your response as JSON:
{{
    "edited_content": "the improved content",
    "changes_summary": "summary of what was changed",
    "reasoning": "explanation of why changes were made"
}}"""

        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000
        )
        
        try:
            result = json.loads(response.choices[0].message.content)
            return result
        except json.JSONDecodeError:
            return {
                "edited_content": content,
                "changes_summary": "Unable to process edits",
                "reasoning": "JSON parsing error occurred"
            }
    
    async def _anthropic_provider(self, task, content, options):
        """Anthropic provider implementation (placeholder)"""
        # This would implement Anthropic Claude API calls
        # For now, return a placeholder response
        return {
            "error": "Anthropic provider not yet implemented",
            "fallback": "Using OpenAI provider"
        }
    
    async def process_request(self, task, content, options):
        """Process AI request with provider selection"""
        provider = options.get('provider', 'openai')
        
        if provider not in self.providers:
            provider = 'openai'  # Fallback to OpenAI
        
        try:
            result = await self.providers[provider](task, content, options)
            return {
                'success': True,
                'result': result,
                'provider_used': provider,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'provider_used': provider,
                'timestamp': datetime.utcnow().isoformat()
            }

# Global AI orchestrator instance
ai_orchestrator = AIOrchestrator()

@ai_bp.route('/analyze', methods=['POST'])
@require_auth
def analyze_content():
    """Analyze document content using AI"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        content = data.get('content', '').strip()
        document_id = data.get('document_id')
        options = data.get('options', {})
        
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        # Validate document access if document_id provided
        if document_id:
            document = Document.query.get(document_id)
            if document:
                # Check permissions
                if document.owner_id != request.current_user.id:
                    from src.models.document import Collaboration
                    collaboration = Collaboration.query.filter_by(
                        document_id=document_id,
                        user_id=request.current_user.id
                    ).first()
                    
                    if not collaboration:
                        return jsonify({'error': 'Access denied to document'}), 403
        
        # Process with AI
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                ai_orchestrator.process_request('analyze', content, options)
            )
        finally:
            loop.close()
        
        if not result['success']:
            return jsonify({'error': result['error']}), 500
        
        # Log AI interaction
        ai_interaction = AIInteraction(
            user_id=request.current_user.id,
            document_id=document_id,
            interaction_type='analyze',
            model_used=result.get('provider_used', 'unknown'),
            input_tokens=len(content.split()),  # Rough estimate
            output_tokens=len(str(result['result']).split())  # Rough estimate
        )
        
        db.session.add(ai_interaction)
        db.session.commit()
        
        return jsonify({
            'analysis': result['result'],
            'metadata': {
                'provider': result['provider_used'],
                'timestamp': result['timestamp'],
                'interaction_id': ai_interaction.id
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@ai_bp.route('/generate', methods=['POST'])
@require_auth
def generate_content():
    """Generate content using AI"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        prompt = data.get('prompt', '').strip()
        document_id = data.get('document_id')
        options = data.get('options', {})
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        # Validate document access if document_id provided
        if document_id:
            document = Document.query.get(document_id)
            if document:
                # Check permissions
                if document.owner_id != request.current_user.id:
                    from src.models.document import Collaboration
                    collaboration = Collaboration.query.filter_by(
                        document_id=document_id,
                        user_id=request.current_user.id
                    ).first()
                    
                    if not collaboration or collaboration.permission_level == 'read':
                        return jsonify({'error': 'Write access required'}), 403
        
        # Process with AI
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                ai_orchestrator.process_request('generate', prompt, options)
            )
        finally:
            loop.close()
        
        if not result['success']:
            return jsonify({'error': result['error']}), 500
        
        # Log AI interaction
        ai_interaction = AIInteraction(
            user_id=request.current_user.id,
            document_id=document_id,
            interaction_type='generate',
            model_used=result.get('provider_used', 'unknown'),
            input_tokens=len(prompt.split()),  # Rough estimate
            output_tokens=len(str(result['result']).split())  # Rough estimate
        )
        
        db.session.add(ai_interaction)
        db.session.commit()
        
        return jsonify({
            'generated_content': result['result'],
            'metadata': {
                'provider': result['provider_used'],
                'timestamp': result['timestamp'],
                'interaction_id': ai_interaction.id
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Generation failed: {str(e)}'}), 500

@ai_bp.route('/edit', methods=['POST'])
@require_auth
def edit_content():
    """Edit content using AI"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        content = data.get('content', '').strip()
        document_id = data.get('document_id')
        options = data.get('options', {})
        
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        if not options.get('instructions'):
            return jsonify({'error': 'Edit instructions are required'}), 400
        
        # Validate document access if document_id provided
        if document_id:
            document = Document.query.get(document_id)
            if document:
                # Check permissions
                if document.owner_id != request.current_user.id:
                    from src.models.document import Collaboration
                    collaboration = Collaboration.query.filter_by(
                        document_id=document_id,
                        user_id=request.current_user.id
                    ).first()
                    
                    if not collaboration or collaboration.permission_level == 'read':
                        return jsonify({'error': 'Write access required'}), 403
        
        # Process with AI
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                ai_orchestrator.process_request('edit', content, options)
            )
        finally:
            loop.close()
        
        if not result['success']:
            return jsonify({'error': result['error']}), 500
        
        # Log AI interaction
        ai_interaction = AIInteraction(
            user_id=request.current_user.id,
            document_id=document_id,
            interaction_type='edit',
            model_used=result.get('provider_used', 'unknown'),
            input_tokens=len(content.split()),  # Rough estimate
            output_tokens=len(str(result['result']).split())  # Rough estimate
        )
        
        db.session.add(ai_interaction)
        db.session.commit()
        
        return jsonify({
            'edited_content': result['result'],
            'metadata': {
                'provider': result['provider_used'],
                'timestamp': result['timestamp'],
                'interaction_id': ai_interaction.id
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Edit failed: {str(e)}'}), 500

@ai_bp.route('/usage', methods=['GET'])
@require_auth
def get_ai_usage():
    """Get user's AI usage statistics"""
    try:
        # Get usage for the current user
        interactions = AIInteraction.query.filter_by(user_id=request.current_user.id).all()
        
        # Calculate statistics
        total_interactions = len(interactions)
        total_input_tokens = sum(i.input_tokens or 0 for i in interactions)
        total_output_tokens = sum(i.output_tokens or 0 for i in interactions)
        total_cost = sum(float(i.cost_usd or 0) for i in interactions)
        
        # Group by interaction type
        by_type = {}
        for interaction in interactions:
            itype = interaction.interaction_type
            if itype not in by_type:
                by_type[itype] = {'count': 0, 'tokens': 0}
            by_type[itype]['count'] += 1
            by_type[itype]['tokens'] += (interaction.input_tokens or 0) + (interaction.output_tokens or 0)
        
        # Recent interactions (last 10)
        recent = AIInteraction.query.filter_by(user_id=request.current_user.id).order_by(
            AIInteraction.created_at.desc()
        ).limit(10).all()
        
        return jsonify({
            'usage_summary': {
                'total_interactions': total_interactions,
                'total_input_tokens': total_input_tokens,
                'total_output_tokens': total_output_tokens,
                'total_cost_usd': total_cost,
                'by_type': by_type
            },
            'recent_interactions': [i.to_dict() for i in recent]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get usage: {str(e)}'}), 500

@ai_bp.route('/models', methods=['GET'])
def get_available_models():
    """Get list of available AI models and providers"""
    return jsonify({
        'providers': {
            'openai': {
                'models': ['gpt-4', 'gpt-3.5-turbo'],
                'capabilities': ['analyze', 'generate', 'edit'],
                'status': 'available'
            },
            'anthropic': {
                'models': ['claude-3-opus', 'claude-3-sonnet'],
                'capabilities': ['analyze', 'generate', 'edit'],
                'status': 'coming_soon'
            }
        },
        'default_provider': 'openai'
    }), 200

