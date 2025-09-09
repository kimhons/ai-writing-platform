"""
Master Router Agent - Central Orchestrator for WriteCrew
Intelligent task routing and agent coordination using CrewAI
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import structlog

from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from ..models.task import TaskRequest, TaskResponse, AgentCapability
from ..services.ai_providers import AIProviderService
from ..utils.prompts import MASTER_ROUTER_PROMPTS

logger = structlog.get_logger(__name__)


class RoutingDecision(BaseModel):
    """Routing decision model"""
    primary_agent: str = Field(..., description="Primary agent to handle the task")
    supporting_agents: List[str] = Field(default=[], description="Supporting agents for collaboration")
    task_breakdown: List[Dict[str, Any]] = Field(default=[], description="Task breakdown with subtasks")
    estimated_complexity: str = Field(..., description="Task complexity: low, medium, high")
    estimated_duration: int = Field(..., description="Estimated duration in seconds")
    required_permissions: List[str] = Field(default=[], description="Required permissions")
    risk_assessment: str = Field(..., description="Risk level: low, medium, high")
    reasoning: str = Field(..., description="Reasoning for routing decision")


class TaskAnalysisTool(BaseTool):
    """Tool for analyzing task requirements"""
    
    name: str = "task_analyzer"
    description: str = "Analyze task requirements and determine optimal agent routing"
    
    def _run(self, task_description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze task and return routing recommendations"""
        try:
            # Task complexity analysis
            complexity_indicators = {
                'high': ['research', 'analysis', 'comprehensive', 'detailed', 'complex', 'multi-chapter'],
                'medium': ['edit', 'improve', 'enhance', 'format', 'structure'],
                'low': ['fix', 'correct', 'simple', 'quick', 'basic']
            }
            
            task_lower = task_description.lower()
            complexity = 'medium'  # default
            
            for level, indicators in complexity_indicators.items():
                if any(indicator in task_lower for indicator in indicators):
                    complexity = level
                    break
            
            # Agent capability matching
            agent_keywords = {
                'content_writer': ['write', 'create', 'draft', 'compose', 'story', 'article'],
                'research_agent': ['research', 'find', 'investigate', 'fact-check', 'sources'],
                'style_editor': ['edit', 'style', 'tone', 'voice', 'improve', 'polish'],
                'grammar_assistant': ['grammar', 'spelling', 'punctuation', 'correct', 'proofread'],
                'structure_architect': ['structure', 'organize', 'outline', 'format', 'layout'],
                'dialogue_specialist': ['dialogue', 'conversation', 'character', 'speech'],
                'technical_writer': ['technical', 'documentation', 'manual', 'guide', 'instructions'],
                'creative_enhancer': ['creative', 'imagination', 'innovative', 'unique', 'original']
            }
            
            # Find matching agents
            matching_agents = []
            for agent, keywords in agent_keywords.items():
                if any(keyword in task_lower for keyword in keywords):
                    matching_agents.append(agent)
            
            # Default to content writer if no specific match
            if not matching_agents:
                matching_agents = ['content_writer']
            
            # Risk assessment
            risk_keywords = {
                'high': ['delete', 'remove', 'replace all', 'overwrite', 'major changes'],
                'medium': ['edit', 'modify', 'change', 'update'],
                'low': ['suggest', 'recommend', 'highlight', 'comment']
            }
            
            risk_level = 'low'  # default
            for level, keywords in risk_keywords.items():
                if any(keyword in task_lower for keyword in keywords):
                    risk_level = level
                    break
            
            return {
                'complexity': complexity,
                'matching_agents': matching_agents,
                'risk_level': risk_level,
                'word_count_estimate': len(task_description.split()) * 10,  # rough estimate
                'requires_research': 'research' in task_lower or 'find' in task_lower,
                'requires_creativity': any(word in task_lower for word in ['creative', 'story', 'novel', 'fiction']),
                'requires_technical': any(word in task_lower for word in ['technical', 'documentation', 'manual'])
            }
            
        except Exception as e:
            logger.error("Task analysis failed", error=str(e))
            return {
                'complexity': 'medium',
                'matching_agents': ['content_writer'],
                'risk_level': 'low',
                'error': str(e)
            }


class MasterRouterAgent:
    """Master Router Agent for intelligent task orchestration"""
    
    def __init__(self, ai_provider_service: AIProviderService, agent_registry: Dict[str, Any]):
        self.ai_provider_service = ai_provider_service
        self.agent_registry = agent_registry
        self.task_history: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, Dict[str, float]] = {}
        
        # Initialize CrewAI agent
        self.crew_agent = Agent(
            role="Master Router and Task Orchestrator",
            goal="Intelligently route tasks to the most appropriate agents and coordinate multi-agent workflows",
            backstory=MASTER_ROUTER_PROMPTS["backstory"],
            verbose=True,
            allow_delegation=True,
            tools=[TaskAnalysisTool()],
            llm=ai_provider_service.get_primary_llm()
        )
        
        logger.info("Master Router Agent initialized")
    
    async def route_task(self, task_request: TaskRequest) -> RoutingDecision:
        """Route task to appropriate agents"""
        try:
            logger.info("Routing task", task_id=task_request.task_id, task_type=task_request.task_type)
            
            # Analyze task requirements
            analysis = await self._analyze_task(task_request)
            
            # Get agent recommendations
            routing_decision = await self._make_routing_decision(task_request, analysis)
            
            # Validate routing decision
            validated_decision = await self._validate_routing(routing_decision)
            
            # Update performance metrics
            await self._update_metrics(task_request, validated_decision)
            
            logger.info(
                "Task routing complete",
                task_id=task_request.task_id,
                primary_agent=validated_decision.primary_agent,
                supporting_agents=validated_decision.supporting_agents,
                complexity=validated_decision.estimated_complexity
            )
            
            return validated_decision
            
        except Exception as e:
            logger.error("Task routing failed", task_id=task_request.task_id, error=str(e))
            
            # Fallback routing
            return RoutingDecision(
                primary_agent="content_writer",
                supporting_agents=[],
                task_breakdown=[{"subtask": task_request.content, "agent": "content_writer"}],
                estimated_complexity="medium",
                estimated_duration=300,
                required_permissions=["collaborative"],
                risk_assessment="medium",
                reasoning=f"Fallback routing due to error: {str(e)}"
            )
    
    async def _analyze_task(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Analyze task requirements using AI"""
        try:
            # Create analysis task
            analysis_task = Task(
                description=f"""
                Analyze the following writing task and provide detailed insights:
                
                Task Type: {task_request.task_type}
                Content: {task_request.content}
                Context: {task_request.context or 'None provided'}
                User Preferences: {task_request.user_preferences or 'None specified'}
                
                Provide analysis including:
                1. Task complexity (low/medium/high)
                2. Required skills and capabilities
                3. Estimated word count impact
                4. Risk assessment
                5. Recommended agent types
                6. Potential collaboration needs
                """,
                agent=self.crew_agent,
                expected_output="Detailed task analysis with routing recommendations"
            )
            
            # Execute analysis
            crew = Crew(
                agents=[self.crew_agent],
                tasks=[analysis_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Parse result and extract structured data
            analysis = self._parse_analysis_result(str(result))
            
            return analysis
            
        except Exception as e:
            logger.error("Task analysis failed", error=str(e))
            return {
                'complexity': 'medium',
                'required_skills': ['writing'],
                'word_count_estimate': 500,
                'risk_level': 'low',
                'recommended_agents': ['content_writer']
            }
    
    def _parse_analysis_result(self, result: str) -> Dict[str, Any]:
        """Parse AI analysis result into structured data"""
        try:
            # Extract key information using simple parsing
            # In production, this would use more sophisticated NLP
            
            result_lower = result.lower()
            
            # Complexity detection
            if any(word in result_lower for word in ['complex', 'difficult', 'challenging', 'comprehensive']):
                complexity = 'high'
            elif any(word in result_lower for word in ['simple', 'easy', 'basic', 'straightforward']):
                complexity = 'low'
            else:
                complexity = 'medium'
            
            # Risk assessment
            if any(word in result_lower for word in ['high risk', 'dangerous', 'destructive']):
                risk_level = 'high'
            elif any(word in result_lower for word in ['medium risk', 'moderate']):
                risk_level = 'medium'
            else:
                risk_level = 'low'
            
            # Agent recommendations
            agent_mentions = {}
            for agent_name in self.agent_registry.keys():
                if agent_name.replace('_', ' ') in result_lower:
                    agent_mentions[agent_name] = result_lower.count(agent_name.replace('_', ' '))
            
            recommended_agents = sorted(agent_mentions.keys(), key=lambda x: agent_mentions[x], reverse=True)
            
            if not recommended_agents:
                recommended_agents = ['content_writer']
            
            return {
                'complexity': complexity,
                'risk_level': risk_level,
                'recommended_agents': recommended_agents[:3],  # Top 3
                'word_count_estimate': self._estimate_word_count(result),
                'requires_research': 'research' in result_lower,
                'requires_creativity': 'creative' in result_lower or 'imagination' in result_lower,
                'collaboration_needed': 'collaboration' in result_lower or 'multiple agents' in result_lower
            }
            
        except Exception as e:
            logger.error("Failed to parse analysis result", error=str(e))
            return {
                'complexity': 'medium',
                'risk_level': 'low',
                'recommended_agents': ['content_writer'],
                'word_count_estimate': 500
            }
    
    def _estimate_word_count(self, text: str) -> int:
        """Estimate word count impact from analysis"""
        # Simple heuristic based on text length and complexity indicators
        base_count = len(text.split()) * 5
        
        if 'comprehensive' in text.lower():
            base_count *= 3
        elif 'detailed' in text.lower():
            base_count *= 2
        elif 'brief' in text.lower() or 'short' in text.lower():
            base_count //= 2
        
        return max(50, min(base_count, 5000))  # Clamp between 50-5000 words
    
    async def _make_routing_decision(self, task_request: TaskRequest, analysis: Dict[str, Any]) -> RoutingDecision:
        """Make intelligent routing decision based on analysis"""
        try:
            # Select primary agent
            recommended_agents = analysis.get('recommended_agents', ['content_writer'])
            primary_agent = recommended_agents[0]
            
            # Select supporting agents based on task requirements
            supporting_agents = []
            
            if analysis.get('requires_research', False):
                supporting_agents.append('research_agent')
            
            if analysis.get('requires_creativity', False) and 'creative_enhancer' not in recommended_agents:
                supporting_agents.append('creative_enhancer')
            
            if analysis.get('complexity') == 'high':
                if 'structure_architect' not in recommended_agents:
                    supporting_agents.append('structure_architect')
                if 'style_editor' not in recommended_agents:
                    supporting_agents.append('style_editor')
            
            # Remove duplicates and primary agent from supporting agents
            supporting_agents = [agent for agent in supporting_agents if agent != primary_agent]
            supporting_agents = list(set(supporting_agents))
            
            # Create task breakdown
            task_breakdown = await self._create_task_breakdown(task_request, primary_agent, supporting_agents)
            
            # Estimate duration
            complexity_multipliers = {'low': 1, 'medium': 2, 'high': 4}
            base_duration = 60  # 1 minute base
            estimated_duration = base_duration * complexity_multipliers.get(analysis.get('complexity', 'medium'), 2)
            estimated_duration += len(supporting_agents) * 30  # 30 seconds per supporting agent
            
            # Determine required permissions
            required_permissions = self._determine_permissions(task_request, analysis)
            
            return RoutingDecision(
                primary_agent=primary_agent,
                supporting_agents=supporting_agents,
                task_breakdown=task_breakdown,
                estimated_complexity=analysis.get('complexity', 'medium'),
                estimated_duration=estimated_duration,
                required_permissions=required_permissions,
                risk_assessment=analysis.get('risk_level', 'low'),
                reasoning=f"Selected {primary_agent} based on task analysis. Complexity: {analysis.get('complexity')}. Supporting agents: {', '.join(supporting_agents) if supporting_agents else 'None'}."
            )
            
        except Exception as e:
            logger.error("Failed to make routing decision", error=str(e))
            raise
    
    async def _create_task_breakdown(self, task_request: TaskRequest, primary_agent: str, supporting_agents: List[str]) -> List[Dict[str, Any]]:
        """Create detailed task breakdown"""
        breakdown = []
        
        # Primary task
        breakdown.append({
            "subtask": task_request.content,
            "agent": primary_agent,
            "priority": 1,
            "dependencies": [],
            "estimated_duration": 120
        })
        
        # Supporting tasks
        for i, agent in enumerate(supporting_agents):
            if agent == 'research_agent':
                breakdown.append({
                    "subtask": f"Research and fact-check content for: {task_request.content[:100]}...",
                    "agent": agent,
                    "priority": 2,
                    "dependencies": [],
                    "estimated_duration": 90
                })
            elif agent == 'style_editor':
                breakdown.append({
                    "subtask": f"Review and enhance style for: {task_request.content[:100]}...",
                    "agent": agent,
                    "priority": 3,
                    "dependencies": [primary_agent],
                    "estimated_duration": 60
                })
            elif agent == 'structure_architect':
                breakdown.append({
                    "subtask": f"Optimize structure and organization for: {task_request.content[:100]}...",
                    "agent": agent,
                    "priority": 2,
                    "dependencies": [],
                    "estimated_duration": 75
                })
            else:
                breakdown.append({
                    "subtask": f"Support task for {agent}: {task_request.content[:100]}...",
                    "agent": agent,
                    "priority": 3,
                    "dependencies": [primary_agent],
                    "estimated_duration": 45
                })
        
        return breakdown
    
    def _determine_permissions(self, task_request: TaskRequest, analysis: Dict[str, Any]) -> List[str]:
        """Determine required permissions based on task and analysis"""
        permissions = []
        
        # Base permission based on risk level
        risk_level = analysis.get('risk_level', 'low')
        if risk_level == 'high':
            permissions.append('assistant')  # Highest control
        elif risk_level == 'medium':
            permissions.append('collaborative')
        else:
            permissions.append('semi_autonomous')
        
        # Additional permissions based on task type
        if task_request.task_type in ['delete', 'replace', 'major_edit']:
            permissions.append('assistant')  # Force highest control for destructive actions
        
        # User preference override
        if task_request.user_preferences and 'permission_level' in task_request.user_preferences:
            user_pref = task_request.user_preferences['permission_level']
            if user_pref in ['assistant', 'collaborative', 'semi_autonomous', 'autonomous']:
                permissions = [user_pref]
        
        return permissions or ['collaborative']  # Default fallback
    
    async def _validate_routing(self, routing_decision: RoutingDecision) -> RoutingDecision:
        """Validate and optimize routing decision"""
        try:
            # Check if primary agent exists and is available
            if routing_decision.primary_agent not in self.agent_registry:
                logger.warning(
                    "Primary agent not found, falling back to content_writer",
                    agent=routing_decision.primary_agent
                )
                routing_decision.primary_agent = 'content_writer'
            
            # Validate supporting agents
            valid_supporting_agents = []
            for agent in routing_decision.supporting_agents:
                if agent in self.agent_registry:
                    valid_supporting_agents.append(agent)
                else:
                    logger.warning("Supporting agent not found, skipping", agent=agent)
            
            routing_decision.supporting_agents = valid_supporting_agents
            
            # Limit number of supporting agents to prevent overload
            if len(routing_decision.supporting_agents) > 3:
                routing_decision.supporting_agents = routing_decision.supporting_agents[:3]
                logger.info("Limited supporting agents to 3 for performance")
            
            return routing_decision
            
        except Exception as e:
            logger.error("Routing validation failed", error=str(e))
            return routing_decision
    
    async def _update_metrics(self, task_request: TaskRequest, routing_decision: RoutingDecision):
        """Update performance metrics for routing decisions"""
        try:
            # Track routing decisions
            self.task_history.append({
                'timestamp': datetime.utcnow().isoformat(),
                'task_id': task_request.task_id,
                'task_type': task_request.task_type,
                'primary_agent': routing_decision.primary_agent,
                'supporting_agents': routing_decision.supporting_agents,
                'complexity': routing_decision.estimated_complexity,
                'estimated_duration': routing_decision.estimated_duration
            })
            
            # Keep only last 1000 entries
            if len(self.task_history) > 1000:
                self.task_history = self.task_history[-1000:]
            
            # Update agent usage metrics
            for agent in [routing_decision.primary_agent] + routing_decision.supporting_agents:
                if agent not in self.performance_metrics:
                    self.performance_metrics[agent] = {
                        'total_tasks': 0,
                        'avg_complexity': 0,
                        'success_rate': 1.0
                    }
                
                self.performance_metrics[agent]['total_tasks'] += 1
            
        except Exception as e:
            logger.error("Failed to update metrics", error=str(e))
    
    async def get_routing_statistics(self) -> Dict[str, Any]:
        """Get routing statistics and performance metrics"""
        try:
            total_tasks = len(self.task_history)
            
            if total_tasks == 0:
                return {
                    'total_tasks': 0,
                    'agent_usage': {},
                    'complexity_distribution': {},
                    'average_agents_per_task': 0
                }
            
            # Agent usage statistics
            agent_usage = {}
            complexity_counts = {'low': 0, 'medium': 0, 'high': 0}
            total_agents_used = 0
            
            for task in self.task_history:
                # Primary agent
                primary = task['primary_agent']
                if primary not in agent_usage:
                    agent_usage[primary] = {'primary': 0, 'supporting': 0}
                agent_usage[primary]['primary'] += 1
                
                # Supporting agents
                for agent in task['supporting_agents']:
                    if agent not in agent_usage:
                        agent_usage[agent] = {'primary': 0, 'supporting': 0}
                    agent_usage[agent]['supporting'] += 1
                
                # Complexity distribution
                complexity = task.get('complexity', 'medium')
                if complexity in complexity_counts:
                    complexity_counts[complexity] += 1
                
                # Total agents per task
                total_agents_used += 1 + len(task['supporting_agents'])
            
            return {
                'total_tasks': total_tasks,
                'agent_usage': agent_usage,
                'complexity_distribution': complexity_counts,
                'average_agents_per_task': total_agents_used / total_tasks,
                'performance_metrics': self.performance_metrics
            }
            
        except Exception as e:
            logger.error("Failed to get routing statistics", error=str(e))
            return {'error': str(e)}
    
    async def optimize_routing(self) -> Dict[str, Any]:
        """Optimize routing based on historical performance"""
        try:
            # Analyze historical performance
            stats = await self.get_routing_statistics()
            
            # Identify underperforming agents
            underperforming = []
            for agent, metrics in self.performance_metrics.items():
                if metrics.get('success_rate', 1.0) < 0.8:
                    underperforming.append(agent)
            
            # Identify overused agents
            total_tasks = stats['total_tasks']
            overused = []
            for agent, usage in stats['agent_usage'].items():
                total_usage = usage['primary'] + usage['supporting']
                if total_usage > total_tasks * 0.4:  # More than 40% of tasks
                    overused.append(agent)
            
            recommendations = {
                'underperforming_agents': underperforming,
                'overused_agents': overused,
                'optimization_suggestions': []
            }
            
            if underperforming:
                recommendations['optimization_suggestions'].append(
                    f"Consider retraining or replacing agents: {', '.join(underperforming)}"
                )
            
            if overused:
                recommendations['optimization_suggestions'].append(
                    f"Consider load balancing for agents: {', '.join(overused)}"
                )
            
            return recommendations
            
        except Exception as e:
            logger.error("Failed to optimize routing", error=str(e))
            return {'error': str(e)}

