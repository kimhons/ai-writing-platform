"""
Quality Assurance System
Comprehensive content quality monitoring, assessment, and improvement recommendations
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import re
import json
import statistics
from collections import defaultdict

from ..services.ai_provider_service import AIProviderService
from ..config.settings import settings

logger = logging.getLogger(__name__)

class QualityLevel(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    UNACCEPTABLE = "unacceptable"

class QualityDimension(Enum):
    CLARITY = "clarity"
    COHERENCE = "coherence"
    GRAMMAR = "grammar"
    STYLE = "style"
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    ENGAGEMENT = "engagement"
    STRUCTURE = "structure"
    TONE = "tone"
    READABILITY = "readability"

class ContentType(Enum):
    ARTICLE = "article"
    BLOG_POST = "blog_post"
    ACADEMIC_PAPER = "academic_paper"
    BUSINESS_DOCUMENT = "business_document"
    CREATIVE_WRITING = "creative_writing"
    TECHNICAL_DOCUMENTATION = "technical_documentation"
    LEGAL_DOCUMENT = "legal_document"
    MEDICAL_DOCUMENT = "medical_document"
    EMAIL = "email"
    SOCIAL_MEDIA = "social_media"

@dataclass
class QualityMetric:
    """Individual quality assessment metric"""
    dimension: QualityDimension
    score: float  # 0.0 - 5.0 scale
    level: QualityLevel
    explanation: str
    suggestions: List[str] = field(default_factory=list)
    confidence: float = 1.0

@dataclass
class QualityIssue:
    """Specific quality issue identified in content"""
    id: str
    type: str
    severity: str  # low, medium, high, critical
    description: str
    location: Tuple[int, int]  # start, end positions
    suggestion: str
    example: Optional[str] = None
    confidence: float = 1.0

@dataclass
class QualityReport:
    """Comprehensive quality assessment report"""
    content_id: str
    content_type: ContentType
    overall_score: float  # 0.0 - 5.0 scale
    overall_level: QualityLevel
    word_count: int
    readability_score: float
    metrics: List[QualityMetric] = field(default_factory=list)
    issues: List[QualityIssue] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    improvement_priority: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    agent_id: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)

class QualityAssuranceSystem:
    """
    Comprehensive quality assurance system that monitors, assesses,
    and provides improvement recommendations for all content
    """
    
    def __init__(self, ai_provider_service: AIProviderService):
        self.ai_provider_service = ai_provider_service
        self.quality_standards = self._initialize_quality_standards()
        self.performance_metrics = {
            'total_assessments': 0,
            'average_quality_score': 0.0,
            'quality_trends': defaultdict(list),
            'agent_performance': defaultdict(list),
            'improvement_rate': 0.0
        }
        
        # Quality thresholds by content type
        self.quality_thresholds = {
            ContentType.ACADEMIC_PAPER: 4.5,
            ContentType.LEGAL_DOCUMENT: 4.5,
            ContentType.MEDICAL_DOCUMENT: 4.5,
            ContentType.BUSINESS_DOCUMENT: 4.0,
            ContentType.TECHNICAL_DOCUMENTATION: 4.0,
            ContentType.ARTICLE: 3.5,
            ContentType.BLOG_POST: 3.0,
            ContentType.EMAIL: 3.0,
            ContentType.CREATIVE_WRITING: 3.5,
            ContentType.SOCIAL_MEDIA: 2.5
        }
    
    def _initialize_quality_standards(self) -> Dict[str, Any]:
        """Initialize quality standards and benchmarks"""
        return {
            'readability': {
                'flesch_kincaid_min': 8.0,
                'flesch_kincaid_max': 12.0,
                'avg_sentence_length_max': 20,
                'complex_words_max': 0.15
            },
            'grammar': {
                'error_rate_max': 0.02,  # 2% error rate
                'passive_voice_max': 0.20,  # 20% passive voice
                'sentence_variety_min': 0.7
            },
            'structure': {
                'paragraph_length_max': 150,
                'paragraph_length_min': 30,
                'heading_ratio_min': 0.1,
                'transition_density_min': 0.05
            },
            'style': {
                'tone_consistency_min': 0.8,
                'voice_consistency_min': 0.8,
                'formality_variance_max': 0.3
            }
        }
    
    async def assess_quality(self, content: str, content_type: ContentType,
                           agent_id: str = "", context: Dict[str, Any] = None) -> QualityReport:
        """
        Comprehensive quality assessment of content
        """
        start_time = datetime.utcnow()
        content_id = f"qa_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        try:
            logger.info(f"Starting quality assessment for content {content_id}")
            
            # Step 1: Basic content analysis
            basic_metrics = self._analyze_basic_metrics(content)
            
            # Step 2: Readability analysis
            readability_score = self._calculate_readability(content)
            
            # Step 3: Quality dimension assessment
            quality_metrics = await self._assess_quality_dimensions(content, content_type)
            
            # Step 4: Issue identification
            quality_issues = await self._identify_quality_issues(content, content_type)
            
            # Step 5: Generate comprehensive report
            report = self._generate_quality_report(
                content_id, content, content_type, agent_id,
                basic_metrics, readability_score, quality_metrics,
                quality_issues, start_time
            )
            
            # Step 6: Update performance metrics
            self._update_performance_metrics(report, agent_id)
            
            logger.info(f"Quality assessment completed for {content_id} - Score: {report.overall_score:.2f}")
            return report
            
        except Exception as e:
            logger.error(f"Error in quality assessment: {str(e)}")
            raise
    
    def _analyze_basic_metrics(self, content: str) -> Dict[str, Any]:
        """Analyze basic content metrics"""
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        paragraphs = content.split('\n\n')
        
        return {
            'word_count': len(words),
            'sentence_count': len([s for s in sentences if s.strip()]),
            'paragraph_count': len([p for p in paragraphs if p.strip()]),
            'avg_words_per_sentence': len(words) / max(1, len(sentences)),
            'avg_sentences_per_paragraph': len(sentences) / max(1, len(paragraphs)),
            'character_count': len(content),
            'unique_words': len(set(word.lower() for word in words if word.isalpha()))
        }
    
    def _calculate_readability(self, content: str) -> float:
        """Calculate Flesch-Kincaid readability score"""
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        syllables = sum(self._count_syllables(word) for word in words)
        
        if len(sentences) == 0 or len(words) == 0:
            return 0.0
        
        # Flesch-Kincaid Grade Level
        avg_sentence_length = len(words) / len(sentences)
        avg_syllables_per_word = syllables / len(words)
        
        fk_score = (0.39 * avg_sentence_length) + (11.8 * avg_syllables_per_word) - 15.59
        
        # Convert to 0-5 scale (lower grade level = higher readability)
        readability_score = max(0, min(5, 5 - (fk_score - 8) / 4))
        
        return readability_score
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (simplified algorithm)"""
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel
        
        # Handle silent 'e'
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
        
        return max(1, syllable_count)
    
    async def _assess_quality_dimensions(self, content: str, 
                                       content_type: ContentType) -> List[QualityMetric]:
        """Assess quality across multiple dimensions using AI"""
        metrics = []
        
        # AI-powered quality assessment
        ai_metrics = await self._assess_dimensions_ai(content, content_type)
        
        # Rule-based quality assessment
        rule_metrics = self._assess_dimensions_rules(content, content_type)
        
        # Combine AI and rule-based assessments
        combined_metrics = self._combine_quality_assessments(ai_metrics, rule_metrics)
        
        return combined_metrics
    
    async def _assess_dimensions_ai(self, content: str, 
                                  content_type: ContentType) -> List[QualityMetric]:
        """Use AI to assess quality dimensions"""
        try:
            prompt = f"""
            Assess the quality of the following {content_type.value} content across these dimensions:
            
            1. CLARITY: How clear and understandable is the content?
            2. COHERENCE: How well do ideas flow and connect?
            3. GRAMMAR: Grammar, punctuation, and language correctness
            4. STYLE: Writing style appropriateness for the content type
            5. ACCURACY: Factual accuracy and precision
            6. COMPLETENESS: How complete and comprehensive is the content?
            7. ENGAGEMENT: How engaging and interesting is the content?
            8. STRUCTURE: Organization and logical structure
            9. TONE: Appropriateness of tone for the content type
            10. READABILITY: Ease of reading and comprehension
            
            For each dimension, provide:
            - Score (0.0-5.0): 5.0 = Excellent, 4.0 = Good, 3.0 = Acceptable, 2.0 = Poor, 1.0 = Unacceptable
            - Level: excellent/good/acceptable/poor/unacceptable
            - Explanation: Brief explanation of the score
            - Suggestions: 2-3 specific improvement suggestions
            - Confidence: How confident you are in this assessment (0.0-1.0)
            
            Content to assess:
            {content[:1500]}  # Limit content for AI processing
            
            Return as JSON array:
            [
                {{
                    "dimension": "clarity",
                    "score": 4.2,
                    "level": "good",
                    "explanation": "Content is generally clear with minor ambiguities",
                    "suggestions": ["Clarify technical terms", "Add examples"],
                    "confidence": 0.9
                }}
            ]
            """
            
            response = await self.ai_provider_service.generate_content(
                prompt=prompt,
                provider="openai",
                model="gpt-4",
                max_tokens=2000,
                temperature=0.1
            )
            
            # Parse AI response
            ai_data = json.loads(response.get('content', '[]'))
            metrics = []
            
            for metric_data in ai_data:
                metric = QualityMetric(
                    dimension=QualityDimension(metric_data.get('dimension', 'clarity')),
                    score=float(metric_data.get('score', 3.0)),
                    level=QualityLevel(metric_data.get('level', 'acceptable')),
                    explanation=metric_data.get('explanation', ''),
                    suggestions=metric_data.get('suggestions', []),
                    confidence=float(metric_data.get('confidence', 0.8))
                )
                metrics.append(metric)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error in AI quality assessment: {str(e)}")
            return []
    
    def _assess_dimensions_rules(self, content: str, 
                               content_type: ContentType) -> List[QualityMetric]:
        """Rule-based quality assessment"""
        metrics = []
        basic_metrics = self._analyze_basic_metrics(content)
        
        # Grammar assessment (simplified)
        grammar_score = self._assess_grammar_rules(content)
        metrics.append(QualityMetric(
            dimension=QualityDimension.GRAMMAR,
            score=grammar_score,
            level=self._score_to_level(grammar_score),
            explanation=f"Grammar score based on error detection: {grammar_score:.1f}/5.0",
            suggestions=self._get_grammar_suggestions(content),
            confidence=0.7
        ))
        
        # Readability assessment
        readability_score = self._calculate_readability(content)
        metrics.append(QualityMetric(
            dimension=QualityDimension.READABILITY,
            score=readability_score,
            level=self._score_to_level(readability_score),
            explanation=f"Readability score: {readability_score:.1f}/5.0",
            suggestions=self._get_readability_suggestions(content, readability_score),
            confidence=0.9
        ))
        
        # Structure assessment
        structure_score = self._assess_structure_rules(content, basic_metrics)
        metrics.append(QualityMetric(
            dimension=QualityDimension.STRUCTURE,
            score=structure_score,
            level=self._score_to_level(structure_score),
            explanation=f"Structure score based on organization: {structure_score:.1f}/5.0",
            suggestions=self._get_structure_suggestions(content, basic_metrics),
            confidence=0.8
        ))
        
        # Completeness assessment
        completeness_score = self._assess_completeness_rules(content, content_type)
        metrics.append(QualityMetric(
            dimension=QualityDimension.COMPLETENESS,
            score=completeness_score,
            level=self._score_to_level(completeness_score),
            explanation=f"Completeness score: {completeness_score:.1f}/5.0",
            suggestions=self._get_completeness_suggestions(content, content_type),
            confidence=0.6
        ))
        
        return metrics
    
    def _assess_grammar_rules(self, content: str) -> float:
        """Rule-based grammar assessment"""
        issues = 0
        total_checks = 0
        
        # Check for common grammar issues
        sentences = re.split(r'[.!?]+', content)
        
        for sentence in sentences:
            if not sentence.strip():
                continue
            total_checks += 1
            
            # Check for double spaces
            if '  ' in sentence:
                issues += 0.1
            
            # Check for missing capitalization
            if sentence.strip() and not sentence.strip()[0].isupper():
                issues += 0.2
            
            # Check for run-on sentences (very long sentences)
            if len(sentence.split()) > 30:
                issues += 0.1
            
            # Check for sentence fragments (very short sentences)
            if len(sentence.split()) < 3:
                issues += 0.1
        
        # Calculate score (5.0 - penalty for issues)
        if total_checks == 0:
            return 3.0
        
        error_rate = issues / total_checks
        grammar_score = max(1.0, 5.0 - (error_rate * 10))
        
        return min(5.0, grammar_score)
    
    def _assess_structure_rules(self, content: str, basic_metrics: Dict[str, Any]) -> float:
        """Rule-based structure assessment"""
        score = 5.0
        
        # Check paragraph length
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if paragraphs:
            avg_paragraph_length = sum(len(p.split()) for p in paragraphs) / len(paragraphs)
            
            if avg_paragraph_length > 150:  # Too long
                score -= 0.5
            elif avg_paragraph_length < 30:  # Too short
                score -= 0.3
        
        # Check for headings/structure
        heading_patterns = [r'^#{1,6}\s+', r'^[A-Z][^.]*:$', r'^\d+\.\s+']
        has_headings = any(re.search(pattern, content, re.MULTILINE) for pattern in heading_patterns)
        
        if len(content.split()) > 500 and not has_headings:
            score -= 0.5  # Long content should have structure
        
        # Check sentence variety
        sentences = [s.strip() for s in re.split(r'[.!?]+', content) if s.strip()]
        if sentences:
            sentence_lengths = [len(s.split()) for s in sentences]
            if len(set(sentence_lengths)) < len(sentence_lengths) * 0.3:
                score -= 0.3  # Low sentence variety
        
        return max(1.0, score)
    
    def _assess_completeness_rules(self, content: str, content_type: ContentType) -> float:
        """Rule-based completeness assessment"""
        word_count = len(content.split())
        
        # Expected word count ranges by content type
        expected_ranges = {
            ContentType.ARTICLE: (800, 2000),
            ContentType.BLOG_POST: (500, 1500),
            ContentType.ACADEMIC_PAPER: (3000, 8000),
            ContentType.BUSINESS_DOCUMENT: (500, 2000),
            ContentType.CREATIVE_WRITING: (1000, 5000),
            ContentType.TECHNICAL_DOCUMENTATION: (1000, 3000),
            ContentType.LEGAL_DOCUMENT: (1000, 5000),
            ContentType.MEDICAL_DOCUMENT: (1000, 3000),
            ContentType.EMAIL: (50, 300),
            ContentType.SOCIAL_MEDIA: (10, 280)
        }
        
        min_words, max_words = expected_ranges.get(content_type, (100, 1000))
        
        if word_count < min_words * 0.5:
            return 1.0  # Very incomplete
        elif word_count < min_words:
            return 2.5  # Somewhat incomplete
        elif word_count <= max_words:
            return 5.0  # Appropriate length
        elif word_count <= max_words * 1.5:
            return 4.0  # Slightly long
        else:
            return 3.0  # Too long
    
    def _combine_quality_assessments(self, ai_metrics: List[QualityMetric],
                                   rule_metrics: List[QualityMetric]) -> List[QualityMetric]:
        """Combine AI and rule-based assessments"""
        combined = {}
        
        # Add AI metrics
        for metric in ai_metrics:
            combined[metric.dimension] = metric
        
        # Combine with rule-based metrics
        for rule_metric in rule_metrics:
            if rule_metric.dimension in combined:
                ai_metric = combined[rule_metric.dimension]
                # Weighted average (AI: 70%, Rules: 30%)
                combined_score = (ai_metric.score * 0.7) + (rule_metric.score * 0.3)
                combined_confidence = (ai_metric.confidence * 0.7) + (rule_metric.confidence * 0.3)
                
                combined[rule_metric.dimension] = QualityMetric(
                    dimension=rule_metric.dimension,
                    score=combined_score,
                    level=self._score_to_level(combined_score),
                    explanation=f"Combined assessment: {ai_metric.explanation}",
                    suggestions=ai_metric.suggestions + rule_metric.suggestions,
                    confidence=combined_confidence
                )
            else:
                combined[rule_metric.dimension] = rule_metric
        
        return list(combined.values())
    
    async def _identify_quality_issues(self, content: str, 
                                     content_type: ContentType) -> List[QualityIssue]:
        """Identify specific quality issues in content"""
        issues = []
        
        # Rule-based issue detection
        rule_issues = self._identify_issues_rules(content)
        
        # AI-powered issue detection
        ai_issues = await self._identify_issues_ai(content, content_type)
        
        # Combine and deduplicate issues
        all_issues = rule_issues + ai_issues
        unique_issues = self._deduplicate_issues(all_issues)
        
        return unique_issues[:20]  # Limit to 20 issues
    
    def _identify_issues_rules(self, content: str) -> List[QualityIssue]:
        """Rule-based issue identification"""
        issues = []
        issue_counter = 1
        
        # Check for common issues
        
        # 1. Double spaces
        for match in re.finditer(r'  +', content):
            issues.append(QualityIssue(
                id=f"rule_issue_{issue_counter}",
                type="formatting",
                severity="low",
                description="Multiple consecutive spaces",
                location=(match.start(), match.end()),
                suggestion="Replace with single space",
                confidence=0.9
            ))
            issue_counter += 1
        
        # 2. Very long sentences
        sentences = re.split(r'[.!?]+', content)
        pos = 0
        for sentence in sentences:
            if len(sentence.split()) > 35:
                issues.append(QualityIssue(
                    id=f"rule_issue_{issue_counter}",
                    type="readability",
                    severity="medium",
                    description="Very long sentence (>35 words)",
                    location=(pos, pos + len(sentence)),
                    suggestion="Consider breaking into shorter sentences",
                    confidence=0.8
                ))
                issue_counter += 1
            pos += len(sentence) + 1
        
        # 3. Passive voice detection (simplified)
        passive_patterns = [
            r'\b(?:was|were|is|are|been|being)\s+\w+ed\b',
            r'\b(?:was|were|is|are|been|being)\s+\w+en\b'
        ]
        
        for pattern in passive_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                issues.append(QualityIssue(
                    id=f"rule_issue_{issue_counter}",
                    type="style",
                    severity="low",
                    description="Possible passive voice",
                    location=(match.start(), match.end()),
                    suggestion="Consider using active voice",
                    example=match.group(),
                    confidence=0.6
                ))
                issue_counter += 1
        
        # 4. Repetitive words
        words = re.findall(r'\b\w+\b', content.lower())
        word_positions = {}
        for i, word in enumerate(words):
            if word not in word_positions:
                word_positions[word] = []
            word_positions[word].append(i)
        
        for word, positions in word_positions.items():
            if len(positions) > 10 and len(word) > 4:  # Word appears >10 times
                issues.append(QualityIssue(
                    id=f"rule_issue_{issue_counter}",
                    type="style",
                    severity="low",
                    description=f"Word '{word}' used {len(positions)} times",
                    location=(0, len(content)),  # General issue
                    suggestion="Consider using synonyms for variety",
                    confidence=0.7
                ))
                issue_counter += 1
        
        return issues
    
    async def _identify_issues_ai(self, content: str, 
                                content_type: ContentType) -> List[QualityIssue]:
        """AI-powered issue identification"""
        try:
            prompt = f"""
            Identify specific quality issues in the following {content_type.value} content.
            Look for:
            1. Grammar and punctuation errors
            2. Unclear or confusing sentences
            3. Inconsistent tone or style
            4. Missing transitions
            5. Weak or vague language
            6. Structural problems
            7. Factual inconsistencies
            8. Inappropriate tone for content type
            
            For each issue, provide:
            - Type: grammar/clarity/style/structure/tone/accuracy
            - Severity: low/medium/high/critical
            - Description: What the issue is
            - Suggestion: How to fix it
            - Example: The problematic text (if specific)
            - Confidence: How confident you are (0.0-1.0)
            
            Content:
            {content[:1000]}  # Limit for AI processing
            
            Return as JSON array (max 10 issues):
            [
                {{
                    "type": "clarity",
                    "severity": "medium",
                    "description": "Unclear pronoun reference",
                    "suggestion": "Specify what 'it' refers to",
                    "example": "It was important",
                    "confidence": 0.8
                }}
            ]
            """
            
            response = await self.ai_provider_service.generate_content(
                prompt=prompt,
                provider="openai",
                model="gpt-4",
                max_tokens=1000,
                temperature=0.1
            )
            
            # Parse AI response
            ai_data = json.loads(response.get('content', '[]'))
            issues = []
            
            for i, issue_data in enumerate(ai_data[:10]):
                # Find issue location in content
                example = issue_data.get('example', '')
                start_pos = content.find(example) if example else 0
                end_pos = start_pos + len(example) if start_pos != -1 else 0
                
                issue = QualityIssue(
                    id=f"ai_issue_{i+1}",
                    type=issue_data.get('type', 'general'),
                    severity=issue_data.get('severity', 'medium'),
                    description=issue_data.get('description', ''),
                    location=(start_pos, end_pos),
                    suggestion=issue_data.get('suggestion', ''),
                    example=example,
                    confidence=float(issue_data.get('confidence', 0.7))
                )
                issues.append(issue)
            
            return issues
            
        except Exception as e:
            logger.error(f"Error in AI issue identification: {str(e)}")
            return []
    
    def _deduplicate_issues(self, issues: List[QualityIssue]) -> List[QualityIssue]:
        """Remove duplicate issues"""
        unique_issues = []
        seen_descriptions = set()
        
        for issue in issues:
            # Normalize description for comparison
            normalized_desc = issue.description.lower().strip()
            
            if normalized_desc not in seen_descriptions:
                seen_descriptions.add(normalized_desc)
                unique_issues.append(issue)
        
        return unique_issues
    
    def _generate_quality_report(self, content_id: str, content: str,
                               content_type: ContentType, agent_id: str,
                               basic_metrics: Dict[str, Any], readability_score: float,
                               quality_metrics: List[QualityMetric],
                               quality_issues: List[QualityIssue],
                               start_time: datetime) -> QualityReport:
        """Generate comprehensive quality report"""
        
        # Calculate overall score
        if quality_metrics:
            overall_score = sum(metric.score for metric in quality_metrics) / len(quality_metrics)
        else:
            overall_score = 3.0
        
        overall_level = self._score_to_level(overall_score)
        
        # Identify strengths
        strengths = []
        for metric in quality_metrics:
            if metric.score >= 4.0:
                strengths.append(f"Strong {metric.dimension.value}: {metric.explanation}")
        
        # Generate recommendations
        recommendations = []
        
        # Priority issues
        critical_issues = [i for i in quality_issues if i.severity == 'critical']
        high_issues = [i for i in quality_issues if i.severity == 'high']
        
        if critical_issues:
            recommendations.append("Address critical issues immediately")
        if high_issues:
            recommendations.append("Focus on high-severity issues first")
        
        # Metric-based recommendations
        low_metrics = [m for m in quality_metrics if m.score < 3.0]
        for metric in low_metrics:
            recommendations.extend(metric.suggestions[:2])  # Top 2 suggestions
        
        # Content type specific recommendations
        threshold = self.quality_thresholds.get(content_type, 3.5)
        if overall_score < threshold:
            recommendations.append(f"Content quality below {content_type.value} standards")
        
        # Improvement priority
        improvement_priority = []
        sorted_metrics = sorted(quality_metrics, key=lambda m: m.score)
        for metric in sorted_metrics[:3]:  # Top 3 areas for improvement
            improvement_priority.append(metric.dimension.value)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return QualityReport(
            content_id=content_id,
            content_type=content_type,
            overall_score=overall_score,
            overall_level=overall_level,
            word_count=basic_metrics['word_count'],
            readability_score=readability_score,
            metrics=quality_metrics,
            issues=quality_issues,
            strengths=strengths,
            recommendations=list(set(recommendations)),  # Remove duplicates
            improvement_priority=improvement_priority,
            processing_time=processing_time,
            agent_id=agent_id
        )
    
    def _score_to_level(self, score: float) -> QualityLevel:
        """Convert numeric score to quality level"""
        if score >= 4.5:
            return QualityLevel.EXCELLENT
        elif score >= 3.5:
            return QualityLevel.GOOD
        elif score >= 2.5:
            return QualityLevel.ACCEPTABLE
        elif score >= 1.5:
            return QualityLevel.POOR
        else:
            return QualityLevel.UNACCEPTABLE
    
    def _get_grammar_suggestions(self, content: str) -> List[str]:
        """Get grammar improvement suggestions"""
        suggestions = []
        
        if '  ' in content:
            suggestions.append("Remove extra spaces")
        
        sentences = re.split(r'[.!?]+', content)
        long_sentences = [s for s in sentences if len(s.split()) > 25]
        if long_sentences:
            suggestions.append("Break down long sentences for clarity")
        
        return suggestions
    
    def _get_readability_suggestions(self, content: str, score: float) -> List[str]:
        """Get readability improvement suggestions"""
        suggestions = []
        
        if score < 3.0:
            suggestions.extend([
                "Use shorter sentences",
                "Choose simpler words where possible",
                "Break up long paragraphs"
            ])
        elif score < 4.0:
            suggestions.append("Consider simplifying complex sentences")
        
        return suggestions
    
    def _get_structure_suggestions(self, content: str, 
                                 basic_metrics: Dict[str, Any]) -> List[str]:
        """Get structure improvement suggestions"""
        suggestions = []
        
        if basic_metrics['word_count'] > 500:
            if not re.search(r'^#{1,6}\s+', content, re.MULTILINE):
                suggestions.append("Add headings to improve structure")
        
        if basic_metrics['avg_sentences_per_paragraph'] > 8:
            suggestions.append("Break up long paragraphs")
        
        return suggestions
    
    def _get_completeness_suggestions(self, content: str, 
                                    content_type: ContentType) -> List[str]:
        """Get completeness improvement suggestions"""
        suggestions = []
        word_count = len(content.split())
        
        expected_ranges = {
            ContentType.ARTICLE: (800, 2000),
            ContentType.BLOG_POST: (500, 1500),
            ContentType.ACADEMIC_PAPER: (3000, 8000),
            ContentType.BUSINESS_DOCUMENT: (500, 2000),
        }
        
        min_words, max_words = expected_ranges.get(content_type, (100, 1000))
        
        if word_count < min_words:
            suggestions.append(f"Content may be too short for {content_type.value}")
        elif word_count > max_words * 1.5:
            suggestions.append(f"Content may be too long for {content_type.value}")
        
        return suggestions
    
    def _update_performance_metrics(self, report: QualityReport, agent_id: str):
        """Update quality assurance performance metrics"""
        self.performance_metrics['total_assessments'] += 1
        
        # Update average quality score
        current_avg = self.performance_metrics['average_quality_score']
        total_assessments = self.performance_metrics['total_assessments']
        
        self.performance_metrics['average_quality_score'] = (
            (current_avg * (total_assessments - 1) + report.overall_score) / 
            total_assessments
        )
        
        # Track quality trends
        self.performance_metrics['quality_trends'][report.content_type.value].append(
            report.overall_score
        )
        
        # Track agent performance
        if agent_id:
            self.performance_metrics['agent_performance'][agent_id].append(
                report.overall_score
            )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get quality assurance performance metrics"""
        # Calculate improvement rate
        improvement_rate = 0.0
        for content_type, scores in self.performance_metrics['quality_trends'].items():
            if len(scores) >= 10:
                recent_avg = statistics.mean(scores[-5:])
                earlier_avg = statistics.mean(scores[-10:-5])
                if earlier_avg > 0:
                    improvement_rate += (recent_avg - earlier_avg) / earlier_avg
        
        if self.performance_metrics['quality_trends']:
            improvement_rate /= len(self.performance_metrics['quality_trends'])
        
        # Agent performance summary
        agent_summary = {}
        for agent_id, scores in self.performance_metrics['agent_performance'].items():
            if scores:
                agent_summary[agent_id] = {
                    'average_score': statistics.mean(scores),
                    'total_assessments': len(scores),
                    'trend': 'improving' if len(scores) >= 5 and 
                            statistics.mean(scores[-3:]) > statistics.mean(scores[-5:-2]) 
                            else 'stable'
                }
        
        return {
            'total_assessments': self.performance_metrics['total_assessments'],
            'average_quality_score': self.performance_metrics['average_quality_score'],
            'improvement_rate': improvement_rate * 100,
            'quality_trends': dict(self.performance_metrics['quality_trends']),
            'agent_performance': agent_summary,
            'quality_distribution': self._get_quality_distribution()
        }
    
    def _get_quality_distribution(self) -> Dict[str, int]:
        """Get distribution of quality levels"""
        distribution = {level.value: 0 for level in QualityLevel}
        
        for scores in self.performance_metrics['quality_trends'].values():
            for score in scores:
                level = self._score_to_level(score)
                distribution[level.value] += 1
        
        return distribution
    
    async def get_improvement_recommendations(self, agent_id: str = None) -> Dict[str, Any]:
        """Get personalized improvement recommendations"""
        recommendations = {
            'general': [],
            'agent_specific': {},
            'system_wide': []
        }
        
        # General recommendations based on trends
        avg_score = self.performance_metrics['average_quality_score']
        if avg_score < 3.5:
            recommendations['general'].append("Overall quality below acceptable standards")
        
        # Agent-specific recommendations
        for aid, scores in self.performance_metrics['agent_performance'].items():
            if agent_id and aid != agent_id:
                continue
                
            if scores:
                avg_agent_score = statistics.mean(scores)
                agent_recs = []
                
                if avg_agent_score < 3.0:
                    agent_recs.append("Focus on basic quality improvements")
                elif avg_agent_score < 4.0:
                    agent_recs.append("Work on consistency and polish")
                
                if len(scores) >= 5:
                    recent_trend = statistics.mean(scores[-3:]) - statistics.mean(scores[-5:-2])
                    if recent_trend < -0.2:
                        agent_recs.append("Quality declining - review recent changes")
                
                recommendations['agent_specific'][aid] = agent_recs
        
        # System-wide recommendations
        if self.performance_metrics['total_assessments'] > 50:
            if avg_score < 3.8:
                recommendations['system_wide'].append("Consider updating quality standards")
        
        return recommendations

