"""
Base Writing Agent - Common functionality for all WriteCrew agents
Provides shared methods and interfaces for specialized agents
"""

import time
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import structlog

from ..models.task import TaskRequest, TaskResponse
from ..services.ai_providers import AIProviderService

logger = structlog.get_logger(__name__)


class BaseWritingAgent(ABC):
    """Base class for all WriteCrew writing agents"""
    
    def __init__(self, agent_id: str, name: str, ai_provider_service: AIProviderService):
        self.agent_id = agent_id
        self.name = name
        self.ai_provider_service = ai_provider_service
        self.start_time = None
        self.task_history: List[Dict[str, Any]] = []
        self.performance_metrics = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'average_processing_time': 0.0,
            'average_confidence': 0.0
        }
        
        logger.info(f"{self.name} agent initialized", agent_id=self.agent_id)
    
    @abstractmethod
    async def execute_task(self, task_request: TaskRequest) -> TaskResponse:
        """Execute a writing task - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities - must be implemented by subclasses"""
        pass
    
    def _start_timing(self):
        """Start timing for task execution"""
        self.start_time = time.time()
    
    def _get_processing_time(self) -> float:
        """Get processing time in seconds"""
        if self.start_time is None:
            return 0.0
        return round(time.time() - self.start_time, 2)
    
    def _create_error_response(self, task_request: TaskRequest, error_message: str) -> TaskResponse:
        """Create error response for failed tasks"""
        return TaskResponse(
            task_id=task_request.task_id,
            agent_id=self.agent_id,
            status="failed",
            content="",
            error_message=error_message,
            metadata={
                "error_type": "execution_error",
                "timestamp": datetime.utcnow().isoformat()
            },
            confidence_score=0.0,
            processing_time=self._get_processing_time()
        )
    
    async def _update_performance_metrics(self, task_response: TaskResponse):
        """Update agent performance metrics"""
        try:
            self.performance_metrics['total_tasks'] += 1
            
            if task_response.status == "completed":
                self.performance_metrics['successful_tasks'] += 1
            else:
                self.performance_metrics['failed_tasks'] += 1
            
            # Update average processing time
            total_time = (self.performance_metrics['average_processing_time'] * 
                         (self.performance_metrics['total_tasks'] - 1) + 
                         task_response.processing_time)
            self.performance_metrics['average_processing_time'] = round(
                total_time / self.performance_metrics['total_tasks'], 2
            )
            
            # Update average confidence
            if task_response.confidence_score > 0:
                total_confidence = (self.performance_metrics['average_confidence'] * 
                                  (self.performance_metrics['successful_tasks'] - 1) + 
                                  task_response.confidence_score)
                self.performance_metrics['average_confidence'] = round(
                    total_confidence / self.performance_metrics['successful_tasks'], 2
                )
            
            # Store task history (keep last 100)
            self.task_history.append({
                'task_id': task_response.task_id,
                'status': task_response.status,
                'processing_time': task_response.processing_time,
                'confidence_score': task_response.confidence_score,
                'timestamp': datetime.utcnow().isoformat(),
                'word_count': task_response.metadata.get('word_count', 0) if task_response.metadata else 0
            })
            
            if len(self.task_history) > 100:
                self.task_history = self.task_history[-100:]
                
        except Exception as e:
            logger.error("Failed to update performance metrics", agent_id=self.agent_id, error=str(e))
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        success_rate = 0.0
        if self.performance_metrics['total_tasks'] > 0:
            success_rate = round(
                self.performance_metrics['successful_tasks'] / self.performance_metrics['total_tasks'], 2
            )
        
        return {
            **self.performance_metrics,
            'success_rate': success_rate,
            'agent_id': self.agent_id,
            'name': self.name,
            'last_updated': datetime.utcnow().isoformat()
        }
    
    async def get_task_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent task history"""
        return self.task_history[-limit:] if self.task_history else []
    
    def _validate_task_request(self, task_request: TaskRequest) -> bool:
        """Validate task request format and requirements"""
        try:
            if not task_request.task_id:
                logger.error("Task request missing task_id")
                return False
            
            if not task_request.content:
                logger.error("Task request missing content")
                return False
            
            if not task_request.task_type:
                logger.error("Task request missing task_type")
                return False
            
            return True
            
        except Exception as e:
            logger.error("Task request validation failed", error=str(e))
            return False
    
    async def can_handle_task(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Check if agent can handle the given task"""
        try:
            capabilities = await self.get_capabilities()
            
            # Basic validation
            if not self._validate_task_request(task_request):
                return {
                    'can_handle': False,
                    'reason': 'Invalid task request format',
                    'confidence': 0.0
                }
            
            # Check if task type is supported
            supported_tasks = capabilities.get('supported_tasks', [])
            if supported_tasks and task_request.task_type not in supported_tasks:
                return {
                    'can_handle': False,
                    'reason': f'Task type {task_request.task_type} not supported',
                    'confidence': 0.0
                }
            
            # Estimate confidence based on content analysis
            confidence = await self._estimate_task_confidence(task_request, capabilities)
            
            return {
                'can_handle': confidence > 0.3,  # Minimum confidence threshold
                'reason': 'Task within agent capabilities' if confidence > 0.3 else 'Low confidence for task',
                'confidence': confidence,
                'estimated_processing_time': self._estimate_processing_time(task_request),
                'recommended_collaboration': self._suggest_collaboration(task_request, capabilities)
            }
            
        except Exception as e:
            logger.error("Task capability check failed", agent_id=self.agent_id, error=str(e))
            return {
                'can_handle': False,
                'reason': f'Error checking capabilities: {str(e)}',
                'confidence': 0.0
            }
    
    async def _estimate_task_confidence(self, task_request: TaskRequest, capabilities: Dict[str, Any]) -> float:
        """Estimate confidence for handling a specific task"""
        try:
            base_confidence = 0.7
            
            # Adjust based on content length
            content_length = len(task_request.content.split())
            if content_length > capabilities.get('max_word_count', 1000):
                base_confidence -= 0.2
            
            # Adjust based on complexity indicators
            complex_indicators = ['comprehensive', 'detailed', 'complex', 'advanced']
            if any(indicator in task_request.content.lower() for indicator in complex_indicators):
                base_confidence -= 0.1
            
            # Adjust based on specializations
            specializations = capabilities.get('specializations', [])
            content_lower = task_request.content.lower()
            
            specialization_match = False
            for spec in specializations:
                if any(word in content_lower for word in spec.lower().split()):
                    specialization_match = True
                    base_confidence += 0.1
                    break
            
            if not specialization_match:
                base_confidence -= 0.1
            
            return max(0.0, min(1.0, base_confidence))
            
        except Exception:
            return 0.5  # Default confidence
    
    def _estimate_processing_time(self, task_request: TaskRequest) -> int:
        """Estimate processing time in seconds"""
        try:
            # Base time
            base_time = 30
            
            # Adjust based on content length
            content_length = len(task_request.content.split())
            time_per_word = 0.5  # seconds per word
            content_time = content_length * time_per_word
            
            # Adjust based on task complexity
            complexity_indicators = ['comprehensive', 'detailed', 'research', 'analysis']
            complexity_multiplier = 1.0
            
            for indicator in complexity_indicators:
                if indicator in task_request.content.lower():
                    complexity_multiplier += 0.5
            
            total_time = (base_time + content_time) * complexity_multiplier
            
            return int(min(max(total_time, 10), 300))  # Clamp between 10-300 seconds
            
        except Exception:
            return 60  # Default 1 minute
    
    def _suggest_collaboration(self, task_request: TaskRequest, capabilities: Dict[str, Any]) -> List[str]:
        """Suggest collaborating agents for better results"""
        try:
            suggestions = []
            content_lower = task_request.content.lower()
            
            # Research collaboration
            if any(word in content_lower for word in ['research', 'facts', 'data', 'current']):
                suggestions.append('research_agent')
            
            # Style collaboration
            if any(word in content_lower for word in ['improve', 'enhance', 'polish', 'style']):
                suggestions.append('style_editor')
            
            # Grammar collaboration
            if any(word in content_lower for word in ['correct', 'grammar', 'proofread']):
                suggestions.append('grammar_assistant')
            
            # Structure collaboration
            if any(word in content_lower for word in ['organize', 'structure', 'outline']):
                suggestions.append('structure_architect')
            
            return suggestions
            
        except Exception:
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the agent"""
        try:
            # Check AI provider connectivity
            provider_healthy = await self.ai_provider_service.health_check()
            
            # Check recent performance
            recent_tasks = self.task_history[-10:] if self.task_history else []
            recent_success_rate = 1.0
            
            if recent_tasks:
                successful = sum(1 for task in recent_tasks if task['status'] == 'completed')
                recent_success_rate = successful / len(recent_tasks)
            
            # Overall health assessment
            health_score = 1.0
            issues = []
            
            if not provider_healthy:
                health_score -= 0.5
                issues.append("AI provider connectivity issues")
            
            if recent_success_rate < 0.8:
                health_score -= 0.3
                issues.append(f"Low recent success rate: {recent_success_rate:.2f}")
            
            if self.performance_metrics['average_processing_time'] > 120:
                health_score -= 0.2
                issues.append("High average processing time")
            
            status = "healthy" if health_score >= 0.8 else "degraded" if health_score >= 0.5 else "unhealthy"
            
            return {
                'agent_id': self.agent_id,
                'name': self.name,
                'status': status,
                'health_score': round(health_score, 2),
                'issues': issues,
                'provider_healthy': provider_healthy,
                'recent_success_rate': round(recent_success_rate, 2),
                'last_check': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Health check failed", agent_id=self.agent_id, error=str(e))
            return {
                'agent_id': self.agent_id,
                'name': self.name,
                'status': 'unhealthy',
                'health_score': 0.0,
                'issues': [f"Health check error: {str(e)}"],
                'last_check': datetime.utcnow().isoformat()
            }

