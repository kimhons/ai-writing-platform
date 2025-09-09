"""
Agent Orchestration Service
Manages multi-agent workflows, task distribution, and coordination
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

from crewai import Crew, Task
from ..agents.master_router import MasterRouterAgent
from ..agents.content_writer import ContentWriterAgent
from ..agents.research_agent import ResearchAgent
from ..agents.style_editor import StyleEditorAgent
from ..agents.grammar_assistant import GrammarAssistantAgent
from ..agents.structure_architect import StructureArchitectAgent
from ..agents.legal_expert import LegalWritingExpertAgent
from ..agents.medical_expert import MedicalWritingExpertAgent
from ..agents.technical_expert import TechnicalWritingExpertAgent
from ..agents.academic_expert import AcademicWritingExpertAgent
from ..services.ai_provider_service import AIProviderService
from ..config.settings import settings

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

@dataclass
class WorkflowTask:
    """Individual task within a workflow"""
    id: str
    agent_type: str
    description: str
    input_data: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    priority: TaskPriority = TaskPriority.MEDIUM
    status: WorkflowStatus = WorkflowStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time: Optional[float] = None

@dataclass
class Workflow:
    """Multi-agent workflow definition"""
    id: str
    name: str
    description: str
    tasks: List[WorkflowTask]
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_processing_time: Optional[float] = None
    user_id: str = ""
    document_id: str = ""
    permission_level: int = 2
    
class AgentOrchestrator:
    """
    Orchestrates multi-agent workflows with intelligent task distribution,
    dependency management, and performance optimization
    """
    
    def __init__(self, ai_provider_service: AIProviderService):
        self.ai_provider_service = ai_provider_service
        self.active_workflows: Dict[str, Workflow] = {}
        self.agent_pool = self._initialize_agent_pool()
        self.performance_metrics = {
            'total_workflows': 0,
            'successful_workflows': 0,
            'failed_workflows': 0,
            'average_processing_time': 0.0,
            'agent_utilization': {}
        }
        
    def _initialize_agent_pool(self) -> Dict[str, Any]:
        """Initialize all available agents"""
        return {
            'master_router': MasterRouterAgent(self.ai_provider_service),
            'content_writer': ContentWriterAgent(self.ai_provider_service),
            'research_agent': ResearchAgent(self.ai_provider_service),
            'style_editor': StyleEditorAgent(self.ai_provider_service),
            'grammar_assistant': GrammarAssistantAgent(self.ai_provider_service),
            'structure_architect': StructureArchitectAgent(self.ai_provider_service),
            'legal_expert': LegalWritingExpertAgent(self.ai_provider_service),
            'medical_expert': MedicalWritingExpertAgent(self.ai_provider_service),
            'technical_expert': TechnicalWritingExpertAgent(self.ai_provider_service),
            'academic_expert': AcademicWritingExpertAgent(self.ai_provider_service)
        }
    
    async def create_workflow(self, workflow_request: Dict[str, Any]) -> str:
        """Create a new multi-agent workflow"""
        try:
            # Use Master Router to analyze and plan workflow
            master_router = self.agent_pool['master_router']
            routing_decision = await master_router.route_task(workflow_request)
            
            # Create workflow tasks based on routing decision
            workflow_id = f"workflow_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
            tasks = self._create_workflow_tasks(routing_decision, workflow_request)
            
            workflow = Workflow(
                id=workflow_id,
                name=workflow_request.get('name', 'Untitled Workflow'),
                description=workflow_request.get('description', ''),
                tasks=tasks,
                user_id=workflow_request.get('user_id', ''),
                document_id=workflow_request.get('document_id', ''),
                permission_level=workflow_request.get('permission_level', 2)
            )
            
            self.active_workflows[workflow_id] = workflow
            logger.info(f"Created workflow {workflow_id} with {len(tasks)} tasks")
            
            return workflow_id
            
        except Exception as e:
            logger.error(f"Error creating workflow: {str(e)}")
            raise
    
    def _create_workflow_tasks(self, routing_decision: Dict[str, Any], 
                             workflow_request: Dict[str, Any]) -> List[WorkflowTask]:
        """Create individual tasks based on routing decision"""
        tasks = []
        task_counter = 1
        
        # Primary agent task
        primary_task = WorkflowTask(
            id=f"task_{task_counter}",
            agent_type=routing_decision['primary_agent'],
            description=f"Primary task: {routing_decision['task_breakdown']['primary_task']}",
            input_data=workflow_request,
            priority=TaskPriority.HIGH
        )
        tasks.append(primary_task)
        task_counter += 1
        
        # Supporting agent tasks
        for supporting_agent in routing_decision.get('supporting_agents', []):
            supporting_task = WorkflowTask(
                id=f"task_{task_counter}",
                agent_type=supporting_agent,
                description=f"Supporting task for {supporting_agent}",
                input_data=workflow_request,
                dependencies=[primary_task.id],
                priority=TaskPriority.MEDIUM
            )
            tasks.append(supporting_task)
            task_counter += 1
        
        # Quality assurance tasks
        if routing_decision.get('requires_review', False):
            qa_task = WorkflowTask(
                id=f"task_{task_counter}",
                agent_type='grammar_assistant',
                description="Quality assurance and final review",
                input_data=workflow_request,
                dependencies=[t.id for t in tasks],
                priority=TaskPriority.HIGH
            )
            tasks.append(qa_task)
        
        return tasks
    
    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute a workflow with intelligent task scheduling"""
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.active_workflows[workflow_id]
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.utcnow()
        
        try:
            logger.info(f"Starting workflow execution: {workflow_id}")
            
            # Execute tasks based on dependencies
            completed_tasks = set()
            while len(completed_tasks) < len(workflow.tasks):
                # Find ready tasks (no pending dependencies)
                ready_tasks = [
                    task for task in workflow.tasks
                    if (task.status == WorkflowStatus.PENDING and
                        all(dep_id in completed_tasks for dep_id in task.dependencies))
                ]
                
                if not ready_tasks:
                    # Check for circular dependencies or stuck tasks
                    pending_tasks = [t for t in workflow.tasks if t.status == WorkflowStatus.PENDING]
                    if pending_tasks:
                        logger.error(f"Workflow {workflow_id} stuck - possible circular dependencies")
                        workflow.status = WorkflowStatus.FAILED
                        break
                    else:
                        break
                
                # Execute ready tasks in parallel (respecting priority)
                ready_tasks.sort(key=lambda t: t.priority.value, reverse=True)
                await self._execute_tasks_parallel(ready_tasks[:3])  # Max 3 parallel tasks
                
                # Update completed tasks
                for task in ready_tasks:
                    if task.status == WorkflowStatus.COMPLETED:
                        completed_tasks.add(task.id)
            
            # Finalize workflow
            workflow.completed_at = datetime.utcnow()
            workflow.total_processing_time = (
                workflow.completed_at - workflow.started_at
            ).total_seconds()
            
            if all(task.status == WorkflowStatus.COMPLETED for task in workflow.tasks):
                workflow.status = WorkflowStatus.COMPLETED
                self.performance_metrics['successful_workflows'] += 1
            else:
                workflow.status = WorkflowStatus.FAILED
                self.performance_metrics['failed_workflows'] += 1
            
            self.performance_metrics['total_workflows'] += 1
            self._update_performance_metrics(workflow)
            
            logger.info(f"Workflow {workflow_id} completed with status: {workflow.status}")
            
            return {
                'workflow_id': workflow_id,
                'status': workflow.status.value,
                'total_processing_time': workflow.total_processing_time,
                'completed_tasks': len([t for t in workflow.tasks if t.status == WorkflowStatus.COMPLETED]),
                'total_tasks': len(workflow.tasks),
                'results': [task.result for task in workflow.tasks if task.result]
            }
            
        except Exception as e:
            logger.error(f"Error executing workflow {workflow_id}: {str(e)}")
            workflow.status = WorkflowStatus.FAILED
            workflow.completed_at = datetime.utcnow()
            self.performance_metrics['failed_workflows'] += 1
            raise
    
    async def _execute_tasks_parallel(self, tasks: List[WorkflowTask]):
        """Execute multiple tasks in parallel"""
        async def execute_single_task(task: WorkflowTask):
            try:
                task.status = WorkflowStatus.RUNNING
                task.started_at = datetime.utcnow()
                
                # Get appropriate agent
                agent = self.agent_pool.get(task.agent_type)
                if not agent:
                    raise ValueError(f"Agent {task.agent_type} not found")
                
                # Execute task
                result = await agent.process_request(task.input_data)
                
                task.result = result
                task.status = WorkflowStatus.COMPLETED
                task.completed_at = datetime.utcnow()
                task.processing_time = (
                    task.completed_at - task.started_at
                ).total_seconds()
                
                logger.info(f"Task {task.id} completed successfully")
                
            except Exception as e:
                task.error = str(e)
                task.status = WorkflowStatus.FAILED
                task.completed_at = datetime.utcnow()
                logger.error(f"Task {task.id} failed: {str(e)}")
        
        # Execute tasks in parallel
        await asyncio.gather(*[execute_single_task(task) for task in tasks])
    
    def _update_performance_metrics(self, workflow: Workflow):
        """Update performance metrics based on completed workflow"""
        if workflow.total_processing_time:
            current_avg = self.performance_metrics['average_processing_time']
            total_workflows = self.performance_metrics['total_workflows']
            
            # Update rolling average
            self.performance_metrics['average_processing_time'] = (
                (current_avg * (total_workflows - 1) + workflow.total_processing_time) / 
                total_workflows
            )
        
        # Update agent utilization
        for task in workflow.tasks:
            agent_type = task.agent_type
            if agent_type not in self.performance_metrics['agent_utilization']:
                self.performance_metrics['agent_utilization'][agent_type] = {
                    'total_tasks': 0,
                    'successful_tasks': 0,
                    'average_processing_time': 0.0
                }
            
            metrics = self.performance_metrics['agent_utilization'][agent_type]
            metrics['total_tasks'] += 1
            
            if task.status == WorkflowStatus.COMPLETED:
                metrics['successful_tasks'] += 1
                
                if task.processing_time:
                    current_avg = metrics['average_processing_time']
                    total_tasks = metrics['total_tasks']
                    metrics['average_processing_time'] = (
                        (current_avg * (total_tasks - 1) + task.processing_time) / 
                        total_tasks
                    )
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get current status of a workflow"""
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.active_workflows[workflow_id]
        
        return {
            'workflow_id': workflow_id,
            'name': workflow.name,
            'status': workflow.status.value,
            'created_at': workflow.created_at.isoformat(),
            'started_at': workflow.started_at.isoformat() if workflow.started_at else None,
            'completed_at': workflow.completed_at.isoformat() if workflow.completed_at else None,
            'total_processing_time': workflow.total_processing_time,
            'tasks': [
                {
                    'id': task.id,
                    'agent_type': task.agent_type,
                    'status': task.status.value,
                    'processing_time': task.processing_time,
                    'error': task.error
                }
                for task in workflow.tasks
            ]
        }
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow"""
        if workflow_id not in self.active_workflows:
            return False
        
        workflow = self.active_workflows[workflow_id]
        if workflow.status == WorkflowStatus.RUNNING:
            workflow.status = WorkflowStatus.CANCELLED
            workflow.completed_at = datetime.utcnow()
            
            # Cancel running tasks
            for task in workflow.tasks:
                if task.status == WorkflowStatus.RUNNING:
                    task.status = WorkflowStatus.CANCELLED
                    task.completed_at = datetime.utcnow()
            
            logger.info(f"Workflow {workflow_id} cancelled")
            return True
        
        return False
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get orchestrator performance metrics"""
        return {
            'total_workflows': self.performance_metrics['total_workflows'],
            'successful_workflows': self.performance_metrics['successful_workflows'],
            'failed_workflows': self.performance_metrics['failed_workflows'],
            'success_rate': (
                self.performance_metrics['successful_workflows'] / 
                max(1, self.performance_metrics['total_workflows'])
            ) * 100,
            'average_processing_time': self.performance_metrics['average_processing_time'],
            'agent_utilization': self.performance_metrics['agent_utilization'],
            'active_workflows': len([
                w for w in self.active_workflows.values() 
                if w.status == WorkflowStatus.RUNNING
            ])
        }
    
    async def optimize_agent_allocation(self) -> Dict[str, Any]:
        """Analyze and optimize agent allocation based on performance"""
        utilization = self.performance_metrics['agent_utilization']
        
        recommendations = {
            'underutilized_agents': [],
            'overutilized_agents': [],
            'performance_issues': [],
            'optimization_suggestions': []
        }
        
        for agent_type, metrics in utilization.items():
            success_rate = (
                metrics['successful_tasks'] / max(1, metrics['total_tasks'])
            ) * 100
            
            # Identify performance issues
            if success_rate < 90:
                recommendations['performance_issues'].append({
                    'agent': agent_type,
                    'success_rate': success_rate,
                    'issue': 'Low success rate'
                })
            
            if metrics['average_processing_time'] > 30:  # 30 seconds threshold
                recommendations['performance_issues'].append({
                    'agent': agent_type,
                    'processing_time': metrics['average_processing_time'],
                    'issue': 'High processing time'
                })
            
            # Identify utilization patterns
            if metrics['total_tasks'] < 5:  # Low usage threshold
                recommendations['underutilized_agents'].append(agent_type)
            elif metrics['total_tasks'] > 100:  # High usage threshold
                recommendations['overutilized_agents'].append(agent_type)
        
        # Generate optimization suggestions
        if recommendations['overutilized_agents']:
            recommendations['optimization_suggestions'].append(
                "Consider load balancing for overutilized agents"
            )
        
        if recommendations['performance_issues']:
            recommendations['optimization_suggestions'].append(
                "Review and optimize agents with performance issues"
            )
        
        return recommendations

