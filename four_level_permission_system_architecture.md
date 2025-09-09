# 4-Level Permission System Technical Architecture

## Executive Summary

The 4-Level Permission System is the core security and control mechanism for BestSellerSphere's multi-agentic AI writing platform. It provides granular control over AI agent autonomy while ensuring user safety, cost control, and quality assurance. The system seamlessly integrates with CrewAI's agent framework and Microsoft Word's interface.

## System Overview

### Permission Levels Hierarchy

```
Level 1: Assistant Agents (High Human Control)
├── Every action requires explicit approval
├── Real-time suggestions only
└── Maximum safety and control

Level 2: Collaborative Agents (Medium Human Control)
├── Can make direct edits with paragraph-level approval
├── Proactive content generation
└── Balanced autonomy and oversight

Level 3: Semi-Autonomous Agents (Low Human Control)
├── Can write full sections with chapter-level approval
├── Independent research and planning
└── High productivity with milestone oversight

Level 4: Fully Autonomous Agents (Minimal Human Control)
├── Can complete entire documents with project-level approval
├── Full workflow execution
└── Maximum efficiency with strategic oversight
```

## Core Architecture Components

### 1. Permission Engine

```python
# src/permissions/permission_engine.py
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import json

class AutonomyLevel(Enum):
    ASSISTANT = "assistant"           # Level 1
    COLLABORATIVE = "collaborative"   # Level 2
    SEMI_AUTONOMOUS = "semi_autonomous" # Level 3
    FULLY_AUTONOMOUS = "fully_autonomous" # Level 4

class ApprovalScope(Enum):
    ACTION = "action"           # Every individual action
    PARAGRAPH = "paragraph"     # Per paragraph/small section
    SECTION = "section"         # Per section/chapter
    DOCUMENT = "document"       # Per complete document
    PROJECT = "project"         # Per major milestone

class PermissionResult(Enum):
    ALLOWED = "allowed"
    DENIED = "denied"
    REQUIRES_APPROVAL = "requires_approval"
    RATE_LIMITED = "rate_limited"
    COST_LIMITED = "cost_limited"

@dataclass
class AgentPermissions:
    """Comprehensive permission configuration for an agent instance"""
    
    # Core autonomy settings
    autonomy_level: AutonomyLevel
    approval_scope: ApprovalScope
    
    # Capability permissions
    can_write: bool = True
    can_edit: bool = True
    can_delete: bool = False
    can_research: bool = True
    can_generate_images: bool = False
    can_generate_audio: bool = False
    can_access_internet: bool = True
    can_use_external_apis: bool = False
    
    # Content scope permissions
    max_words_per_action: int = 100
    max_words_per_session: int = 1000
    max_words_per_day: int = 5000
    allowed_document_sections: List[str] = None  # None = all sections
    
    # Cost and resource limits
    max_cost_per_action: float = 0.10
    max_cost_per_session: float = 1.00
    max_cost_per_day: float = 10.00
    max_tokens_per_minute: int = 1000
    
    # Time-based restrictions
    session_timeout_minutes: int = 60
    daily_usage_reset_hour: int = 0  # UTC hour for daily reset
    
    # Quality and safety controls
    content_filter_level: str = "moderate"  # strict, moderate, permissive
    require_fact_checking: bool = False
    require_plagiarism_check: bool = False
    require_style_consistency: bool = True
    
    # Approval workflow settings
    approval_timeout_minutes: int = 30
    auto_approve_minor_edits: bool = False
    escalation_threshold: int = 3  # Number of rejections before escalation
    
    # Provider preferences
    preferred_providers: List[str] = None  # None = auto-select
    fallback_providers: List[str] = None
    cost_optimization_enabled: bool = True
    
    # Collaboration settings
    can_see_other_agents: bool = True
    can_coordinate_with_agents: bool = False
    priority_level: int = 1  # 1-10, higher = more priority
    
    # Metadata
    created_at: datetime = None
    updated_at: datetime = None
    created_by: str = None
    last_modified_by: str = None

class PermissionEngine:
    """Core permission evaluation and enforcement engine"""
    
    def __init__(self, db_session, cache_service, audit_service):
        self.db = db_session
        self.cache = cache_service
        self.audit = audit_service
        self.permission_cache_ttl = 300  # 5 minutes
        
        # Permission evaluators for each level
        self.evaluators = {
            AutonomyLevel.ASSISTANT: AssistantLevelEvaluator(),
            AutonomyLevel.COLLABORATIVE: CollaborativeLevelEvaluator(),
            AutonomyLevel.SEMI_AUTONOMOUS: SemiAutonomousLevelEvaluator(),
            AutonomyLevel.FULLY_AUTONOMOUS: FullyAutonomousLevelEvaluator()
        }
    
    async def evaluate_permission(
        self,
        agent_instance_id: str,
        action: AgentAction,
        context: ActionContext
    ) -> PermissionEvaluationResult:
        """Evaluate if agent can perform action"""
        
        # Get agent permissions (with caching)
        permissions = await self.get_agent_permissions(agent_instance_id)
        if not permissions:
            return PermissionEvaluationResult(
                result=PermissionResult.DENIED,
                reason="Agent permissions not found"
            )
        
        # Get appropriate evaluator
        evaluator = self.evaluators[permissions.autonomy_level]
        
        # Perform multi-layer evaluation
        evaluation_result = await evaluator.evaluate(
            permissions, action, context
        )
        
        # Log permission evaluation
        await self.audit.log_permission_evaluation(
            agent_instance_id, action, evaluation_result
        )
        
        return evaluation_result
    
    async def get_agent_permissions(self, agent_instance_id: str) -> Optional[AgentPermissions]:
        """Get agent permissions with caching"""
        
        cache_key = f"permissions:{agent_instance_id}"
        
        # Try cache first
        cached_permissions = await self.cache.get(cache_key)
        if cached_permissions:
            return AgentPermissions(**json.loads(cached_permissions))
        
        # Load from database
        query = """
        SELECT permissions, updated_at 
        FROM agent_instances 
        WHERE id = %s
        """
        
        result = await self.db.execute(query, (agent_instance_id,))
        row = result.fetchone()
        
        if not row:
            return None
        
        permissions = AgentPermissions(**json.loads(row.permissions))
        
        # Cache permissions
        await self.cache.set(
            cache_key, 
            json.dumps(permissions.__dict__, default=str),
            ttl=self.permission_cache_ttl
        )
        
        return permissions
    
    async def update_agent_permissions(
        self,
        agent_instance_id: str,
        new_permissions: AgentPermissions,
        updated_by: str
    ) -> bool:
        """Update agent permissions"""
        
        # Validate permissions
        validation_result = await self.validate_permissions(new_permissions)
        if not validation_result.valid:
            raise ValueError(f"Invalid permissions: {validation_result.errors}")
        
        # Update database
        new_permissions.updated_at = datetime.utcnow()
        new_permissions.last_modified_by = updated_by
        
        query = """
        UPDATE agent_instances 
        SET permissions = %s, updated_at = %s 
        WHERE id = %s
        """
        
        await self.db.execute(
            query,
            (json.dumps(new_permissions.__dict__, default=str), 
             new_permissions.updated_at, 
             agent_instance_id)
        )
        
        # Invalidate cache
        cache_key = f"permissions:{agent_instance_id}"
        await self.cache.delete(cache_key)
        
        # Log permission change
        await self.audit.log_permission_change(
            agent_instance_id, new_permissions, updated_by
        )
        
        return True

@dataclass
class AgentAction:
    """Represents an action an agent wants to perform"""
    
    action_type: str  # write, edit, delete, research, generate_image, etc.
    target_type: str  # document, paragraph, sentence, word
    target_id: str    # ID of the target (document_id, paragraph_id, etc.)
    
    # Content details
    content: Optional[str] = None
    content_length: int = 0
    estimated_tokens: int = 0
    estimated_cost: float = 0.0
    
    # Position and scope
    position: Optional[int] = None
    length: Optional[int] = None
    scope: Optional[str] = None  # paragraph, section, chapter, document
    
    # Provider and model
    provider: Optional[str] = None
    model: Optional[str] = None
    
    # Quality and safety
    content_category: Optional[str] = None  # creative, technical, research, etc.
    safety_level: Optional[str] = None
    
    # Timing
    requested_at: datetime = None
    deadline: Optional[datetime] = None
    
    # Context
    user_initiated: bool = False
    workflow_step: Optional[str] = None
    dependencies: List[str] = None

@dataclass
class ActionContext:
    """Context information for permission evaluation"""
    
    # User context
    user_id: str
    user_subscription_tier: str
    user_permissions: Dict[str, Any]
    
    # Document context
    document_id: str
    document_type: str
    document_size: int
    document_collaborators: List[str]
    
    # Session context
    session_id: str
    session_start_time: datetime
    session_actions_count: int
    session_words_generated: int
    session_cost_incurred: float
    
    # Daily usage context
    daily_actions_count: int
    daily_words_generated: int
    daily_cost_incurred: float
    
    # Real-time context
    current_time: datetime
    system_load: float
    provider_availability: Dict[str, bool]
    
    # Quality context
    recent_approval_rate: float
    recent_quality_scores: List[float]
    recent_user_feedback: List[str]

@dataclass
class PermissionEvaluationResult:
    """Result of permission evaluation"""
    
    result: PermissionResult
    reason: str
    
    # Approval details (if requires approval)
    approval_required: bool = False
    approval_scope: Optional[ApprovalScope] = None
    approval_timeout: Optional[int] = None
    
    # Modifications (if action needs to be modified)
    suggested_modifications: Optional[Dict[str, Any]] = None
    
    # Rate limiting (if rate limited)
    retry_after_seconds: Optional[int] = None
    
    # Cost information
    estimated_cost: float = 0.0
    remaining_budget: float = 0.0
    
    # Quality requirements
    quality_checks_required: List[str] = None
    
    # Metadata
    evaluation_time_ms: float = 0.0
    evaluator_version: str = "1.0"
```

### 2. Level-Specific Evaluators

```python
# src/permissions/level_evaluators.py

class BaseLevelEvaluator:
    """Base class for permission level evaluators"""
    
    async def evaluate(
        self,
        permissions: AgentPermissions,
        action: AgentAction,
        context: ActionContext
    ) -> PermissionEvaluationResult:
        """Evaluate permission for action"""
        
        # Common checks across all levels
        basic_checks = await self.perform_basic_checks(permissions, action, context)
        if basic_checks.result != PermissionResult.ALLOWED:
            return basic_checks
        
        # Level-specific evaluation
        return await self.evaluate_level_specific(permissions, action, context)
    
    async def perform_basic_checks(
        self,
        permissions: AgentPermissions,
        action: AgentAction,
        context: ActionContext
    ) -> PermissionEvaluationResult:
        """Perform basic checks common to all levels"""
        
        # Check capability permissions
        if not self.check_capability_permission(permissions, action):
            return PermissionEvaluationResult(
                result=PermissionResult.DENIED,
                reason=f"Agent not permitted to perform {action.action_type}"
            )
        
        # Check resource limits
        resource_check = await self.check_resource_limits(permissions, action, context)
        if resource_check.result != PermissionResult.ALLOWED:
            return resource_check
        
        # Check cost limits
        cost_check = await self.check_cost_limits(permissions, action, context)
        if cost_check.result != PermissionResult.ALLOWED:
            return cost_check
        
        # Check time restrictions
        time_check = await self.check_time_restrictions(permissions, action, context)
        if time_check.result != PermissionResult.ALLOWED:
            return time_check
        
        return PermissionEvaluationResult(
            result=PermissionResult.ALLOWED,
            reason="Basic checks passed"
        )
    
    def check_capability_permission(
        self,
        permissions: AgentPermissions,
        action: AgentAction
    ) -> bool:
        """Check if agent has capability to perform action"""
        
        capability_map = {
            'write': permissions.can_write,
            'edit': permissions.can_edit,
            'delete': permissions.can_delete,
            'research': permissions.can_research,
            'generate_image': permissions.can_generate_images,
            'generate_audio': permissions.can_generate_audio
        }
        
        return capability_map.get(action.action_type, False)
    
    async def check_resource_limits(
        self,
        permissions: AgentPermissions,
        action: AgentAction,
        context: ActionContext
    ) -> PermissionEvaluationResult:
        """Check resource usage limits"""
        
        # Check words per action
        if action.content_length > permissions.max_words_per_action:
            return PermissionEvaluationResult(
                result=PermissionResult.DENIED,
                reason=f"Action exceeds word limit ({action.content_length} > {permissions.max_words_per_action})"
            )
        
        # Check session limits
        if (context.session_words_generated + action.content_length) > permissions.max_words_per_session:
            return PermissionEvaluationResult(
                result=PermissionResult.RATE_LIMITED,
                reason="Session word limit would be exceeded",
                retry_after_seconds=3600  # Retry after 1 hour
            )
        
        # Check daily limits
        if (context.daily_words_generated + action.content_length) > permissions.max_words_per_day:
            return PermissionEvaluationResult(
                result=PermissionResult.RATE_LIMITED,
                reason="Daily word limit would be exceeded",
                retry_after_seconds=86400  # Retry after 24 hours
            )
        
        return PermissionEvaluationResult(
            result=PermissionResult.ALLOWED,
            reason="Resource limits OK"
        )
    
    async def check_cost_limits(
        self,
        permissions: AgentPermissions,
        action: AgentAction,
        context: ActionContext
    ) -> PermissionEvaluationResult:
        """Check cost limits"""
        
        # Check cost per action
        if action.estimated_cost > permissions.max_cost_per_action:
            return PermissionEvaluationResult(
                result=PermissionResult.DENIED,
                reason=f"Action cost too high (${action.estimated_cost} > ${permissions.max_cost_per_action})"
            )
        
        # Check session cost
        if (context.session_cost_incurred + action.estimated_cost) > permissions.max_cost_per_session:
            return PermissionEvaluationResult(
                result=PermissionResult.COST_LIMITED,
                reason="Session cost limit would be exceeded",
                remaining_budget=permissions.max_cost_per_session - context.session_cost_incurred
            )
        
        # Check daily cost
        if (context.daily_cost_incurred + action.estimated_cost) > permissions.max_cost_per_day:
            return PermissionEvaluationResult(
                result=PermissionResult.COST_LIMITED,
                reason="Daily cost limit would be exceeded",
                remaining_budget=permissions.max_cost_per_day - context.daily_cost_incurred
            )
        
        return PermissionEvaluationResult(
            result=PermissionResult.ALLOWED,
            reason="Cost limits OK"
        )

class AssistantLevelEvaluator(BaseLevelEvaluator):
    """Level 1: Assistant Agents - High Human Control"""
    
    async def evaluate_level_specific(
        self,
        permissions: AgentPermissions,
        action: AgentAction,
        context: ActionContext
    ) -> PermissionEvaluationResult:
        """Assistant level requires approval for ALL actions"""
        
        # Assistant level ALWAYS requires approval
        return PermissionEvaluationResult(
            result=PermissionResult.REQUIRES_APPROVAL,
            reason="Assistant level requires approval for all actions",
            approval_required=True,
            approval_scope=ApprovalScope.ACTION,
            approval_timeout=permissions.approval_timeout_minutes
        )

class CollaborativeLevelEvaluator(BaseLevelEvaluator):
    """Level 2: Collaborative Agents - Medium Human Control"""
    
    async def evaluate_level_specific(
        self,
        permissions: AgentPermissions,
        action: AgentAction,
        context: ActionContext
    ) -> PermissionEvaluationResult:
        """Collaborative level allows some actions, requires approval for others"""
        
        # Auto-approve minor edits if enabled
        if (permissions.auto_approve_minor_edits and 
            action.action_type == 'edit' and 
            action.content_length <= 50):
            
            return PermissionEvaluationResult(
                result=PermissionResult.ALLOWED,
                reason="Minor edit auto-approved"
            )
        
        # Auto-approve research actions
        if action.action_type == 'research':
            return PermissionEvaluationResult(
                result=PermissionResult.ALLOWED,
                reason="Research action auto-approved"
            )
        
        # Require approval for content generation/modification
        if action.action_type in ['write', 'edit', 'delete']:
            return PermissionEvaluationResult(
                result=PermissionResult.REQUIRES_APPROVAL,
                reason="Content modification requires approval",
                approval_required=True,
                approval_scope=ApprovalScope.PARAGRAPH,
                approval_timeout=permissions.approval_timeout_minutes
            )
        
        # Allow other actions
        return PermissionEvaluationResult(
            result=PermissionResult.ALLOWED,
            reason="Action allowed at collaborative level"
        )

class SemiAutonomousLevelEvaluator(BaseLevelEvaluator):
    """Level 3: Semi-Autonomous Agents - Low Human Control"""
    
    async def evaluate_level_specific(
        self,
        permissions: AgentPermissions,
        action: AgentAction,
        context: ActionContext
    ) -> PermissionEvaluationResult:
        """Semi-autonomous level allows most actions, requires approval for major changes"""
        
        # Auto-approve small to medium content changes
        if (action.action_type in ['write', 'edit'] and 
            action.content_length <= 500):
            
            return PermissionEvaluationResult(
                result=PermissionResult.ALLOWED,
                reason="Small content change auto-approved"
            )
        
        # Auto-approve research and media generation
        if action.action_type in ['research', 'generate_image', 'generate_audio']:
            return PermissionEvaluationResult(
                result=PermissionResult.ALLOWED,
                reason="Research/media action auto-approved"
            )
        
        # Require approval for large content changes
        if (action.action_type in ['write', 'edit'] and 
            action.content_length > 500):
            
            return PermissionEvaluationResult(
                result=PermissionResult.REQUIRES_APPROVAL,
                reason="Large content change requires approval",
                approval_required=True,
                approval_scope=ApprovalScope.SECTION,
                approval_timeout=permissions.approval_timeout_minutes
            )
        
        # Require approval for deletions
        if action.action_type == 'delete':
            return PermissionEvaluationResult(
                result=PermissionResult.REQUIRES_APPROVAL,
                reason="Deletion requires approval",
                approval_required=True,
                approval_scope=ApprovalScope.ACTION,
                approval_timeout=permissions.approval_timeout_minutes
            )
        
        # Allow other actions
        return PermissionEvaluationResult(
            result=PermissionResult.ALLOWED,
            reason="Action allowed at semi-autonomous level"
        )

class FullyAutonomousLevelEvaluator(BaseLevelEvaluator):
    """Level 4: Fully Autonomous Agents - Minimal Human Control"""
    
    async def evaluate_level_specific(
        self,
        permissions: AgentPermissions,
        action: AgentAction,
        context: ActionContext
    ) -> PermissionEvaluationResult:
        """Fully autonomous level allows most actions with minimal oversight"""
        
        # Auto-approve most content operations
        if action.action_type in ['write', 'edit', 'research', 'generate_image', 'generate_audio']:
            return PermissionEvaluationResult(
                result=PermissionResult.ALLOWED,
                reason="Action auto-approved at autonomous level"
            )
        
        # Require approval only for major structural changes
        if (action.action_type == 'delete' and 
            action.scope in ['chapter', 'document']):
            
            return PermissionEvaluationResult(
                result=PermissionResult.REQUIRES_APPROVAL,
                reason="Major deletion requires approval",
                approval_required=True,
                approval_scope=ApprovalScope.DOCUMENT,
                approval_timeout=permissions.approval_timeout_minutes
            )
        
        # Require approval for external API access
        if (action.action_type == 'external_api' and 
            not permissions.can_use_external_apis):
            
            return PermissionEvaluationResult(
                result=PermissionResult.REQUIRES_APPROVAL,
                reason="External API access requires approval",
                approval_required=True,
                approval_scope=ApprovalScope.ACTION,
                approval_timeout=permissions.approval_timeout_minutes
            )
        
        # Allow all other actions
        return PermissionEvaluationResult(
            result=PermissionResult.ALLOWED,
            reason="Action allowed at fully autonomous level"
        )
```

### 3. Approval Workflow System

```python
# src/permissions/approval_workflow.py

class ApprovalWorkflowManager:
    """Manages approval workflows for agent actions"""
    
    def __init__(self, db_session, websocket_manager, notification_service):
        self.db = db_session
        self.websocket = websocket_manager
        self.notifications = notification_service
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        
    async def request_approval(
        self,
        agent_instance_id: str,
        action: AgentAction,
        approval_scope: ApprovalScope,
        timeout_minutes: int = 30
    ) -> str:
        """Request approval for agent action"""
        
        # Create approval request
        approval_request = ApprovalRequest(
            id=str(uuid.uuid4()),
            agent_instance_id=agent_instance_id,
            action=action,
            approval_scope=approval_scope,
            requested_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=timeout_minutes),
            status=ApprovalStatus.PENDING
        )
        
        # Store in database
        await self.store_approval_request(approval_request)
        
        # Add to pending approvals
        self.pending_approvals[approval_request.id] = approval_request
        
        # Send real-time notification to user
        await self.send_approval_notification(approval_request)
        
        # Set up timeout handler
        asyncio.create_task(
            self.handle_approval_timeout(approval_request.id, timeout_minutes)
        )
        
        return approval_request.id
    
    async def respond_to_approval(
        self,
        approval_id: str,
        user_id: str,
        approved: bool,
        feedback: Optional[str] = None
    ) -> ApprovalResponse:
        """Respond to approval request"""
        
        # Get approval request
        approval_request = await self.get_approval_request(approval_id)
        if not approval_request:
            raise ValueError(f"Approval request {approval_id} not found")
        
        # Check if already responded
        if approval_request.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval request already {approval_request.status}")
        
        # Check if expired
        if datetime.utcnow() > approval_request.expires_at:
            raise ValueError("Approval request has expired")
        
        # Create response
        response = ApprovalResponse(
            approval_id=approval_id,
            user_id=user_id,
            approved=approved,
            feedback=feedback,
            responded_at=datetime.utcnow()
        )
        
        # Update approval request
        approval_request.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        approval_request.response = response
        
        # Store response
        await self.store_approval_response(approval_request)
        
        # Remove from pending
        if approval_id in self.pending_approvals:
            del self.pending_approvals[approval_id]
        
        # Notify agent of response
        await self.notify_agent_of_response(approval_request)
        
        return response
    
    async def send_approval_notification(self, approval_request: ApprovalRequest):
        """Send approval notification to user"""
        
        # Get agent info
        agent_info = await self.get_agent_info(approval_request.agent_instance_id)
        
        # Create notification
        notification = {
            'type': 'approval_request',
            'approval_id': approval_request.id,
            'agent_name': agent_info.display_name,
            'action_type': approval_request.action.action_type,
            'action_description': self.format_action_description(approval_request.action),
            'approval_scope': approval_request.approval_scope.value,
            'expires_at': approval_request.expires_at.isoformat(),
            'estimated_cost': approval_request.action.estimated_cost
        }
        
        # Send via WebSocket
        await self.websocket.send_personal_message(
            agent_info.user_id, notification
        )
        
        # Send push notification if enabled
        await self.notifications.send_push_notification(
            agent_info.user_id,
            f"Agent {agent_info.display_name} needs approval",
            f"Wants to {approval_request.action.action_type} content"
        )
    
    def format_action_description(self, action: AgentAction) -> str:
        """Format action for user-friendly description"""
        
        descriptions = {
            'write': f"Write {action.content_length} words",
            'edit': f"Edit {action.content_length} words",
            'delete': f"Delete content at position {action.position}",
            'research': f"Research {action.content[:50]}...",
            'generate_image': f"Generate image: {action.content[:50]}...",
            'generate_audio': f"Generate audio: {action.content[:50]}..."
        }
        
        return descriptions.get(action.action_type, f"Perform {action.action_type}")
    
    async def handle_approval_timeout(self, approval_id: str, timeout_minutes: int):
        """Handle approval timeout"""
        
        await asyncio.sleep(timeout_minutes * 60)
        
        # Check if still pending
        if approval_id in self.pending_approvals:
            approval_request = self.pending_approvals[approval_id]
            
            # Mark as expired
            approval_request.status = ApprovalStatus.EXPIRED
            
            # Store update
            await self.store_approval_response(approval_request)
            
            # Remove from pending
            del self.pending_approvals[approval_id]
            
            # Notify agent of timeout
            await self.notify_agent_of_response(approval_request)

@dataclass
class ApprovalRequest:
    """Represents an approval request"""
    
    id: str
    agent_instance_id: str
    action: AgentAction
    approval_scope: ApprovalScope
    requested_at: datetime
    expires_at: datetime
    status: 'ApprovalStatus'
    response: Optional['ApprovalResponse'] = None

@dataclass
class ApprovalResponse:
    """Represents an approval response"""
    
    approval_id: str
    user_id: str
    approved: bool
    feedback: Optional[str]
    responded_at: datetime

class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
```

### 4. Real-Time Permission Updates

```python
# src/permissions/real_time_updates.py

class RealTimePermissionManager:
    """Manages real-time permission updates and notifications"""
    
    def __init__(self, permission_engine, websocket_manager):
        self.permission_engine = permission_engine
        self.websocket = websocket_manager
        self.active_sessions: Dict[str, Set[str]] = {}  # user_id -> set of agent_instance_ids
    
    async def register_agent_session(self, user_id: str, agent_instance_id: str):
        """Register active agent session"""
        
        if user_id not in self.active_sessions:
            self.active_sessions[user_id] = set()
        
        self.active_sessions[user_id].add(agent_instance_id)
        
        # Send current permission status
        await self.send_permission_status(user_id, agent_instance_id)
    
    async def unregister_agent_session(self, user_id: str, agent_instance_id: str):
        """Unregister agent session"""
        
        if user_id in self.active_sessions:
            self.active_sessions[user_id].discard(agent_instance_id)
            
            if not self.active_sessions[user_id]:
                del self.active_sessions[user_id]
    
    async def update_permissions_real_time(
        self,
        agent_instance_id: str,
        new_permissions: AgentPermissions,
        updated_by: str
    ):
        """Update permissions and notify in real-time"""
        
        # Update permissions
        await self.permission_engine.update_agent_permissions(
            agent_instance_id, new_permissions, updated_by
        )
        
        # Find affected users
        affected_users = []
        for user_id, agent_ids in self.active_sessions.items():
            if agent_instance_id in agent_ids:
                affected_users.append(user_id)
        
        # Send updates to affected users
        for user_id in affected_users:
            await self.send_permission_update(user_id, agent_instance_id, new_permissions)
    
    async def send_permission_status(self, user_id: str, agent_instance_id: str):
        """Send current permission status to user"""
        
        permissions = await self.permission_engine.get_agent_permissions(agent_instance_id)
        if not permissions:
            return
        
        status_message = {
            'type': 'permission_status',
            'agent_instance_id': agent_instance_id,
            'autonomy_level': permissions.autonomy_level.value,
            'approval_scope': permissions.approval_scope.value,
            'capabilities': {
                'can_write': permissions.can_write,
                'can_edit': permissions.can_edit,
                'can_delete': permissions.can_delete,
                'can_research': permissions.can_research,
                'can_generate_images': permissions.can_generate_images,
                'can_generate_audio': permissions.can_generate_audio
            },
            'limits': {
                'max_words_per_action': permissions.max_words_per_action,
                'max_words_per_session': permissions.max_words_per_session,
                'max_cost_per_action': permissions.max_cost_per_action,
                'max_cost_per_session': permissions.max_cost_per_session
            }
        }
        
        await self.websocket.send_personal_message(user_id, status_message)
    
    async def send_permission_update(
        self,
        user_id: str,
        agent_instance_id: str,
        new_permissions: AgentPermissions
    ):
        """Send permission update notification"""
        
        update_message = {
            'type': 'permission_update',
            'agent_instance_id': agent_instance_id,
            'updated_at': new_permissions.updated_at.isoformat(),
            'updated_by': new_permissions.last_modified_by,
            'changes': {
                'autonomy_level': new_permissions.autonomy_level.value,
                'approval_scope': new_permissions.approval_scope.value,
                'capabilities': {
                    'can_write': new_permissions.can_write,
                    'can_edit': new_permissions.can_edit,
                    'can_delete': new_permissions.can_delete,
                    'can_research': new_permissions.can_research,
                    'can_generate_images': new_permissions.can_generate_images,
                    'can_generate_audio': new_permissions.can_generate_audio
                }
            }
        }
        
        await self.websocket.send_personal_message(user_id, update_message)
    
    async def broadcast_permission_violation(
        self,
        user_id: str,
        agent_instance_id: str,
        violation: PermissionViolation
    ):
        """Broadcast permission violation to user"""
        
        violation_message = {
            'type': 'permission_violation',
            'agent_instance_id': agent_instance_id,
            'violation_type': violation.violation_type,
            'action_attempted': violation.action_attempted,
            'reason': violation.reason,
            'timestamp': violation.timestamp.isoformat(),
            'suggested_action': violation.suggested_action
        }
        
        await self.websocket.send_personal_message(user_id, violation_message)

@dataclass
class PermissionViolation:
    """Represents a permission violation"""
    
    violation_type: str  # denied, rate_limited, cost_limited
    action_attempted: str
    reason: str
    timestamp: datetime
    suggested_action: str
```

### 5. Word Add-in Integration

```typescript
// src/word-integration/permission-interface.ts

export interface PermissionControlPanel {
    agentInstanceId: string;
    currentPermissions: AgentPermissions;
    onPermissionChange: (newPermissions: AgentPermissions) => void;
}

export class WordPermissionManager {
    private websocketService: WebSocketService;
    private permissionService: PermissionService;
    private approvalInterface: ApprovalInterface;
    
    constructor() {
        this.websocketService = new WebSocketService();
        this.permissionService = new PermissionService();
        this.approvalInterface = new ApprovalInterface();
        
        this.setupWebSocketListeners();
    }
    
    private setupWebSocketListeners(): void {
        // Listen for approval requests
        this.websocketService.on('approval_request', (request: ApprovalRequest) => {
            this.handleApprovalRequest(request);
        });
        
        // Listen for permission updates
        this.websocketService.on('permission_update', (update: PermissionUpdate) => {
            this.handlePermissionUpdate(update);
        });
        
        // Listen for permission violations
        this.websocketService.on('permission_violation', (violation: PermissionViolation) => {
            this.handlePermissionViolation(violation);
        });
    }
    
    async updateAgentPermissions(
        agentInstanceId: string,
        newPermissions: Partial<AgentPermissions>
    ): Promise<void> {
        try {
            await this.permissionService.updatePermissions(agentInstanceId, newPermissions);
            
            // Show success notification in Word
            await this.showWordNotification(
                'Permissions updated successfully',
                'success'
            );
        } catch (error) {
            await this.showWordNotification(
                `Failed to update permissions: ${error.message}`,
                'error'
            );
        }
    }
    
    private async handleApprovalRequest(request: ApprovalRequest): Promise<void> {
        // Show approval dialog in Word task pane
        const approved = await this.approvalInterface.showApprovalDialog(request);
        
        // Send response
        await this.permissionService.respondToApproval(
            request.id,
            approved,
            null // feedback
        );
    }
    
    private async handlePermissionUpdate(update: PermissionUpdate): Promise<void> {
        // Update UI to reflect new permissions
        await this.updatePermissionUI(update.agentInstanceId, update.changes);
        
        // Show notification
        await this.showWordNotification(
            `Agent permissions updated by ${update.updatedBy}`,
            'info'
        );
    }
    
    private async handlePermissionViolation(violation: PermissionViolation): Promise<void> {
        // Show violation notification
        await this.showWordNotification(
            `Permission denied: ${violation.reason}`,
            'warning'
        );
        
        // Suggest corrective action
        if (violation.suggestedAction) {
            await this.showWordNotification(
                `Suggestion: ${violation.suggestedAction}`,
                'info'
            );
        }
    }
    
    private async showWordNotification(
        message: string,
        type: 'success' | 'error' | 'warning' | 'info'
    ): Promise<void> {
        return Word.run(async (context) => {
            // Use Word's notification system
            Office.addin.showAsTaskpane({
                message: message,
                type: type,
                timeout: 5000
            });
        });
    }
    
    private async updatePermissionUI(
        agentInstanceId: string,
        changes: Partial<AgentPermissions>
    ): Promise<void> {
        // Update the permission control panel in the task pane
        const controlPanel = document.getElementById(`permission-panel-${agentInstanceId}`);
        if (controlPanel) {
            // Update UI elements to reflect new permissions
            this.renderPermissionChanges(controlPanel, changes);
        }
    }
    
    private renderPermissionChanges(
        panel: HTMLElement,
        changes: Partial<AgentPermissions>
    ): void {
        // Update autonomy level display
        if (changes.autonomyLevel) {
            const autonomyDisplay = panel.querySelector('.autonomy-level');
            if (autonomyDisplay) {
                autonomyDisplay.textContent = this.formatAutonomyLevel(changes.autonomyLevel);
                autonomyDisplay.className = `autonomy-level level-${changes.autonomyLevel}`;
            }
        }
        
        // Update capability toggles
        if (changes.capabilities) {
            Object.entries(changes.capabilities).forEach(([capability, enabled]) => {
                const toggle = panel.querySelector(`[data-capability="${capability}"]`) as HTMLInputElement;
                if (toggle) {
                    toggle.checked = enabled;
                    toggle.disabled = !this.canUserModifyCapability(capability);
                }
            });
        }
        
        // Update limit displays
        if (changes.limits) {
            Object.entries(changes.limits).forEach(([limit, value]) => {
                const display = panel.querySelector(`[data-limit="${limit}"]`);
                if (display) {
                    display.textContent = this.formatLimitValue(limit, value);
                }
            });
        }
    }
    
    private formatAutonomyLevel(level: string): string {
        const levelNames = {
            'assistant': 'Assistant (High Control)',
            'collaborative': 'Collaborative (Medium Control)',
            'semi_autonomous': 'Semi-Autonomous (Low Control)',
            'fully_autonomous': 'Fully Autonomous (Minimal Control)'
        };
        
        return levelNames[level] || level;
    }
    
    private canUserModifyCapability(capability: string): boolean {
        // Check if user has permission to modify this capability
        // This would be based on user role and subscription tier
        return true; // Simplified for example
    }
    
    private formatLimitValue(limit: string, value: any): string {
        if (limit.includes('cost')) {
            return `$${value.toFixed(2)}`;
        } else if (limit.includes('words')) {
            return `${value.toLocaleString()} words`;
        } else {
            return String(value);
        }
    }
}

// React component for permission control panel
export const PermissionControlPanel: React.FC<PermissionControlPanelProps> = ({
    agentInstanceId,
    currentPermissions,
    onPermissionChange
}) => {
    const [permissions, setPermissions] = useState<AgentPermissions>(currentPermissions);
    const [isUpdating, setIsUpdating] = useState(false);
    
    const handleAutonomyLevelChange = async (newLevel: AutonomyLevel) => {
        setIsUpdating(true);
        
        try {
            const updatedPermissions = {
                ...permissions,
                autonomyLevel: newLevel,
                approvalScope: getDefaultApprovalScope(newLevel)
            };
            
            await onPermissionChange(updatedPermissions);
            setPermissions(updatedPermissions);
        } catch (error) {
            console.error('Failed to update autonomy level:', error);
        } finally {
            setIsUpdating(false);
        }
    };
    
    const handleCapabilityToggle = async (capability: string, enabled: boolean) => {
        setIsUpdating(true);
        
        try {
            const updatedPermissions = {
                ...permissions,
                [capability]: enabled
            };
            
            await onPermissionChange(updatedPermissions);
            setPermissions(updatedPermissions);
        } catch (error) {
            console.error('Failed to update capability:', error);
        } finally {
            setIsUpdating(false);
        }
    };
    
    const handleLimitChange = async (limit: string, value: number) => {
        setIsUpdating(true);
        
        try {
            const updatedPermissions = {
                ...permissions,
                [limit]: value
            };
            
            await onPermissionChange(updatedPermissions);
            setPermissions(updatedPermissions);
        } catch (error) {
            console.error('Failed to update limit:', error);
        } finally {
            setIsUpdating(false);
        }
    };
    
    return (
        <div className="permission-control-panel">
            <h3>Agent Permissions</h3>
            
            {/* Autonomy Level Selector */}
            <div className="permission-section">
                <label>Autonomy Level</label>
                <select
                    value={permissions.autonomyLevel}
                    onChange={(e) => handleAutonomyLevelChange(e.target.value as AutonomyLevel)}
                    disabled={isUpdating}
                >
                    <option value="assistant">Assistant (High Control)</option>
                    <option value="collaborative">Collaborative (Medium Control)</option>
                    <option value="semi_autonomous">Semi-Autonomous (Low Control)</option>
                    <option value="fully_autonomous">Fully Autonomous (Minimal Control)</option>
                </select>
            </div>
            
            {/* Capability Toggles */}
            <div className="permission-section">
                <label>Capabilities</label>
                <div className="capability-toggles">
                    {Object.entries(permissions.capabilities || {}).map(([capability, enabled]) => (
                        <div key={capability} className="capability-toggle">
                            <input
                                type="checkbox"
                                id={`capability-${capability}`}
                                checked={enabled}
                                onChange={(e) => handleCapabilityToggle(capability, e.target.checked)}
                                disabled={isUpdating}
                            />
                            <label htmlFor={`capability-${capability}`}>
                                {formatCapabilityName(capability)}
                            </label>
                        </div>
                    ))}
                </div>
            </div>
            
            {/* Usage Limits */}
            <div className="permission-section">
                <label>Usage Limits</label>
                <div className="limit-controls">
                    <div className="limit-control">
                        <label>Max Words per Action</label>
                        <input
                            type="number"
                            value={permissions.maxWordsPerAction}
                            onChange={(e) => handleLimitChange('maxWordsPerAction', parseInt(e.target.value))}
                            disabled={isUpdating}
                            min="1"
                            max="10000"
                        />
                    </div>
                    
                    <div className="limit-control">
                        <label>Max Cost per Action</label>
                        <input
                            type="number"
                            step="0.01"
                            value={permissions.maxCostPerAction}
                            onChange={(e) => handleLimitChange('maxCostPerAction', parseFloat(e.target.value))}
                            disabled={isUpdating}
                            min="0.01"
                            max="10.00"
                        />
                    </div>
                </div>
            </div>
            
            {/* Status Indicator */}
            <div className="permission-status">
                <div className={`status-indicator ${permissions.autonomyLevel}`}>
                    {formatAutonomyLevel(permissions.autonomyLevel)}
                </div>
                {isUpdating && <div className="updating-indicator">Updating...</div>}
            </div>
        </div>
    );
};

function getDefaultApprovalScope(autonomyLevel: AutonomyLevel): ApprovalScope {
    const scopeMap = {
        'assistant': 'action',
        'collaborative': 'paragraph',
        'semi_autonomous': 'section',
        'fully_autonomous': 'document'
    };
    
    return scopeMap[autonomyLevel] || 'action';
}

function formatCapabilityName(capability: string): string {
    return capability
        .replace(/([A-Z])/g, ' $1')
        .replace(/^./, str => str.toUpperCase())
        .replace('Can ', '');
}
```

## Integration Points

### 1. CrewAI Integration

The permission system integrates with CrewAI through custom agent wrappers:

```python
# src/agents/bestsellersphere_agent.py
from crewai import Agent
from typing import Optional

class BestSellerSphereAgent(Agent):
    """Custom CrewAI agent with permission system integration"""
    
    def __init__(
        self,
        role: str,
        goal: str,
        backstory: str,
        permission_manager: PermissionEngine,
        agent_instance_id: str,
        **kwargs
    ):
        super().__init__(role=role, goal=goal, backstory=backstory, **kwargs)
        self.permission_manager = permission_manager
        self.agent_instance_id = agent_instance_id
    
    async def execute_task(self, task: Task) -> TaskResult:
        """Execute task with permission checking"""
        
        # Convert task to action
        action = self.task_to_action(task)
        
        # Check permissions
        permission_result = await self.permission_manager.evaluate_permission(
            self.agent_instance_id,
            action,
            self.get_current_context()
        )
        
        if permission_result.result == PermissionResult.DENIED:
            return TaskResult(
                success=False,
                error=permission_result.reason
            )
        
        elif permission_result.result == PermissionResult.REQUIRES_APPROVAL:
            # Request approval and wait
            approval_id = await self.request_approval(action, permission_result)
            approval_response = await self.wait_for_approval(approval_id)
            
            if not approval_response.approved:
                return TaskResult(
                    success=False,
                    error=f"Action rejected: {approval_response.feedback}"
                )
        
        # Execute the task
        return await super().execute_task(task)
```

### 2. Database Schema

```sql
-- Agent instances with permissions
CREATE TABLE agent_instances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    agent_id VARCHAR(100) NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    permissions JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Approval requests
CREATE TABLE approval_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_instance_id UUID NOT NULL REFERENCES agent_instances(id),
    action_data JSONB NOT NULL,
    approval_scope VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    requested_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    response_data JSONB,
    responded_at TIMESTAMP
);

-- Permission audit log
CREATE TABLE permission_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_instance_id UUID NOT NULL REFERENCES agent_instances(id),
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB NOT NULL,
    user_id UUID REFERENCES users(id),
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_agent_instances_user_id ON agent_instances(user_id);
CREATE INDEX idx_approval_requests_status ON approval_requests(status);
CREATE INDEX idx_approval_requests_expires_at ON approval_requests(expires_at);
CREATE INDEX idx_permission_audit_log_timestamp ON permission_audit_log(timestamp);
```

## Security Considerations

### 1. Permission Escalation Prevention

- **Immutable Core Permissions**: Certain permissions cannot be modified by users
- **Role-Based Restrictions**: User roles limit which permissions can be changed
- **Audit Trail**: All permission changes are logged with user attribution
- **Time-Based Restrictions**: Permissions can have expiration dates

### 2. Cost Protection

- **Multi-Level Budgets**: Action, session, daily, and monthly cost limits
- **Real-Time Monitoring**: Continuous cost tracking with immediate cutoffs
- **Provider Failover**: Automatic switching to cheaper providers when limits approached
- **Usage Alerts**: Proactive notifications before limits are reached

### 3. Content Safety

- **Content Filtering**: All generated content passes through safety filters
- **Plagiarism Detection**: Optional plagiarism checking for generated content
- **Fact Verification**: Optional fact-checking for research-based content
- **Version Control**: All changes are tracked and can be reverted

## Performance Optimizations

### 1. Caching Strategy

- **Permission Caching**: Frequently accessed permissions cached for 5 minutes
- **Evaluation Caching**: Similar action evaluations cached for 1 hour
- **User Context Caching**: User session data cached for session duration

### 2. Asynchronous Processing

- **Non-Blocking Evaluations**: Permission checks don't block agent execution
- **Background Approval Processing**: Approval workflows run in background
- **Batch Permission Updates**: Multiple permission changes batched together

### 3. Database Optimization

- **Indexed Queries**: All permission queries use optimized indexes
- **Connection Pooling**: Database connections pooled for efficiency
- **Read Replicas**: Read-heavy operations use dedicated replicas

## Monitoring and Analytics

### 1. Permission Metrics

- **Approval Rates**: Track approval/rejection rates by level and user
- **Response Times**: Monitor approval response times
- **Permission Violations**: Track and analyze permission violations
- **Cost Efficiency**: Monitor cost savings from permission controls

### 2. User Behavior Analytics

- **Permission Preferences**: Analyze which permission levels users prefer
- **Approval Patterns**: Identify common approval/rejection patterns
- **Usage Optimization**: Suggest optimal permission configurations

### 3. System Health Monitoring

- **Permission Engine Performance**: Monitor evaluation times and throughput
- **Approval Workflow Health**: Track approval processing times
- **Cache Hit Rates**: Monitor caching effectiveness
- **Database Performance**: Track permission-related query performance

This comprehensive 4-level permission system provides the granular control and security needed for a multi-agentic AI writing platform while maintaining usability and performance. The system scales from simple assistant-level interactions to fully autonomous document creation, always maintaining user control and system security.

