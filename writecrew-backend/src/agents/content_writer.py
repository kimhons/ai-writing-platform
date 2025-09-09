"""
Content Writer Agent - Primary Writing and Content Creation
Specialized CrewAI agent for generating high-quality written content
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import structlog

from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from ..models.task import TaskRequest, TaskResponse
from ..services.ai_providers import AIProviderService
from ..utils.prompts import CONTENT_WRITER_PROMPTS
from .base_agent import BaseWritingAgent

logger = structlog.get_logger(__name__)


class ContentGenerationTool(BaseTool):
    """Tool for generating various types of content"""
    
    name: str = "content_generator"
    description: str = "Generate high-quality written content based on specifications"
    
    def _run(self, content_type: str, topic: str, requirements: Dict[str, Any] = None) -> str:
        """Generate content based on type and requirements"""
        try:
            requirements = requirements or {}
            
            # Content type templates
            templates = {
                'article': self._generate_article_structure,
                'blog_post': self._generate_blog_structure,
                'story': self._generate_story_structure,
                'essay': self._generate_essay_structure,
                'report': self._generate_report_structure,
                'email': self._generate_email_structure,
                'social_media': self._generate_social_structure
            }
            
            generator = templates.get(content_type, self._generate_generic_structure)
            return generator(topic, requirements)
            
        except Exception as e:
            logger.error("Content generation failed", error=str(e))
            return f"Error generating content: {str(e)}"
    
    def _generate_article_structure(self, topic: str, requirements: Dict[str, Any]) -> str:
        """Generate article structure"""
        word_count = requirements.get('word_count', 800)
        tone = requirements.get('tone', 'informative')
        
        return f"""
# {topic}

## Introduction
[Hook the reader with an engaging opening that introduces {topic}]

## Main Content
[Develop the core ideas about {topic} with supporting evidence and examples]

### Key Point 1
[First major point with detailed explanation]

### Key Point 2
[Second major point with supporting details]

### Key Point 3
[Third major point with analysis]

## Conclusion
[Summarize key insights and provide actionable takeaways]

Target: {word_count} words | Tone: {tone}
"""
    
    def _generate_blog_structure(self, topic: str, requirements: Dict[str, Any]) -> str:
        """Generate blog post structure"""
        return f"""
# {topic}: [Compelling Headline]

## Hook
[Start with a question, statistic, or relatable scenario]

## Problem/Challenge
[Identify the main issue your readers face regarding {topic}]

## Solution/Insights
[Provide valuable solutions and actionable advice]

## Examples/Case Studies
[Include real-world examples or personal experiences]

## Call to Action
[Encourage reader engagement and next steps]

Style: Conversational, engaging, SEO-optimized
"""
    
    def _generate_story_structure(self, topic: str, requirements: Dict[str, Any]) -> str:
        """Generate story structure"""
        genre = requirements.get('genre', 'general fiction')
        
        return f"""
# {topic}

## Setting
[Establish time, place, and atmosphere for the story about {topic}]

## Characters
[Introduce main character(s) with clear motivations]

## Inciting Incident
[The event that sets the story in motion]

## Rising Action
[Build tension and develop conflict around {topic}]

## Climax
[The turning point or most intense moment]

## Resolution
[Conclude the story with satisfying closure]

Genre: {genre} | Focus: Character-driven narrative
"""
    
    def _generate_essay_structure(self, topic: str, requirements: Dict[str, Any]) -> str:
        """Generate essay structure"""
        essay_type = requirements.get('type', 'argumentative')
        
        return f"""
# {topic}

## Introduction
[Present thesis statement about {topic}]

## Body Paragraph 1
[First supporting argument with evidence]

## Body Paragraph 2
[Second supporting argument with analysis]

## Body Paragraph 3
[Third supporting argument or counterargument]

## Conclusion
[Restate thesis and synthesize arguments]

Type: {essay_type} | Academic tone with clear argumentation
"""
    
    def _generate_report_structure(self, topic: str, requirements: Dict[str, Any]) -> str:
        """Generate report structure"""
        return f"""
# {topic} - Report

## Executive Summary
[Brief overview of key findings and recommendations]

## Introduction
[Background and objectives of the {topic} analysis]

## Methodology
[How the research/analysis was conducted]

## Findings
[Detailed results and data analysis]

## Analysis
[Interpretation of findings and implications]

## Recommendations
[Actionable suggestions based on analysis]

## Conclusion
[Summary and next steps]

Format: Professional, data-driven, objective
"""
    
    def _generate_email_structure(self, topic: str, requirements: Dict[str, Any]) -> str:
        """Generate email structure"""
        purpose = requirements.get('purpose', 'informational')
        
        return f"""
Subject: [Clear, specific subject line about {topic}]

Dear [Recipient],

## Opening
[Friendly greeting and context for writing about {topic}]

## Main Message
[Core information or request related to {topic}]

## Action Items
[Clear next steps or requests if applicable]

## Closing
[Professional closing with contact information]

Best regards,
[Your name]

Purpose: {purpose} | Tone: Professional yet approachable
"""
    
    def _generate_social_structure(self, topic: str, requirements: Dict[str, Any]) -> str:
        """Generate social media structure"""
        platform = requirements.get('platform', 'general')
        
        return f"""
# Social Media Post: {topic}

## Hook
[Attention-grabbing opening line about {topic}]

## Value
[Key insight, tip, or information]

## Engagement
[Question or call-to-action to encourage interaction]

## Hashtags
[Relevant hashtags for {topic}]

Platform: {platform} | Style: Engaging, concise, shareable
"""
    
    def _generate_generic_structure(self, topic: str, requirements: Dict[str, Any]) -> str:
        """Generate generic content structure"""
        return f"""
# {topic}

## Overview
[Introduction to {topic} and its significance]

## Main Content
[Detailed exploration of {topic} with supporting information]

## Key Points
[Important takeaways and insights]

## Conclusion
[Summary and final thoughts on {topic}]

Style: Clear, informative, well-structured
"""


class ContentWriterAgent(BaseWritingAgent):
    """Content Writer Agent for primary writing tasks"""
    
    def __init__(self, ai_provider_service: AIProviderService):
        super().__init__(
            agent_id="content_writer",
            name="Content Writer",
            ai_provider_service=ai_provider_service
        )
        
        # Initialize CrewAI agent
        self.crew_agent = Agent(
            role="Expert Content Writer and Storyteller",
            goal="Create compelling, well-structured, and engaging written content across various formats and genres",
            backstory=CONTENT_WRITER_PROMPTS["backstory"],
            verbose=True,
            allow_delegation=False,
            tools=[ContentGenerationTool()],
            llm=ai_provider_service.get_primary_llm(),
            max_iter=3,
            memory=True
        )
        
        # Specializations
        self.specializations = [
            "Article writing",
            "Blog posts", 
            "Creative fiction",
            "Business content",
            "Technical documentation",
            "Email composition",
            "Social media content",
            "Academic essays"
        ]
        
        # Content type expertise
        self.content_expertise = {
            'articles': 0.95,
            'blog_posts': 0.90,
            'stories': 0.85,
            'essays': 0.88,
            'reports': 0.82,
            'emails': 0.92,
            'social_media': 0.87,
            'technical_docs': 0.80
        }
        
        logger.info("Content Writer Agent initialized", specializations=len(self.specializations))
    
    async def execute_task(self, task_request: TaskRequest) -> TaskResponse:
        """Execute content writing task"""
        try:
            logger.info("Executing content writing task", task_id=task_request.task_id)
            
            # Analyze content requirements
            content_analysis = await self._analyze_content_requirements(task_request)
            
            # Generate content structure
            structure = await self._generate_content_structure(task_request, content_analysis)
            
            # Create detailed content
            content = await self._create_content(task_request, structure, content_analysis)
            
            # Enhance and polish
            final_content = await self._enhance_content(content, content_analysis)
            
            # Create response
            response = TaskResponse(
                task_id=task_request.task_id,
                agent_id=self.agent_id,
                status="completed",
                content=final_content,
                metadata={
                    "content_type": content_analysis.get("content_type"),
                    "word_count": len(final_content.split()),
                    "tone": content_analysis.get("tone"),
                    "structure_used": structure.get("type"),
                    "enhancements_applied": content_analysis.get("enhancements", [])
                },
                confidence_score=self._calculate_confidence(task_request, content_analysis),
                processing_time=self._get_processing_time()
            )
            
            logger.info(
                "Content writing task completed",
                task_id=task_request.task_id,
                word_count=response.metadata["word_count"],
                confidence=response.confidence_score
            )
            
            return response
            
        except Exception as e:
            logger.error("Content writing task failed", task_id=task_request.task_id, error=str(e))
            return self._create_error_response(task_request, str(e))
    
    async def _analyze_content_requirements(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Analyze content requirements and specifications"""
        try:
            # Extract content type from task
            content_type = self._detect_content_type(task_request.content, task_request.task_type)
            
            # Analyze tone and style requirements
            tone = self._detect_required_tone(task_request.content, task_request.context)
            
            # Estimate word count requirements
            word_count = self._estimate_word_count(task_request.content, task_request.user_preferences)
            
            # Identify target audience
            audience = self._identify_target_audience(task_request.context, task_request.user_preferences)
            
            # Determine required enhancements
            enhancements = self._identify_required_enhancements(task_request)
            
            return {
                "content_type": content_type,
                "tone": tone,
                "word_count": word_count,
                "audience": audience,
                "enhancements": enhancements,
                "complexity": self._assess_complexity(task_request),
                "research_needed": self._needs_research(task_request.content),
                "creativity_level": self._assess_creativity_needs(task_request.content)
            }
            
        except Exception as e:
            logger.error("Content analysis failed", error=str(e))
            return {
                "content_type": "article",
                "tone": "professional",
                "word_count": 500,
                "audience": "general",
                "enhancements": [],
                "complexity": "medium"
            }
    
    def _detect_content_type(self, content: str, task_type: str) -> str:
        """Detect the type of content to be created"""
        content_lower = content.lower()
        
        # Direct type indicators
        type_keywords = {
            'blog_post': ['blog', 'blog post', 'post'],
            'article': ['article', 'news', 'feature'],
            'story': ['story', 'fiction', 'narrative', 'tale'],
            'essay': ['essay', 'academic', 'thesis'],
            'report': ['report', 'analysis', 'findings'],
            'email': ['email', 'message', 'correspondence'],
            'social_media': ['tweet', 'facebook', 'instagram', 'social'],
            'technical_docs': ['documentation', 'manual', 'guide', 'instructions']
        }
        
        for content_type, keywords in type_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                return content_type
        
        # Fallback based on task type
        if task_type in ['create', 'write', 'compose']:
            return 'article'  # Default
        
        return 'article'
    
    def _detect_required_tone(self, content: str, context: Optional[str]) -> str:
        """Detect required tone from content and context"""
        combined_text = f"{content} {context or ''}".lower()
        
        tone_indicators = {
            'formal': ['formal', 'professional', 'business', 'academic'],
            'casual': ['casual', 'friendly', 'conversational', 'relaxed'],
            'persuasive': ['convince', 'persuade', 'argue', 'sell'],
            'informative': ['explain', 'inform', 'educate', 'teach'],
            'creative': ['creative', 'imaginative', 'artistic', 'expressive'],
            'humorous': ['funny', 'humor', 'joke', 'entertaining']
        }
        
        for tone, keywords in tone_indicators.items():
            if any(keyword in combined_text for keyword in keywords):
                return tone
        
        return 'professional'  # Default tone
    
    def _estimate_word_count(self, content: str, user_preferences: Optional[Dict[str, Any]]) -> int:
        """Estimate required word count"""
        # Check user preferences first
        if user_preferences and 'word_count' in user_preferences:
            return user_preferences['word_count']
        
        # Estimate based on content complexity
        content_length = len(content.split())
        
        if content_length < 10:
            return 300  # Short content
        elif content_length < 50:
            return 800  # Medium content
        else:
            return 1500  # Long content
    
    def _identify_target_audience(self, context: Optional[str], user_preferences: Optional[Dict[str, Any]]) -> str:
        """Identify target audience"""
        if user_preferences and 'audience' in user_preferences:
            return user_preferences['audience']
        
        if context:
            context_lower = context.lower()
            if any(word in context_lower for word in ['expert', 'professional', 'technical']):
                return 'expert'
            elif any(word in context_lower for word in ['beginner', 'introduction', 'basic']):
                return 'beginner'
            elif any(word in context_lower for word in ['student', 'academic', 'research']):
                return 'academic'
        
        return 'general'
    
    def _identify_required_enhancements(self, task_request: TaskRequest) -> List[str]:
        """Identify required content enhancements"""
        enhancements = []
        content_lower = task_request.content.lower()
        
        if 'seo' in content_lower or 'search' in content_lower:
            enhancements.append('seo_optimization')
        
        if 'engaging' in content_lower or 'compelling' in content_lower:
            enhancements.append('engagement_boost')
        
        if 'data' in content_lower or 'statistics' in content_lower:
            enhancements.append('data_integration')
        
        if 'examples' in content_lower or 'case study' in content_lower:
            enhancements.append('example_integration')
        
        return enhancements
    
    def _assess_complexity(self, task_request: TaskRequest) -> str:
        """Assess content complexity requirements"""
        content_lower = task_request.content.lower()
        
        high_complexity_indicators = [
            'comprehensive', 'detailed', 'in-depth', 'complex', 'advanced', 'thorough'
        ]
        
        low_complexity_indicators = [
            'simple', 'basic', 'brief', 'quick', 'overview', 'summary'
        ]
        
        if any(indicator in content_lower for indicator in high_complexity_indicators):
            return 'high'
        elif any(indicator in content_lower for indicator in low_complexity_indicators):
            return 'low'
        
        return 'medium'
    
    def _needs_research(self, content: str) -> bool:
        """Determine if content requires research"""
        research_indicators = [
            'research', 'facts', 'data', 'statistics', 'current', 'latest', 'trends'
        ]
        
        return any(indicator in content.lower() for indicator in research_indicators)
    
    def _assess_creativity_needs(self, content: str) -> str:
        """Assess creativity level needed"""
        content_lower = content.lower()
        
        high_creativity = ['creative', 'imaginative', 'story', 'fiction', 'artistic']
        low_creativity = ['factual', 'technical', 'report', 'data', 'analysis']
        
        if any(word in content_lower for word in high_creativity):
            return 'high'
        elif any(word in content_lower for word in low_creativity):
            return 'low'
        
        return 'medium'
    
    async def _generate_content_structure(self, task_request: TaskRequest, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content structure using CrewAI"""
        try:
            structure_task = Task(
                description=f"""
                Create a detailed content structure for the following writing task:
                
                Content Type: {analysis['content_type']}
                Topic: {task_request.content}
                Target Audience: {analysis['audience']}
                Tone: {analysis['tone']}
                Word Count: {analysis['word_count']}
                Complexity: {analysis['complexity']}
                
                Generate a comprehensive outline with:
                1. Main sections and subsections
                2. Key points for each section
                3. Suggested content flow
                4. Engagement strategies
                5. Call-to-action elements (if applicable)
                """,
                agent=self.crew_agent,
                expected_output="Detailed content structure with sections, key points, and flow recommendations"
            )
            
            crew = Crew(
                agents=[self.crew_agent],
                tasks=[structure_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            return {
                "type": analysis['content_type'],
                "structure": str(result),
                "sections": self._parse_structure_sections(str(result)),
                "flow": "linear"  # Could be enhanced with AI analysis
            }
            
        except Exception as e:
            logger.error("Structure generation failed", error=str(e))
            return {
                "type": analysis['content_type'],
                "structure": "Basic structure with introduction, main content, and conclusion",
                "sections": ["Introduction", "Main Content", "Conclusion"],
                "flow": "linear"
            }
    
    def _parse_structure_sections(self, structure_text: str) -> List[str]:
        """Parse sections from structure text"""
        try:
            sections = []
            lines = structure_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith('#') or line.startswith('##'):
                    section = line.lstrip('#').strip()
                    if section and section not in sections:
                        sections.append(section)
            
            return sections if sections else ["Introduction", "Main Content", "Conclusion"]
            
        except Exception:
            return ["Introduction", "Main Content", "Conclusion"]
    
    async def _create_content(self, task_request: TaskRequest, structure: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Create the actual content using CrewAI"""
        try:
            content_task = Task(
                description=f"""
                Write high-quality content based on the following specifications:
                
                Topic: {task_request.content}
                Content Type: {analysis['content_type']}
                Structure: {structure['structure']}
                Target Word Count: {analysis['word_count']}
                Tone: {analysis['tone']}
                Audience: {analysis['audience']}
                Complexity Level: {analysis['complexity']}
                
                Additional Context: {task_request.context or 'None provided'}
                
                Requirements:
                - Follow the provided structure closely
                - Maintain consistent tone throughout
                - Include engaging hooks and transitions
                - Provide valuable, actionable content
                - Use appropriate formatting and headers
                - Ensure content flows logically
                
                {self._get_content_type_specific_instructions(analysis['content_type'])}
                """,
                agent=self.crew_agent,
                expected_output=f"Complete {analysis['content_type']} content of approximately {analysis['word_count']} words"
            )
            
            crew = Crew(
                agents=[self.crew_agent],
                tasks=[content_task],
                verbose=True
            )
            
            result = crew.kickoff()
            return str(result)
            
        except Exception as e:
            logger.error("Content creation failed", error=str(e))
            return f"Error creating content: {str(e)}"
    
    def _get_content_type_specific_instructions(self, content_type: str) -> str:
        """Get specific instructions for content type"""
        instructions = {
            'article': "Include compelling headlines, subheadings, and ensure journalistic quality.",
            'blog_post': "Make it conversational, include personal insights, and optimize for engagement.",
            'story': "Focus on character development, plot progression, and vivid descriptions.",
            'essay': "Maintain academic rigor, clear argumentation, and proper citations if needed.",
            'report': "Use data-driven insights, clear methodology, and actionable recommendations.",
            'email': "Keep it concise, professional, and include clear call-to-action.",
            'social_media': "Make it shareable, include hashtags, and optimize for platform.",
            'technical_docs': "Ensure clarity, step-by-step instructions, and proper formatting."
        }
        
        return instructions.get(content_type, "Ensure high quality and reader engagement.")
    
    async def _enhance_content(self, content: str, analysis: Dict[str, Any]) -> str:
        """Enhance content based on requirements"""
        try:
            enhancements = analysis.get('enhancements', [])
            
            if not enhancements:
                return content
            
            enhancement_task = Task(
                description=f"""
                Enhance the following content with these specific improvements:
                {', '.join(enhancements)}
                
                Original Content:
                {content}
                
                Apply the following enhancements:
                - SEO optimization: Add relevant keywords naturally
                - Engagement boost: Improve hooks, transitions, and call-to-actions
                - Data integration: Suggest where statistics or data would strengthen points
                - Example integration: Add relevant examples or case studies
                
                Maintain the original tone and structure while making these improvements.
                """,
                agent=self.crew_agent,
                expected_output="Enhanced content with requested improvements applied"
            )
            
            crew = Crew(
                agents=[self.crew_agent],
                tasks=[enhancement_task],
                verbose=True
            )
            
            result = crew.kickoff()
            return str(result)
            
        except Exception as e:
            logger.error("Content enhancement failed", error=str(e))
            return content  # Return original if enhancement fails
    
    def _calculate_confidence(self, task_request: TaskRequest, analysis: Dict[str, Any]) -> float:
        """Calculate confidence score for the task"""
        try:
            base_confidence = 0.8
            
            # Adjust based on content type expertise
            content_type = analysis.get('content_type', 'article')
            type_confidence = self.content_expertise.get(content_type, 0.8)
            
            # Adjust based on complexity
            complexity = analysis.get('complexity', 'medium')
            complexity_adjustments = {'low': 0.1, 'medium': 0.0, 'high': -0.1}
            complexity_adjustment = complexity_adjustments.get(complexity, 0.0)
            
            # Adjust based on research needs
            if analysis.get('research_needed', False):
                research_adjustment = -0.1  # Lower confidence if research needed
            else:
                research_adjustment = 0.0
            
            final_confidence = base_confidence + complexity_adjustment + research_adjustment
            final_confidence = min(max(final_confidence, 0.1), 1.0)  # Clamp between 0.1 and 1.0
            
            return round(final_confidence, 2)
            
        except Exception:
            return 0.8  # Default confidence
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities and specializations"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "specializations": self.specializations,
            "content_types": list(self.content_expertise.keys()),
            "expertise_levels": self.content_expertise,
            "max_word_count": 5000,
            "supported_tones": ["professional", "casual", "formal", "creative", "persuasive", "informative"],
            "supported_audiences": ["general", "expert", "beginner", "academic", "business"],
            "enhancements": ["seo_optimization", "engagement_boost", "data_integration", "example_integration"],
            "languages": ["English"],  # Could be expanded
            "collaboration_ready": True
        }

