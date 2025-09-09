"""
Research Agent - Fact-checking and Information Gathering
Specialized CrewAI agent for research, verification, and data collection
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import structlog

from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from ..models.task import TaskRequest, TaskResponse
from ..services.ai_providers import AIProviderService
from ..utils.prompts import RESEARCH_AGENT_PROMPTS
from .base_agent import BaseWritingAgent

logger = structlog.get_logger(__name__)


class FactCheckingTool(BaseTool):
    """Tool for fact-checking and verification"""
    
    name: str = "fact_checker"
    description: str = "Verify facts, claims, and statements for accuracy"
    
    def _run(self, claim: str, context: str = "") -> Dict[str, Any]:
        """Fact-check a claim or statement"""
        try:
            # Analyze claim for fact-checkable elements
            checkable_elements = self._identify_checkable_elements(claim)
            
            # Assess claim credibility
            credibility_score = self._assess_credibility(claim, context)
            
            # Identify verification sources needed
            sources_needed = self._identify_required_sources(claim)
            
            return {
                'claim': claim,
                'checkable_elements': checkable_elements,
                'credibility_score': credibility_score,
                'sources_needed': sources_needed,
                'verification_status': self._determine_verification_status(credibility_score),
                'recommendations': self._generate_verification_recommendations(claim, credibility_score)
            }
            
        except Exception as e:
            logger.error("Fact checking failed", error=str(e))
            return {
                'claim': claim,
                'error': str(e),
                'verification_status': 'error',
                'recommendations': ['Manual verification required due to processing error']
            }
    
    def _identify_checkable_elements(self, claim: str) -> List[Dict[str, str]]:
        """Identify elements that can be fact-checked"""
        elements = []
        claim_lower = claim.lower()
        
        # Statistical claims
        import re
        numbers = re.findall(r'\d+(?:\.\d+)?%?', claim)
        for number in numbers:
            elements.append({
                'type': 'statistic',
                'content': number,
                'context': claim[:100] + '...' if len(claim) > 100 else claim
            })
        
        # Date references
        dates = re.findall(r'\b\d{4}\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b', claim)
        for date in dates:
            elements.append({
                'type': 'date',
                'content': date,
                'context': claim[:100] + '...' if len(claim) > 100 else claim
            })
        
        # Named entities (simplified detection)
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', claim)
        for noun in proper_nouns:
            if len(noun.split()) <= 3:  # Limit to reasonable entity names
                elements.append({
                    'type': 'entity',
                    'content': noun,
                    'context': claim[:100] + '...' if len(claim) > 100 else claim
                })
        
        # Claims with superlatives
        superlatives = ['largest', 'smallest', 'first', 'last', 'most', 'least', 'best', 'worst']
        for superlative in superlatives:
            if superlative in claim_lower:
                elements.append({
                    'type': 'superlative_claim',
                    'content': superlative,
                    'context': claim[:100] + '...' if len(claim) > 100 else claim
                })
        
        return elements
    
    def _assess_credibility(self, claim: str, context: str) -> float:
        """Assess initial credibility of a claim"""
        credibility = 0.5  # Neutral starting point
        claim_lower = claim.lower()
        
        # Positive indicators
        if any(indicator in claim_lower for indicator in ['according to', 'study shows', 'research indicates', 'data suggests']):
            credibility += 0.2
        
        if any(indicator in claim_lower for indicator in ['peer-reviewed', 'published', 'journal', 'university']):
            credibility += 0.2
        
        # Negative indicators
        if any(indicator in claim_lower for indicator in ['everyone knows', 'obviously', 'clearly', 'without doubt']):
            credibility -= 0.2
        
        if any(indicator in claim_lower for indicator in ['miracle', 'secret', 'they don\'t want you to know']):
            credibility -= 0.3
        
        # Extreme claims
        if any(indicator in claim_lower for indicator in ['100%', 'never', 'always', 'impossible', 'guaranteed']):
            credibility -= 0.1
        
        return max(0.0, min(1.0, credibility))
    
    def _identify_required_sources(self, claim: str) -> List[str]:
        """Identify types of sources needed for verification"""
        sources = []
        claim_lower = claim.lower()
        
        # Academic sources
        if any(word in claim_lower for word in ['study', 'research', 'analysis', 'survey']):
            sources.append('academic_papers')
        
        # Government sources
        if any(word in claim_lower for word in ['government', 'policy', 'law', 'regulation', 'census']):
            sources.append('government_data')
        
        # News sources
        if any(word in claim_lower for word in ['recent', 'news', 'reported', 'announced']):
            sources.append('news_articles')
        
        # Statistical sources
        if any(word in claim_lower for word in ['percent', '%', 'statistics', 'data', 'numbers']):
            sources.append('statistical_databases')
        
        # Historical sources
        if any(word in claim_lower for word in ['history', 'historical', 'past', 'ancient']):
            sources.append('historical_records')
        
        return sources if sources else ['general_sources']
    
    def _determine_verification_status(self, credibility_score: float) -> str:
        """Determine verification status based on credibility"""
        if credibility_score >= 0.8:
            return 'likely_accurate'
        elif credibility_score >= 0.6:
            return 'needs_verification'
        elif credibility_score >= 0.4:
            return 'questionable'
        else:
            return 'likely_inaccurate'
    
    def _generate_verification_recommendations(self, claim: str, credibility_score: float) -> List[str]:
        """Generate recommendations for verification"""
        recommendations = []
        
        if credibility_score < 0.6:
            recommendations.append('Verify with multiple independent sources')
        
        if 'study' in claim.lower() or 'research' in claim.lower():
            recommendations.append('Check original study methodology and sample size')
        
        if any(word in claim.lower() for word in ['recent', 'new', 'latest']):
            recommendations.append('Verify publication date and current relevance')
        
        if credibility_score < 0.4:
            recommendations.append('Consider removing or rephrasing this claim')
        
        recommendations.append('Cross-reference with authoritative sources')
        
        return recommendations


class ResearchTool(BaseTool):
    """Tool for conducting research and gathering information"""
    
    name: str = "researcher"
    description: str = "Conduct research and gather relevant information on topics"
    
    def _run(self, topic: str, research_type: str = "general", depth: str = "medium") -> Dict[str, Any]:
        """Conduct research on a given topic"""
        try:
            # Generate research strategy
            strategy = self._create_research_strategy(topic, research_type, depth)
            
            # Identify key research questions
            questions = self._generate_research_questions(topic, research_type)
            
            # Suggest information sources
            sources = self._suggest_information_sources(topic, research_type)
            
            # Create research outline
            outline = self._create_research_outline(topic, questions)
            
            return {
                'topic': topic,
                'research_type': research_type,
                'depth': depth,
                'strategy': strategy,
                'key_questions': questions,
                'recommended_sources': sources,
                'research_outline': outline,
                'estimated_time': self._estimate_research_time(depth, len(questions))
            }
            
        except Exception as e:
            logger.error("Research planning failed", error=str(e))
            return {
                'topic': topic,
                'error': str(e),
                'strategy': 'Basic research approach due to planning error'
            }
    
    def _create_research_strategy(self, topic: str, research_type: str, depth: str) -> str:
        """Create research strategy based on topic and requirements"""
        strategies = {
            'general': f"Conduct comprehensive overview research on {topic}, focusing on key facts, current status, and general understanding.",
            'academic': f"Perform scholarly research on {topic} using peer-reviewed sources, focusing on theoretical frameworks and empirical evidence.",
            'current_events': f"Research recent developments and news about {topic}, emphasizing timeline and current implications.",
            'historical': f"Investigate historical context and evolution of {topic}, tracing development over time.",
            'comparative': f"Compare different aspects, approaches, or perspectives related to {topic}.",
            'technical': f"Research technical specifications, methodologies, and detailed mechanisms related to {topic}."
        }
        
        base_strategy = strategies.get(research_type, strategies['general'])
        
        depth_modifiers = {
            'shallow': "Focus on basic facts and overview information.",
            'medium': "Include supporting details and multiple perspectives.",
            'deep': "Conduct thorough investigation with comprehensive analysis and expert opinions."
        }
        
        return f"{base_strategy} {depth_modifiers.get(depth, depth_modifiers['medium'])}"
    
    def _generate_research_questions(self, topic: str, research_type: str) -> List[str]:
        """Generate key research questions"""
        base_questions = [
            f"What is {topic}?",
            f"Why is {topic} important?",
            f"What are the key aspects of {topic}?",
            f"Who are the main stakeholders in {topic}?",
            f"What are current trends related to {topic}?"
        ]
        
        type_specific_questions = {
            'academic': [
                f"What does current research say about {topic}?",
                f"What are the main theoretical frameworks for {topic}?",
                f"What gaps exist in {topic} research?"
            ],
            'current_events': [
                f"What recent developments have occurred with {topic}?",
                f"How has {topic} changed in the past year?",
                f"What future predictions exist for {topic}?"
            ],
            'historical': [
                f"How has {topic} evolved over time?",
                f"What were the key milestones in {topic} development?",
                f"What lessons can be learned from {topic} history?"
            ],
            'technical': [
                f"How does {topic} work technically?",
                f"What are the specifications of {topic}?",
                f"What are the technical challenges with {topic}?"
            ]
        }
        
        specific_questions = type_specific_questions.get(research_type, [])
        return base_questions + specific_questions
    
    def _suggest_information_sources(self, topic: str, research_type: str) -> List[Dict[str, str]]:
        """Suggest appropriate information sources"""
        sources = [
            {'type': 'encyclopedias', 'description': 'General reference and overview information'},
            {'type': 'news_articles', 'description': 'Current events and recent developments'},
            {'type': 'official_websites', 'description': 'Authoritative organizational information'}
        ]
        
        type_specific_sources = {
            'academic': [
                {'type': 'peer_reviewed_journals', 'description': 'Scholarly research and analysis'},
                {'type': 'academic_databases', 'description': 'Comprehensive academic resources'},
                {'type': 'university_publications', 'description': 'Educational institution research'}
            ],
            'current_events': [
                {'type': 'news_outlets', 'description': 'Breaking news and current reporting'},
                {'type': 'press_releases', 'description': 'Official announcements and statements'},
                {'type': 'social_media', 'description': 'Real-time updates and public opinion'}
            ],
            'historical': [
                {'type': 'historical_archives', 'description': 'Primary historical documents'},
                {'type': 'historical_databases', 'description': 'Curated historical information'},
                {'type': 'biographical_sources', 'description': 'Personal accounts and biographies'}
            ],
            'technical': [
                {'type': 'technical_documentation', 'description': 'Specifications and manuals'},
                {'type': 'industry_reports', 'description': 'Professional analysis and data'},
                {'type': 'patent_databases', 'description': 'Technical innovations and designs'}
            ]
        }
        
        specific_sources = type_specific_sources.get(research_type, [])
        return sources + specific_sources
    
    def _create_research_outline(self, topic: str, questions: List[str]) -> List[Dict[str, str]]:
        """Create structured research outline"""
        outline = [
            {'section': 'Introduction', 'focus': f'Overview and definition of {topic}'},
            {'section': 'Background', 'focus': f'Context and importance of {topic}'},
            {'section': 'Main Analysis', 'focus': 'Detailed examination of key aspects'},
            {'section': 'Current Status', 'focus': 'Present situation and recent developments'},
            {'section': 'Implications', 'focus': 'Significance and future considerations'},
            {'section': 'Conclusion', 'focus': 'Summary of key findings and insights'}
        ]
        
        return outline
    
    def _estimate_research_time(self, depth: str, num_questions: int) -> str:
        """Estimate time needed for research"""
        base_times = {'shallow': 30, 'medium': 60, 'deep': 120}  # minutes
        base_time = base_times.get(depth, 60)
        
        # Add time based on number of questions
        additional_time = num_questions * 5
        
        total_minutes = base_time + additional_time
        
        if total_minutes < 60:
            return f"{total_minutes} minutes"
        else:
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{hours} hour{'s' if hours > 1 else ''}" + (f" {minutes} minutes" if minutes > 0 else "")


class ResearchAgent(BaseWritingAgent):
    """Research Agent for fact-checking and information gathering"""
    
    def __init__(self, ai_provider_service: AIProviderService):
        super().__init__(
            agent_id="research_agent",
            name="Research Agent",
            ai_provider_service=ai_provider_service
        )
        
        # Initialize CrewAI agent
        self.crew_agent = Agent(
            role="Expert Research Analyst and Fact Checker",
            goal="Conduct thorough research, verify facts, and provide accurate, well-sourced information",
            backstory=RESEARCH_AGENT_PROMPTS["backstory"],
            verbose=True,
            allow_delegation=False,
            tools=[FactCheckingTool(), ResearchTool()],
            llm=ai_provider_service.get_primary_llm(),
            max_iter=3,
            memory=True
        )
        
        # Specializations
        self.specializations = [
            "Fact-checking and verification",
            "Academic research",
            "Current events analysis",
            "Historical research",
            "Statistical validation",
            "Source evaluation",
            "Data gathering",
            "Information synthesis"
        ]
        
        # Research type expertise
        self.research_expertise = {
            'fact_checking': 0.95,
            'academic_research': 0.90,
            'current_events': 0.88,
            'historical_research': 0.85,
            'statistical_analysis': 0.82,
            'source_evaluation': 0.93,
            'data_gathering': 0.87,
            'comparative_analysis': 0.80
        }
        
        logger.info("Research Agent initialized", specializations=len(self.specializations))
    
    async def execute_task(self, task_request: TaskRequest) -> TaskResponse:
        """Execute research task"""
        try:
            self._start_timing()
            logger.info("Executing research task", task_id=task_request.task_id)
            
            # Analyze research requirements
            research_analysis = await self._analyze_research_requirements(task_request)
            
            # Conduct research
            research_results = await self._conduct_research(task_request, research_analysis)
            
            # Verify and validate findings
            validated_results = await self._validate_research_findings(research_results, research_analysis)
            
            # Format research output
            formatted_output = await self._format_research_output(validated_results, research_analysis)
            
            # Create response
            response = TaskResponse(
                task_id=task_request.task_id,
                agent_id=self.agent_id,
                status="completed",
                content=formatted_output,
                metadata={
                    "research_type": research_analysis.get("research_type"),
                    "sources_consulted": research_analysis.get("sources_needed", []),
                    "fact_checks_performed": len(research_analysis.get("fact_checkable_claims", [])),
                    "research_depth": research_analysis.get("depth"),
                    "confidence_level": research_analysis.get("overall_confidence", 0.8)
                },
                confidence_score=self._calculate_research_confidence(research_analysis, validated_results),
                processing_time=self._get_processing_time()
            )
            
            await self._update_performance_metrics(response)
            
            logger.info(
                "Research task completed",
                task_id=task_request.task_id,
                research_type=research_analysis.get("research_type"),
                confidence=response.confidence_score
            )
            
            return response
            
        except Exception as e:
            logger.error("Research task failed", task_id=task_request.task_id, error=str(e))
            return self._create_error_response(task_request, str(e))
    
    async def _analyze_research_requirements(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Analyze what type of research is needed"""
        try:
            content_lower = task_request.content.lower()
            
            # Determine research type
            research_type = self._determine_research_type(task_request.content, task_request.task_type)
            
            # Assess research depth needed
            depth = self._assess_research_depth(task_request.content, task_request.context)
            
            # Identify fact-checkable claims
            fact_checkable_claims = self._identify_fact_checkable_claims(task_request.content)
            
            # Determine required sources
            sources_needed = self._determine_required_sources(task_request.content, research_type)
            
            # Assess urgency and timeline
            urgency = self._assess_research_urgency(task_request.content, task_request.user_preferences)
            
            return {
                "research_type": research_type,
                "depth": depth,
                "fact_checkable_claims": fact_checkable_claims,
                "sources_needed": sources_needed,
                "urgency": urgency,
                "estimated_complexity": self._assess_research_complexity(task_request),
                "requires_current_data": self._requires_current_data(task_request.content),
                "requires_expert_sources": self._requires_expert_sources(task_request.content)
            }
            
        except Exception as e:
            logger.error("Research analysis failed", error=str(e))
            return {
                "research_type": "general",
                "depth": "medium",
                "fact_checkable_claims": [],
                "sources_needed": ["general_sources"],
                "urgency": "normal"
            }
    
    def _determine_research_type(self, content: str, task_type: str) -> str:
        """Determine the type of research needed"""
        content_lower = content.lower()
        
        # Fact-checking indicators
        if any(word in content_lower for word in ['verify', 'fact-check', 'accurate', 'true', 'false']):
            return 'fact_checking'
        
        # Academic research indicators
        if any(word in content_lower for word in ['study', 'research', 'academic', 'scholarly', 'peer-reviewed']):
            return 'academic_research'
        
        # Current events indicators
        if any(word in content_lower for word in ['recent', 'current', 'news', 'latest', 'today']):
            return 'current_events'
        
        # Historical research indicators
        if any(word in content_lower for word in ['history', 'historical', 'past', 'evolution', 'timeline']):
            return 'historical_research'
        
        # Statistical analysis indicators
        if any(word in content_lower for word in ['statistics', 'data', 'numbers', 'percentage', 'survey']):
            return 'statistical_analysis'
        
        # Comparative analysis indicators
        if any(word in content_lower for word in ['compare', 'comparison', 'versus', 'vs', 'difference']):
            return 'comparative_analysis'
        
        return 'general'
    
    def _assess_research_depth(self, content: str, context: Optional[str]) -> str:
        """Assess how deep the research needs to be"""
        combined_text = f"{content} {context or ''}".lower()
        
        # Deep research indicators
        if any(word in combined_text for word in ['comprehensive', 'thorough', 'detailed', 'in-depth', 'extensive']):
            return 'deep'
        
        # Shallow research indicators
        if any(word in combined_text for word in ['brief', 'quick', 'overview', 'summary', 'basic']):
            return 'shallow'
        
        return 'medium'
    
    def _identify_fact_checkable_claims(self, content: str) -> List[Dict[str, Any]]:
        """Identify claims that need fact-checking"""
        claims = []
        
        # Split content into sentences for analysis
        sentences = content.split('.')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Look for factual claims
            if any(indicator in sentence.lower() for indicator in [
                'according to', 'study shows', 'research indicates', 'statistics show',
                'data reveals', 'experts say', 'reports suggest', '%', 'percent'
            ]):
                claims.append({
                    'claim': sentence,
                    'type': 'statistical_or_study_based',
                    'priority': 'high'
                })
            
            # Look for definitive statements
            elif any(indicator in sentence.lower() for indicator in [
                'is the largest', 'is the smallest', 'is the first', 'is the only',
                'never', 'always', 'all', 'none', 'every'
            ]):
                claims.append({
                    'claim': sentence,
                    'type': 'definitive_statement',
                    'priority': 'medium'
                })
        
        return claims
    
    def _determine_required_sources(self, content: str, research_type: str) -> List[str]:
        """Determine what types of sources are needed"""
        sources = ['general_sources']  # Always include general sources
        content_lower = content.lower()
        
        # Add sources based on research type
        type_sources = {
            'academic_research': ['academic_journals', 'university_databases', 'scholarly_articles'],
            'current_events': ['news_outlets', 'press_releases', 'official_statements'],
            'historical_research': ['historical_archives', 'historical_databases', 'primary_sources'],
            'statistical_analysis': ['statistical_databases', 'government_data', 'survey_data'],
            'fact_checking': ['authoritative_sources', 'expert_opinions', 'primary_sources']
        }
        
        sources.extend(type_sources.get(research_type, []))
        
        # Add sources based on content keywords
        if any(word in content_lower for word in ['government', 'policy', 'law']):
            sources.append('government_sources')
        
        if any(word in content_lower for word in ['medical', 'health', 'disease']):
            sources.append('medical_sources')
        
        if any(word in content_lower for word in ['technology', 'tech', 'software']):
            sources.append('technical_sources')
        
        return list(set(sources))  # Remove duplicates
    
    def _assess_research_urgency(self, content: str, user_preferences: Optional[Dict[str, Any]]) -> str:
        """Assess how urgent the research is"""
        if user_preferences and 'urgency' in user_preferences:
            return user_preferences['urgency']
        
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['urgent', 'asap', 'immediately', 'rush']):
            return 'high'
        elif any(word in content_lower for word in ['when possible', 'no rush', 'eventually']):
            return 'low'
        
        return 'normal'
    
    def _assess_research_complexity(self, task_request: TaskRequest) -> str:
        """Assess overall research complexity"""
        complexity_score = 0
        content_lower = task_request.content.lower()
        
        # Add complexity based on content indicators
        if any(word in content_lower for word in ['comprehensive', 'detailed', 'thorough']):
            complexity_score += 2
        
        if any(word in content_lower for word in ['compare', 'analysis', 'evaluate']):
            complexity_score += 1
        
        if any(word in content_lower for word in ['multiple', 'various', 'different']):
            complexity_score += 1
        
        # Add complexity based on content length
        if len(task_request.content.split()) > 100:
            complexity_score += 1
        
        if complexity_score >= 3:
            return 'high'
        elif complexity_score >= 1:
            return 'medium'
        else:
            return 'low'
    
    def _requires_current_data(self, content: str) -> bool:
        """Check if current/recent data is required"""
        current_indicators = ['current', 'recent', 'latest', 'today', 'now', '2024', '2025']
        return any(indicator in content.lower() for indicator in current_indicators)
    
    def _requires_expert_sources(self, content: str) -> bool:
        """Check if expert sources are required"""
        expert_indicators = ['expert', 'specialist', 'authority', 'professional', 'academic']
        return any(indicator in content.lower() for indicator in expert_indicators)
    
    async def _conduct_research(self, task_request: TaskRequest, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct the actual research using CrewAI"""
        try:
            research_task = Task(
                description=f"""
                Conduct {analysis['research_type']} research on the following topic:
                
                Topic: {task_request.content}
                Research Depth: {analysis['depth']}
                Required Sources: {', '.join(analysis['sources_needed'])}
                Context: {task_request.context or 'None provided'}
                
                Research Requirements:
                1. Gather accurate, up-to-date information
                2. Verify facts and claims where possible
                3. Identify multiple perspectives on the topic
                4. Note any conflicting information or uncertainties
                5. Provide source recommendations for further verification
                
                Focus Areas:
                - Key facts and figures
                - Current status and recent developments
                - Expert opinions and authoritative sources
                - Historical context where relevant
                - Implications and significance
                
                {self._get_research_type_instructions(analysis['research_type'])}
                """,
                agent=self.crew_agent,
                expected_output="Comprehensive research findings with verified information and source recommendations"
            )
            
            crew = Crew(
                agents=[self.crew_agent],
                tasks=[research_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            return {
                'research_findings': str(result),
                'research_type': analysis['research_type'],
                'depth': analysis['depth'],
                'sources_consulted': analysis['sources_needed']
            }
            
        except Exception as e:
            logger.error("Research execution failed", error=str(e))
            return {
                'research_findings': f"Research error: {str(e)}",
                'research_type': analysis['research_type'],
                'error': str(e)
            }
    
    def _get_research_type_instructions(self, research_type: str) -> str:
        """Get specific instructions for research type"""
        instructions = {
            'fact_checking': """
            Special Focus for Fact-Checking:
            - Verify specific claims and statements
            - Check statistical accuracy
            - Validate dates and figures
            - Identify potential misinformation
            - Rate confidence level for each fact
            """,
            'academic_research': """
            Special Focus for Academic Research:
            - Prioritize peer-reviewed sources
            - Include recent scholarly work
            - Note methodology and sample sizes
            - Identify research gaps or limitations
            - Consider theoretical frameworks
            """,
            'current_events': """
            Special Focus for Current Events:
            - Emphasize recent developments
            - Include multiple news sources
            - Note timeline of events
            - Consider ongoing implications
            - Identify emerging trends
            """,
            'historical_research': """
            Special Focus for Historical Research:
            - Establish chronological timeline
            - Include primary source references
            - Note historical context and significance
            - Consider multiple historical perspectives
            - Identify cause-and-effect relationships
            """
        }
        
        return instructions.get(research_type, "Conduct thorough, accurate research with attention to source quality.")
    
    async def _validate_research_findings(self, research_results: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and cross-check research findings"""
        try:
            # Perform fact-checking on key claims
            fact_check_results = []
            
            for claim_info in analysis.get('fact_checkable_claims', []):
                claim = claim_info['claim']
                
                validation_task = Task(
                    description=f"""
                    Fact-check and validate the following claim:
                    
                    Claim: {claim}
                    Context: Research findings about the main topic
                    
                    Validation Requirements:
                    1. Assess the accuracy of the claim
                    2. Identify supporting or contradicting evidence
                    3. Rate confidence level (0-1)
                    4. Suggest verification sources
                    5. Note any limitations or uncertainties
                    
                    Provide a clear assessment of the claim's validity.
                    """,
                    agent=self.crew_agent,
                    expected_output="Fact-check assessment with confidence rating and verification recommendations"
                )
                
                crew = Crew(
                    agents=[self.crew_agent],
                    tasks=[validation_task],
                    verbose=True
                )
                
                validation_result = crew.kickoff()
                
                fact_check_results.append({
                    'claim': claim,
                    'validation': str(validation_result),
                    'priority': claim_info['priority']
                })
            
            return {
                **research_results,
                'fact_check_results': fact_check_results,
                'validation_performed': True,
                'overall_confidence': self._calculate_overall_confidence(fact_check_results)
            }
            
        except Exception as e:
            logger.error("Research validation failed", error=str(e))
            return {
                **research_results,
                'validation_performed': False,
                'validation_error': str(e)
            }
    
    def _calculate_overall_confidence(self, fact_check_results: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence in research findings"""
        if not fact_check_results:
            return 0.8  # Default confidence when no fact-checking performed
        
        # Simple confidence calculation based on validation results
        # In production, this would be more sophisticated
        high_priority_checks = [r for r in fact_check_results if r['priority'] == 'high']
        
        if high_priority_checks:
            # If we have high-priority fact checks, base confidence on those
            return 0.85  # Placeholder - would analyze validation text
        else:
            return 0.8
    
    async def _format_research_output(self, validated_results: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Format research findings into structured output"""
        try:
            formatting_task = Task(
                description=f"""
                Format the following research findings into a clear, structured report:
                
                Research Type: {analysis['research_type']}
                Research Findings: {validated_results['research_findings']}
                
                Fact-Check Results: {validated_results.get('fact_check_results', 'None performed')}
                
                Format Requirements:
                1. Executive Summary
                2. Key Findings (bullet points)
                3. Detailed Analysis
                4. Source Recommendations
                5. Confidence Assessment
                6. Areas for Further Research (if applicable)
                
                Make the report clear, professional, and actionable.
                Include confidence levels and any limitations or uncertainties.
                """,
                agent=self.crew_agent,
                expected_output="Well-formatted research report with clear structure and actionable insights"
            )
            
            crew = Crew(
                agents=[self.crew_agent],
                tasks=[formatting_task],
                verbose=True
            )
            
            result = crew.kickoff()
            return str(result)
            
        except Exception as e:
            logger.error("Research formatting failed", error=str(e))
            return f"Research Results:\n\n{validated_results.get('research_findings', 'No findings available')}"
    
    def _calculate_research_confidence(self, analysis: Dict[str, Any], validated_results: Dict[str, Any]) -> float:
        """Calculate confidence score for research results"""
        try:
            base_confidence = 0.8
            
            # Adjust based on research type expertise
            research_type = analysis.get('research_type', 'general')
            type_confidence = self.research_expertise.get(research_type, 0.8)
            
            # Adjust based on validation results
            if validated_results.get('validation_performed', False):
                overall_confidence = validated_results.get('overall_confidence', 0.8)
                validation_boost = (overall_confidence - 0.5) * 0.2  # Scale validation impact
            else:
                validation_boost = -0.1  # Slight penalty for no validation
            
            # Adjust based on complexity
            complexity = analysis.get('estimated_complexity', 'medium')
            complexity_adjustments = {'low': 0.1, 'medium': 0.0, 'high': -0.1}
            complexity_adjustment = complexity_adjustments.get(complexity, 0.0)
            
            final_confidence = (base_confidence + type_confidence) / 2 + validation_boost + complexity_adjustment
            return round(min(max(final_confidence, 0.1), 1.0), 2)
            
        except Exception:
            return 0.8
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get research agent capabilities"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "specializations": self.specializations,
            "research_types": list(self.research_expertise.keys()),
            "expertise_levels": self.research_expertise,
            "supported_tasks": ["research", "fact_check", "verify", "investigate", "analyze"],
            "source_types": [
                "academic_journals", "news_outlets", "government_data", 
                "statistical_databases", "expert_opinions", "historical_records"
            ],
            "research_depths": ["shallow", "medium", "deep"],
            "fact_checking": True,
            "real_time_data": False,  # Would require external APIs
            "languages": ["English"],
            "collaboration_ready": True,
            "max_research_complexity": "high"
        }

