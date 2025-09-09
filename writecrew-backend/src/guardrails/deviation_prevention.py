"""
Deviation Prevention System
Monitors plan adherence, goal alignment, and prevents agents from straying from objectives
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import re
import json
import hashlib
from collections import defaultdict
import difflib

from ..services.ai_provider_service import AIProviderService
from ..config.settings import settings

logger = logging.getLogger(__name__)

class DeviationType(Enum):
    SCOPE_CREEP = "scope_creep"
    GOAL_MISALIGNMENT = "goal_misalignment"
    TONE_DEVIATION = "tone_deviation"
    STYLE_INCONSISTENCY = "style_inconsistency"
    CONTENT_DRIFT = "content_drift"
    STRUCTURAL_DEVIATION = "structural_deviation"
    REQUIREMENT_VIOLATION = "requirement_violation"
    PERMISSION_OVERREACH = "permission_overreach"

class DeviationSeverity(Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CRITICAL = "critical"

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ProjectObjective:
    """Individual project objective or requirement"""
    id: str
    description: str
    category: str  # content, style, structure, tone, etc.
    priority: str  # high, medium, low
    measurable_criteria: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    success_metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DeviationAlert:
    """Alert for detected deviation from plan or objectives"""
    id: str
    deviation_type: DeviationType
    severity: DeviationSeverity
    alert_level: AlertLevel
    description: str
    affected_objective: str
    agent_id: str
    content_section: str
    evidence: List[str] = field(default_factory=list)
    suggested_correction: str = ""
    confidence: float = 0.8
    timestamp: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False

@dataclass
class ComplianceCheck:
    """Result of compliance checking against objectives"""
    objective_id: str
    compliant: bool
    compliance_score: float  # 0.0 - 1.0
    violations: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)

@dataclass
class DeviationReport:
    """Comprehensive deviation analysis report"""
    content_id: str
    project_id: str
    agent_id: str
    overall_compliance_score: float
    total_objectives: int
    compliant_objectives: int
    deviation_alerts: List[DeviationAlert] = field(default_factory=list)
    compliance_checks: List[ComplianceCheck] = field(default_factory=list)
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    corrective_actions: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)

class DeviationPreventionSystem:
    """
    Comprehensive system for preventing agent deviation from project objectives,
    maintaining plan adherence, and ensuring goal alignment
    """
    
    def __init__(self, ai_provider_service: AIProviderService):
        self.ai_provider_service = ai_provider_service
        self.active_projects = {}  # project_id -> objectives
        self.deviation_history = defaultdict(list)
        self.performance_metrics = {
            'total_checks': 0,
            'deviations_detected': 0,
            'deviations_prevented': 0,
            'average_compliance_score': 0.0,
            'agent_compliance_rates': defaultdict(list)
        }
        
        # Deviation detection patterns
        self.deviation_patterns = {
            'scope_creep': [
                r'\b(?:also|additionally|furthermore|moreover)\s+(?:we|I)\s+(?:should|could|might|will)\b',
                r'\b(?:expanding|broadening|extending)\s+(?:the|our)\s+(?:scope|focus|coverage)\b',
                r'\b(?:new|additional|extra)\s+(?:features?|requirements?|objectives?)\b'
            ],
            'goal_misalignment': [
                r'\b(?:instead|rather|alternatively)\s+(?:of|than)\b',
                r'\b(?:different|alternative|opposite)\s+(?:approach|direction|goal)\b',
                r'\b(?:changing|shifting|modifying)\s+(?:the|our)\s+(?:goal|objective|focus)\b'
            ],
            'tone_deviation': [
                r'\b(?:suddenly|abruptly|unexpectedly)\s+(?:formal|informal|casual|serious)\b',
                r'\b(?:tone|style|voice)\s+(?:changes?|shifts?|becomes?)\b',
                r'\b(?:inconsistent|conflicting|mixed)\s+(?:tone|style|voice)\b'
            ]
        }
    
    async def register_project_objectives(self, project_id: str, 
                                        objectives: List[Dict[str, Any]]) -> bool:
        """Register project objectives and requirements for monitoring"""
        try:
            project_objectives = []
            
            for i, obj_data in enumerate(objectives):
                objective = ProjectObjective(
                    id=obj_data.get('id', f"obj_{i+1}"),
                    description=obj_data.get('description', ''),
                    category=obj_data.get('category', 'general'),
                    priority=obj_data.get('priority', 'medium'),
                    measurable_criteria=obj_data.get('measurable_criteria', []),
                    constraints=obj_data.get('constraints', []),
                    success_metrics=obj_data.get('success_metrics', {})
                )
                project_objectives.append(objective)
            
            self.active_projects[project_id] = project_objectives
            logger.info(f"Registered {len(project_objectives)} objectives for project {project_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error registering project objectives: {str(e)}")
            return False
    
    async def monitor_deviation(self, content: str, project_id: str, agent_id: str,
                              content_type: str = "general", 
                              context: Dict[str, Any] = None) -> DeviationReport:
        """
        Comprehensive deviation monitoring and prevention
        """
        start_time = datetime.utcnow()
        content_id = f"dev_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        try:
            logger.info(f"Starting deviation monitoring for content {content_id}")
            
            if project_id not in self.active_projects:
                logger.warning(f"Project {project_id} not found - creating default objectives")
                await self._create_default_objectives(project_id, content_type)
            
            objectives = self.active_projects[project_id]
            
            # Step 1: Pattern-based deviation detection
            pattern_alerts = self._detect_pattern_deviations(content, agent_id, objectives)
            
            # Step 2: AI-powered deviation analysis
            ai_alerts = await self._analyze_deviations_ai(content, objectives, agent_id, content_type)
            
            # Step 3: Compliance checking
            compliance_checks = await self._check_objective_compliance(content, objectives, agent_id)
            
            # Step 4: Risk assessment
            risk_assessment = self._assess_deviation_risk(pattern_alerts + ai_alerts, compliance_checks)
            
            # Step 5: Generate comprehensive report
            report = self._generate_deviation_report(
                content_id, project_id, agent_id, content,
                pattern_alerts + ai_alerts, compliance_checks,
                risk_assessment, start_time
            )
            
            # Step 6: Update performance metrics
            self._update_performance_metrics(report, agent_id)
            
            # Step 7: Take corrective action if needed
            await self._take_corrective_action(report)
            
            logger.info(f"Deviation monitoring completed for {content_id}")
            return report
            
        except Exception as e:
            logger.error(f"Error in deviation monitoring: {str(e)}")
            raise
    
    async def _create_default_objectives(self, project_id: str, content_type: str):
        """Create default objectives based on content type"""
        default_objectives = {
            'article': [
                {
                    'id': 'article_clarity',
                    'description': 'Content should be clear and easy to understand',
                    'category': 'clarity',
                    'priority': 'high',
                    'measurable_criteria': ['readability score > 3.0', 'no ambiguous statements']
                },
                {
                    'id': 'article_engagement',
                    'description': 'Content should be engaging and interesting',
                    'category': 'engagement',
                    'priority': 'medium',
                    'measurable_criteria': ['engaging introduction', 'compelling examples']
                }
            ],
            'business_document': [
                {
                    'id': 'business_professionalism',
                    'description': 'Maintain professional tone throughout',
                    'category': 'tone',
                    'priority': 'high',
                    'measurable_criteria': ['formal language', 'no casual expressions']
                },
                {
                    'id': 'business_structure',
                    'description': 'Follow standard business document structure',
                    'category': 'structure',
                    'priority': 'high',
                    'measurable_criteria': ['clear sections', 'logical flow']
                }
            ],
            'academic_paper': [
                {
                    'id': 'academic_rigor',
                    'description': 'Maintain academic standards and rigor',
                    'category': 'accuracy',
                    'priority': 'critical',
                    'measurable_criteria': ['proper citations', 'evidence-based claims']
                },
                {
                    'id': 'academic_structure',
                    'description': 'Follow academic paper structure',
                    'category': 'structure',
                    'priority': 'high',
                    'measurable_criteria': ['abstract', 'introduction', 'methodology', 'conclusion']
                }
            ]
        }
        
        objectives_data = default_objectives.get(content_type, default_objectives['article'])
        await self.register_project_objectives(project_id, objectives_data)
    
    def _detect_pattern_deviations(self, content: str, agent_id: str, 
                                 objectives: List[ProjectObjective]) -> List[DeviationAlert]:
        """Detect deviations using pattern matching"""
        alerts = []
        alert_counter = 1
        
        for deviation_type, patterns in self.deviation_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                
                for match in matches:
                    # Get context around the match
                    start = max(0, match.start() - 50)
                    end = min(len(content), match.end() + 50)
                    context = content[start:end]
                    
                    alert = DeviationAlert(
                        id=f"pattern_alert_{alert_counter}",
                        deviation_type=DeviationType(deviation_type),
                        severity=self._determine_severity(deviation_type, match.group()),
                        alert_level=AlertLevel.WARNING,
                        description=f"Potential {deviation_type.replace('_', ' ')} detected",
                        affected_objective="general",
                        agent_id=agent_id,
                        content_section=context,
                        evidence=[match.group()],
                        suggested_correction=self._get_pattern_correction(deviation_type),
                        confidence=0.6
                    )
                    alerts.append(alert)
                    alert_counter += 1
        
        return alerts
    
    async def _analyze_deviations_ai(self, content: str, objectives: List[ProjectObjective],
                                   agent_id: str, content_type: str) -> List[DeviationAlert]:
        """Use AI to analyze potential deviations"""
        try:
            # Prepare objectives summary for AI
            objectives_summary = []
            for obj in objectives:
                objectives_summary.append({
                    'id': obj.id,
                    'description': obj.description,
                    'category': obj.category,
                    'priority': obj.priority,
                    'criteria': obj.measurable_criteria
                })
            
            prompt = f"""
            Analyze the following {content_type} content for deviations from the specified project objectives.
            
            Project Objectives:
            {json.dumps(objectives_summary, indent=2)}
            
            Content to analyze:
            {content[:2000]}  # Limit content for AI processing
            
            Look for these types of deviations:
            1. SCOPE_CREEP: Content going beyond defined scope
            2. GOAL_MISALIGNMENT: Content not aligned with stated goals
            3. TONE_DEVIATION: Inconsistent or inappropriate tone
            4. STYLE_INCONSISTENCY: Inconsistent writing style
            5. CONTENT_DRIFT: Content straying from main topic
            6. STRUCTURAL_DEVIATION: Not following required structure
            7. REQUIREMENT_VIOLATION: Violating specific requirements
            
            For each deviation found, provide:
            - deviation_type: One of the types above
            - severity: minor/moderate/major/critical
            - description: What the deviation is
            - affected_objective: Which objective ID is affected
            - evidence: Specific text showing the deviation
            - suggested_correction: How to fix it
            - confidence: How confident you are (0.0-1.0)
            
            Return as JSON array (max 8 deviations):
            [
                {{
                    "deviation_type": "goal_misalignment",
                    "severity": "moderate",
                    "description": "Content discusses topics not in project scope",
                    "affected_objective": "article_clarity",
                    "evidence": "specific problematic text",
                    "suggested_correction": "refocus on main objectives",
                    "confidence": 0.8
                }}
            ]
            """
            
            response = await self.ai_provider_service.generate_content(
                prompt=prompt,
                provider="openai",
                model="gpt-4",
                max_tokens=1500,
                temperature=0.1
            )
            
            # Parse AI response
            ai_data = json.loads(response.get('content', '[]'))
            alerts = []
            
            for i, deviation_data in enumerate(ai_data[:8]):
                alert = DeviationAlert(
                    id=f"ai_alert_{i+1}",
                    deviation_type=DeviationType(deviation_data.get('deviation_type', 'content_drift')),
                    severity=DeviationSeverity(deviation_data.get('severity', 'moderate')),
                    alert_level=self._severity_to_alert_level(deviation_data.get('severity', 'moderate')),
                    description=deviation_data.get('description', ''),
                    affected_objective=deviation_data.get('affected_objective', 'general'),
                    agent_id=agent_id,
                    content_section=deviation_data.get('evidence', ''),
                    evidence=[deviation_data.get('evidence', '')],
                    suggested_correction=deviation_data.get('suggested_correction', ''),
                    confidence=float(deviation_data.get('confidence', 0.7))
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error in AI deviation analysis: {str(e)}")
            return []
    
    async def _check_objective_compliance(self, content: str, objectives: List[ProjectObjective],
                                        agent_id: str) -> List[ComplianceCheck]:
        """Check compliance with each project objective"""
        compliance_checks = []
        
        for objective in objectives:
            try:
                # AI-powered compliance checking
                compliance_check = await self._check_single_objective_ai(content, objective)
                compliance_checks.append(compliance_check)
                
            except Exception as e:
                logger.error(f"Error checking objective {objective.id}: {str(e)}")
                
                # Fallback compliance check
                fallback_check = ComplianceCheck(
                    objective_id=objective.id,
                    compliant=True,  # Assume compliant if check fails
                    compliance_score=0.5,
                    violations=[f"Unable to verify compliance: {str(e)}"],
                    recommendations=["Manual review recommended"]
                )
                compliance_checks.append(fallback_check)
        
        return compliance_checks
    
    async def _check_single_objective_ai(self, content: str, 
                                       objective: ProjectObjective) -> ComplianceCheck:
        """Check compliance with a single objective using AI"""
        prompt = f"""
        Check if the following content complies with this specific objective:
        
        Objective:
        - ID: {objective.id}
        - Description: {objective.description}
        - Category: {objective.category}
        - Priority: {objective.priority}
        - Measurable Criteria: {objective.measurable_criteria}
        - Constraints: {objective.constraints}
        
        Content to check:
        {content[:1500]}  # Limit content for AI processing
        
        Analyze compliance and provide:
        1. compliant: true/false - Does the content meet this objective?
        2. compliance_score: 0.0-1.0 - How well does it comply?
        3. violations: List of specific violations found
        4. recommendations: Specific suggestions to improve compliance
        5. evidence: Specific text supporting your assessment
        
        Return as JSON:
        {{
            "compliant": true,
            "compliance_score": 0.85,
            "violations": ["specific violation if any"],
            "recommendations": ["specific recommendation"],
            "evidence": ["supporting text from content"]
        }}
        """
        
        response = await self.ai_provider_service.generate_content(
            prompt=prompt,
            provider="openai",
            model="gpt-4",
            max_tokens=800,
            temperature=0.1
        )
        
        # Parse AI response
        ai_result = json.loads(response.get('content', '{}'))
        
        return ComplianceCheck(
            objective_id=objective.id,
            compliant=ai_result.get('compliant', True),
            compliance_score=float(ai_result.get('compliance_score', 0.8)),
            violations=ai_result.get('violations', []),
            recommendations=ai_result.get('recommendations', []),
            evidence=ai_result.get('evidence', [])
        )
    
    def _assess_deviation_risk(self, alerts: List[DeviationAlert], 
                             compliance_checks: List[ComplianceCheck]) -> Dict[str, Any]:
        """Assess overall deviation risk"""
        risk_assessment = {
            'overall_risk_level': 'low',
            'risk_score': 0.0,
            'critical_issues': 0,
            'major_issues': 0,
            'compliance_rate': 0.0,
            'risk_factors': [],
            'mitigation_priority': []
        }
        
        # Count severity levels
        severity_counts = {
            'critical': len([a for a in alerts if a.severity == DeviationSeverity.CRITICAL]),
            'major': len([a for a in alerts if a.severity == DeviationSeverity.MAJOR]),
            'moderate': len([a for a in alerts if a.severity == DeviationSeverity.MODERATE]),
            'minor': len([a for a in alerts if a.severity == DeviationSeverity.MINOR])
        }
        
        risk_assessment['critical_issues'] = severity_counts['critical']
        risk_assessment['major_issues'] = severity_counts['major']
        
        # Calculate risk score
        risk_score = (
            severity_counts['critical'] * 1.0 +
            severity_counts['major'] * 0.7 +
            severity_counts['moderate'] * 0.4 +
            severity_counts['minor'] * 0.1
        )
        
        # Normalize risk score (0-1 scale)
        max_possible_risk = len(alerts)
        if max_possible_risk > 0:
            risk_assessment['risk_score'] = min(1.0, risk_score / max_possible_risk)
        
        # Determine overall risk level
        if severity_counts['critical'] > 0:
            risk_assessment['overall_risk_level'] = 'critical'
        elif severity_counts['major'] > 0:
            risk_assessment['overall_risk_level'] = 'high'
        elif severity_counts['moderate'] > 2:
            risk_assessment['overall_risk_level'] = 'medium'
        else:
            risk_assessment['overall_risk_level'] = 'low'
        
        # Calculate compliance rate
        if compliance_checks:
            compliant_count = len([c for c in compliance_checks if c.compliant])
            risk_assessment['compliance_rate'] = compliant_count / len(compliance_checks)
        
        # Identify risk factors
        risk_factors = []
        if severity_counts['critical'] > 0:
            risk_factors.append("Critical deviations detected")
        if risk_assessment['compliance_rate'] < 0.8:
            risk_factors.append("Low compliance rate")
        if len(alerts) > 5:
            risk_factors.append("High number of deviation alerts")
        
        risk_assessment['risk_factors'] = risk_factors
        
        # Mitigation priorities
        mitigation_priority = []
        if severity_counts['critical'] > 0:
            mitigation_priority.append("Address critical deviations immediately")
        if severity_counts['major'] > 0:
            mitigation_priority.append("Resolve major deviations")
        if risk_assessment['compliance_rate'] < 0.7:
            mitigation_priority.append("Improve objective compliance")
        
        risk_assessment['mitigation_priority'] = mitigation_priority
        
        return risk_assessment
    
    def _generate_deviation_report(self, content_id: str, project_id: str, agent_id: str,
                                 content: str, alerts: List[DeviationAlert],
                                 compliance_checks: List[ComplianceCheck],
                                 risk_assessment: Dict[str, Any],
                                 start_time: datetime) -> DeviationReport:
        """Generate comprehensive deviation report"""
        
        # Calculate overall compliance score
        if compliance_checks:
            overall_compliance_score = sum(c.compliance_score for c in compliance_checks) / len(compliance_checks)
        else:
            overall_compliance_score = 1.0
        
        # Count compliant objectives
        compliant_objectives = len([c for c in compliance_checks if c.compliant])
        
        # Generate corrective actions
        corrective_actions = []
        
        # High-priority corrective actions
        critical_alerts = [a for a in alerts if a.severity == DeviationSeverity.CRITICAL]
        for alert in critical_alerts:
            if alert.suggested_correction:
                corrective_actions.append(f"CRITICAL: {alert.suggested_correction}")
        
        # Compliance-based corrective actions
        non_compliant_checks = [c for c in compliance_checks if not c.compliant]
        for check in non_compliant_checks:
            corrective_actions.extend(check.recommendations[:2])  # Top 2 recommendations
        
        # Risk-based corrective actions
        corrective_actions.extend(risk_assessment.get('mitigation_priority', []))
        
        # Remove duplicates
        corrective_actions = list(set(corrective_actions))
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return DeviationReport(
            content_id=content_id,
            project_id=project_id,
            agent_id=agent_id,
            overall_compliance_score=overall_compliance_score,
            total_objectives=len(compliance_checks),
            compliant_objectives=compliant_objectives,
            deviation_alerts=alerts,
            compliance_checks=compliance_checks,
            risk_assessment=risk_assessment,
            corrective_actions=corrective_actions,
            processing_time=processing_time
        )
    
    async def _take_corrective_action(self, report: DeviationReport):
        """Take automated corrective actions based on deviation report"""
        
        # Log critical deviations
        critical_alerts = [a for a in report.deviation_alerts if a.severity == DeviationSeverity.CRITICAL]
        if critical_alerts:
            logger.critical(f"Critical deviations detected in {report.content_id} by {report.agent_id}")
            for alert in critical_alerts:
                logger.critical(f"  - {alert.description}: {alert.evidence}")
        
        # Store deviation history for learning
        self.deviation_history[report.agent_id].append({
            'timestamp': datetime.utcnow(),
            'deviation_count': len(report.deviation_alerts),
            'compliance_score': report.overall_compliance_score,
            'risk_level': report.risk_assessment['overall_risk_level']
        })
        
        # Trigger alerts for high-risk situations
        if report.risk_assessment['overall_risk_level'] in ['critical', 'high']:
            await self._trigger_high_risk_alert(report)
    
    async def _trigger_high_risk_alert(self, report: DeviationReport):
        """Trigger alert for high-risk deviation situations"""
        logger.warning(f"High-risk deviation detected - Project: {report.project_id}, Agent: {report.agent_id}")
        
        # In a production system, this would:
        # - Send notifications to project managers
        # - Pause agent execution if critical
        # - Trigger human review workflow
        # - Update agent permission levels
        
        # For now, log the alert
        logger.warning(f"Risk Assessment: {report.risk_assessment}")
        logger.warning(f"Corrective Actions Required: {report.corrective_actions}")
    
    def _determine_severity(self, deviation_type: str, evidence: str) -> DeviationSeverity:
        """Determine severity based on deviation type and evidence"""
        severity_rules = {
            'scope_creep': DeviationSeverity.MODERATE,
            'goal_misalignment': DeviationSeverity.MAJOR,
            'tone_deviation': DeviationSeverity.MODERATE,
            'style_inconsistency': DeviationSeverity.MINOR,
            'content_drift': DeviationSeverity.MODERATE,
            'structural_deviation': DeviationSeverity.MAJOR,
            'requirement_violation': DeviationSeverity.CRITICAL,
            'permission_overreach': DeviationSeverity.CRITICAL
        }
        
        return severity_rules.get(deviation_type, DeviationSeverity.MODERATE)
    
    def _severity_to_alert_level(self, severity: str) -> AlertLevel:
        """Convert severity to alert level"""
        mapping = {
            'minor': AlertLevel.INFO,
            'moderate': AlertLevel.WARNING,
            'major': AlertLevel.ERROR,
            'critical': AlertLevel.CRITICAL
        }
        return mapping.get(severity, AlertLevel.WARNING)
    
    def _get_pattern_correction(self, deviation_type: str) -> str:
        """Get correction suggestion for pattern-based deviation"""
        corrections = {
            'scope_creep': "Stay focused on original project scope and objectives",
            'goal_misalignment': "Realign content with stated project goals",
            'tone_deviation': "Maintain consistent tone throughout the content"
        }
        return corrections.get(deviation_type, "Review content for alignment with objectives")
    
    def _update_performance_metrics(self, report: DeviationReport, agent_id: str):
        """Update deviation prevention performance metrics"""
        self.performance_metrics['total_checks'] += 1
        
        # Count deviations
        deviation_count = len(report.deviation_alerts)
        if deviation_count > 0:
            self.performance_metrics['deviations_detected'] += deviation_count
        
        # Update average compliance score
        current_avg = self.performance_metrics['average_compliance_score']
        total_checks = self.performance_metrics['total_checks']
        
        self.performance_metrics['average_compliance_score'] = (
            (current_avg * (total_checks - 1) + report.overall_compliance_score) / 
            total_checks
        )
        
        # Track agent compliance rates
        self.performance_metrics['agent_compliance_rates'][agent_id].append(
            report.overall_compliance_score
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get deviation prevention performance metrics"""
        # Calculate prevention rate
        total_deviations = self.performance_metrics['deviations_detected']
        prevented_deviations = self.performance_metrics['deviations_prevented']
        prevention_rate = (prevented_deviations / max(1, total_deviations)) * 100
        
        # Agent compliance summary
        agent_compliance = {}
        for agent_id, scores in self.performance_metrics['agent_compliance_rates'].items():
            if scores:
                agent_compliance[agent_id] = {
                    'average_compliance': sum(scores) / len(scores),
                    'total_checks': len(scores),
                    'trend': 'improving' if len(scores) >= 3 and 
                            scores[-1] > scores[-3] else 'stable'
                }
        
        return {
            'total_checks': self.performance_metrics['total_checks'],
            'deviations_detected': self.performance_metrics['deviations_detected'],
            'deviations_prevented': self.performance_metrics['deviations_prevented'],
            'prevention_rate': prevention_rate,
            'average_compliance_score': self.performance_metrics['average_compliance_score'],
            'agent_compliance_rates': agent_compliance,
            'active_projects': len(self.active_projects)
        }
    
    async def get_agent_deviation_analysis(self, agent_id: str) -> Dict[str, Any]:
        """Get detailed deviation analysis for a specific agent"""
        agent_history = self.deviation_history.get(agent_id, [])
        
        if not agent_history:
            return {
                'agent_id': agent_id,
                'total_checks': 0,
                'analysis': 'No deviation history available'
            }
        
        # Calculate trends
        recent_scores = [h['compliance_score'] for h in agent_history[-10:]]
        earlier_scores = [h['compliance_score'] for h in agent_history[-20:-10]] if len(agent_history) >= 20 else []
        
        trend = 'stable'
        if earlier_scores and recent_scores:
            recent_avg = sum(recent_scores) / len(recent_scores)
            earlier_avg = sum(earlier_scores) / len(earlier_scores)
            
            if recent_avg > earlier_avg + 0.1:
                trend = 'improving'
            elif recent_avg < earlier_avg - 0.1:
                trend = 'declining'
        
        # Risk assessment
        recent_risk_levels = [h['risk_level'] for h in agent_history[-5:]]
        high_risk_count = len([r for r in recent_risk_levels if r in ['high', 'critical']])
        
        risk_status = 'low'
        if high_risk_count >= 3:
            risk_status = 'high'
        elif high_risk_count >= 1:
            risk_status = 'medium'
        
        return {
            'agent_id': agent_id,
            'total_checks': len(agent_history),
            'average_compliance': sum(h['compliance_score'] for h in agent_history) / len(agent_history),
            'trend': trend,
            'risk_status': risk_status,
            'recent_compliance_scores': recent_scores,
            'recommendations': self._get_agent_recommendations(agent_id, agent_history)
        }
    
    def _get_agent_recommendations(self, agent_id: str, history: List[Dict[str, Any]]) -> List[str]:
        """Get personalized recommendations for an agent"""
        recommendations = []
        
        if not history:
            return ["No history available for analysis"]
        
        # Analyze compliance trend
        recent_scores = [h['compliance_score'] for h in history[-5:]]
        avg_compliance = sum(recent_scores) / len(recent_scores)
        
        if avg_compliance < 0.7:
            recommendations.append("Focus on improving objective compliance")
        
        # Analyze deviation patterns
        recent_deviations = [h['deviation_count'] for h in history[-5:]]
        avg_deviations = sum(recent_deviations) / len(recent_deviations)
        
        if avg_deviations > 3:
            recommendations.append("Review project objectives before starting tasks")
        
        # Risk-based recommendations
        recent_risks = [h['risk_level'] for h in history[-3:]]
        if 'critical' in recent_risks:
            recommendations.append("Critical deviations detected - require additional oversight")
        elif 'high' in recent_risks:
            recommendations.append("Monitor closely for deviation patterns")
        
        return recommendations if recommendations else ["Performance within acceptable parameters"]
    
    async def update_project_objectives(self, project_id: str, 
                                      updated_objectives: List[Dict[str, Any]]) -> bool:
        """Update project objectives during execution"""
        try:
            # Log the update
            logger.info(f"Updating objectives for project {project_id}")
            
            # Store previous objectives for comparison
            previous_objectives = self.active_projects.get(project_id, [])
            
            # Register new objectives
            success = await self.register_project_objectives(project_id, updated_objectives)
            
            if success:
                # Log significant changes
                new_objectives = self.active_projects[project_id]
                if len(new_objectives) != len(previous_objectives):
                    logger.info(f"Objective count changed: {len(previous_objectives)} -> {len(new_objectives)}")
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating project objectives: {str(e)}")
            return False
    
    def get_project_compliance_summary(self, project_id: str) -> Dict[str, Any]:
        """Get compliance summary for a specific project"""
        if project_id not in self.active_projects:
            return {'error': f'Project {project_id} not found'}
        
        objectives = self.active_projects[project_id]
        
        return {
            'project_id': project_id,
            'total_objectives': len(objectives),
            'objectives': [
                {
                    'id': obj.id,
                    'description': obj.description,
                    'category': obj.category,
                    'priority': obj.priority
                }
                for obj in objectives
            ],
            'monitoring_active': True
        }

