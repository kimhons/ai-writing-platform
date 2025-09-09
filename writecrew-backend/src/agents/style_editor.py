"""
Style Editor Agent - Writing Enhancement and Polish
Specialized CrewAI agent for improving writing style, tone, and readability
"""

import asyncio
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import structlog

from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from ..models.task import TaskRequest, TaskResponse
from ..services.ai_providers import AIProviderService
from ..utils.prompts import STYLE_EDITOR_PROMPTS
from .base_agent import BaseWritingAgent

logger = structlog.get_logger(__name__)


class StyleAnalysisTool(BaseTool):
    """Tool for analyzing writing style and identifying improvement areas"""
    
    name: str = "style_analyzer"
    description: str = "Analyze writing style, tone, readability, and identify areas for improvement"
    
    def _run(self, text: str, target_style: str = "professional", target_audience: str = "general") -> Dict[str, Any]:
        """Analyze text style and provide improvement recommendations"""
        try:
            # Analyze current style characteristics
            current_style = self._analyze_current_style(text)
            
            # Assess readability
            readability = self._assess_readability(text)
            
            # Analyze tone consistency
            tone_analysis = self._analyze_tone_consistency(text)
            
            # Identify style issues
            style_issues = self._identify_style_issues(text, target_style, target_audience)
            
            # Generate improvement recommendations
            recommendations = self._generate_style_recommendations(
                current_style, target_style, style_issues, readability
            )
            
            return {
                'current_style': current_style,
                'target_style': target_style,
                'target_audience': target_audience,
                'readability': readability,
                'tone_analysis': tone_analysis,
                'style_issues': style_issues,
                'recommendations': recommendations,
                'improvement_priority': self._prioritize_improvements(style_issues)
            }
            
        except Exception as e:
            logger.error("Style analysis failed", error=str(e))
            return {
                'error': str(e),
                'current_style': 'unknown',
                'recommendations': ['Manual style review recommended due to analysis error']
            }
    
    def _analyze_current_style(self, text: str) -> Dict[str, Any]:
        """Analyze current writing style characteristics"""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        words = text.split()
        
        # Sentence length analysis
        sentence_lengths = [len(s.split()) for s in sentences if s]
        avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0
        
        # Word complexity analysis
        complex_words = [w for w in words if len(w) > 6]
        complexity_ratio = len(complex_words) / len(words) if words else 0
        
        # Passive voice detection
        passive_indicators = ['was', 'were', 'been', 'being', 'is', 'are', 'am']
        passive_count = sum(1 for word in words if word.lower() in passive_indicators)
        passive_ratio = passive_count / len(sentences) if sentences else 0
        
        # Formality indicators
        formal_words = ['therefore', 'however', 'furthermore', 'consequently', 'nevertheless']
        informal_words = ['really', 'pretty', 'quite', 'sort of', 'kind of']
        
        formal_count = sum(1 for word in words if word.lower() in formal_words)
        informal_count = sum(1 for word in words if word.lower() in informal_words)
        
        # Determine style characteristics
        style_traits = []
        
        if avg_sentence_length > 20:
            style_traits.append('complex_sentences')
        elif avg_sentence_length < 10:
            style_traits.append('simple_sentences')
        
        if complexity_ratio > 0.3:
            style_traits.append('complex_vocabulary')
        elif complexity_ratio < 0.1:
            style_traits.append('simple_vocabulary')
        
        if passive_ratio > 0.3:
            style_traits.append('passive_heavy')
        elif passive_ratio < 0.1:
            style_traits.append('active_voice')
        
        if formal_count > informal_count:
            style_traits.append('formal_tone')
        elif informal_count > formal_count:
            style_traits.append('informal_tone')
        
        return {
            'avg_sentence_length': round(avg_sentence_length, 1),
            'complexity_ratio': round(complexity_ratio, 2),
            'passive_ratio': round(passive_ratio, 2),
            'formal_indicators': formal_count,
            'informal_indicators': informal_count,
            'style_traits': style_traits,
            'total_sentences': len(sentences),
            'total_words': len(words)
        }
    
    def _assess_readability(self, text: str) -> Dict[str, Any]:
        """Assess text readability using various metrics"""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        words = text.split()
        syllables = self._count_syllables(text)
        
        # Flesch Reading Ease (simplified)
        if len(sentences) > 0 and len(words) > 0:
            avg_sentence_length = len(words) / len(sentences)
            avg_syllables_per_word = syllables / len(words)
            
            flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
            flesch_score = max(0, min(100, flesch_score))  # Clamp between 0-100
        else:
            flesch_score = 50  # Default
        
        # Readability level
        if flesch_score >= 90:
            level = 'very_easy'
        elif flesch_score >= 80:
            level = 'easy'
        elif flesch_score >= 70:
            level = 'fairly_easy'
        elif flesch_score >= 60:
            level = 'standard'
        elif flesch_score >= 50:
            level = 'fairly_difficult'
        elif flesch_score >= 30:
            level = 'difficult'
        else:
            level = 'very_difficult'
        
        return {
            'flesch_score': round(flesch_score, 1),
            'readability_level': level,
            'avg_sentence_length': round(len(words) / len(sentences), 1) if sentences else 0,
            'avg_syllables_per_word': round(syllables / len(words), 1) if words else 0,
            'recommendations': self._get_readability_recommendations(level, flesch_score)
        }
    
    def _count_syllables(self, text: str) -> int:
        """Simple syllable counting (approximation)"""
        words = re.findall(r'\b\w+\b', text.lower())
        total_syllables = 0
        
        for word in words:
            # Simple vowel counting method
            vowels = 'aeiouy'
            syllable_count = 0
            prev_was_vowel = False
            
            for char in word:
                if char in vowels:
                    if not prev_was_vowel:
                        syllable_count += 1
                    prev_was_vowel = True
                else:
                    prev_was_vowel = False
            
            # Handle silent e
            if word.endswith('e') and syllable_count > 1:
                syllable_count -= 1
            
            # Minimum of 1 syllable per word
            syllable_count = max(1, syllable_count)
            total_syllables += syllable_count
        
        return total_syllables
    
    def _get_readability_recommendations(self, level: str, score: float) -> List[str]:
        """Get recommendations based on readability level"""
        recommendations = []
        
        if level in ['difficult', 'very_difficult']:
            recommendations.extend([
                'Shorten sentence length',
                'Use simpler vocabulary',
                'Break up complex ideas',
                'Add more paragraph breaks'
            ])
        elif level in ['very_easy', 'easy'] and score > 85:
            recommendations.extend([
                'Consider adding some variety in sentence length',
                'Include more sophisticated vocabulary where appropriate'
            ])
        
        return recommendations
    
    def _analyze_tone_consistency(self, text: str) -> Dict[str, Any]:
        """Analyze tone consistency throughout the text"""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        tone_indicators = {
            'formal': ['therefore', 'however', 'furthermore', 'consequently', 'moreover'],
            'informal': ['really', 'pretty', 'quite', 'sort of', 'kind of', 'gonna', 'wanna'],
            'academic': ['research', 'study', 'analysis', 'methodology', 'hypothesis'],
            'conversational': ['you', 'your', 'we', 'our', 'let\'s', 'here\'s'],
            'authoritative': ['must', 'should', 'will', 'shall', 'required', 'essential'],
            'friendly': ['please', 'thanks', 'great', 'wonderful', 'amazing']
        }
        
        paragraph_tones = []
        
        for paragraph in paragraphs:
            paragraph_lower = paragraph.lower()
            paragraph_tone = {}
            
            for tone, indicators in tone_indicators.items():
                count = sum(1 for indicator in indicators if indicator in paragraph_lower)
                if count > 0:
                    paragraph_tone[tone] = count
            
            # Determine dominant tone for paragraph
            if paragraph_tone:
                dominant_tone = max(paragraph_tone, key=paragraph_tone.get)
            else:
                dominant_tone = 'neutral'
            
            paragraph_tones.append(dominant_tone)
        
        # Analyze consistency
        unique_tones = set(paragraph_tones)
        consistency_score = 1.0 - (len(unique_tones) - 1) / max(1, len(paragraphs))
        
        return {
            'paragraph_tones': paragraph_tones,
            'unique_tones': list(unique_tones),
            'consistency_score': round(consistency_score, 2),
            'dominant_tone': max(set(paragraph_tones), key=paragraph_tones.count) if paragraph_tones else 'neutral',
            'tone_shifts': len(unique_tones) - 1 if unique_tones else 0
        }
    
    def _identify_style_issues(self, text: str, target_style: str, target_audience: str) -> List[Dict[str, Any]]:
        """Identify specific style issues in the text"""
        issues = []
        text_lower = text.lower()
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        # Check for repetitive sentence starters
        sentence_starters = [s.split()[:2] for s in sentences if s.split()]
        starter_counts = {}
        for starter in sentence_starters:
            starter_key = ' '.join(starter).lower()
            starter_counts[starter_key] = starter_counts.get(starter_key, 0) + 1
        
        repetitive_starters = [starter for starter, count in starter_counts.items() if count > 2]
        if repetitive_starters:
            issues.append({
                'type': 'repetitive_sentence_starters',
                'severity': 'medium',
                'description': f'Repetitive sentence starters: {", ".join(repetitive_starters)}',
                'suggestion': 'Vary sentence beginnings for better flow'
            })
        
        # Check for overuse of adverbs
        adverbs = re.findall(r'\b\w+ly\b', text_lower)
        adverb_ratio = len(adverbs) / len(text.split()) if text.split() else 0
        
        if adverb_ratio > 0.05:  # More than 5% adverbs
            issues.append({
                'type': 'excessive_adverbs',
                'severity': 'low',
                'description': f'High adverb usage: {len(adverbs)} adverbs ({adverb_ratio:.1%})',
                'suggestion': 'Consider replacing some adverbs with stronger verbs'
            })
        
        # Check for passive voice overuse
        passive_patterns = [
            r'\b(was|were|is|are|am|been|being)\s+\w+ed\b',
            r'\b(was|were|is|are|am|been|being)\s+\w+en\b'
        ]
        
        passive_count = 0
        for pattern in passive_patterns:
            passive_count += len(re.findall(pattern, text_lower))
        
        passive_ratio = passive_count / len(sentences) if sentences else 0
        
        if passive_ratio > 0.3:  # More than 30% passive
            issues.append({
                'type': 'excessive_passive_voice',
                'severity': 'medium',
                'description': f'High passive voice usage: {passive_ratio:.1%} of sentences',
                'suggestion': 'Convert some passive constructions to active voice'
            })
        
        # Check for weak words
        weak_words = ['very', 'really', 'quite', 'rather', 'somewhat', 'pretty', 'fairly']
        weak_word_count = sum(1 for word in text.split() if word.lower() in weak_words)
        
        if weak_word_count > len(text.split()) * 0.02:  # More than 2%
            issues.append({
                'type': 'weak_modifiers',
                'severity': 'low',
                'description': f'Overuse of weak modifiers: {weak_word_count} instances',
                'suggestion': 'Replace weak modifiers with more precise language'
            })
        
        # Check for clichés
        cliches = [
            'at the end of the day', 'think outside the box', 'low-hanging fruit',
            'move the needle', 'circle back', 'touch base', 'game changer'
        ]
        
        found_cliches = [cliche for cliche in cliches if cliche in text_lower]
        if found_cliches:
            issues.append({
                'type': 'cliches',
                'severity': 'medium',
                'description': f'Clichés found: {", ".join(found_cliches)}',
                'suggestion': 'Replace clichés with original expressions'
            })
        
        # Target style specific checks
        if target_style == 'academic' and target_audience == 'expert':
            # Check for informal language in academic context
            informal_words = ['really', 'pretty', 'quite', 'sort of', 'kind of']
            informal_count = sum(1 for word in text.split() if word.lower() in informal_words)
            
            if informal_count > 0:
                issues.append({
                    'type': 'informal_language_in_academic',
                    'severity': 'high',
                    'description': f'Informal language in academic context: {informal_count} instances',
                    'suggestion': 'Use more formal academic language'
                })
        
        elif target_style == 'conversational' and 'you' not in text_lower:
            issues.append({
                'type': 'missing_conversational_elements',
                'severity': 'medium',
                'description': 'Text lacks conversational engagement',
                'suggestion': 'Add direct address (you/your) and conversational elements'
            })
        
        return issues
    
    def _generate_style_recommendations(self, current_style: Dict[str, Any], 
                                      target_style: str, style_issues: List[Dict[str, Any]], 
                                      readability: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate comprehensive style improvement recommendations"""
        recommendations = []
        
        # Sentence length recommendations
        avg_length = current_style.get('avg_sentence_length', 15)
        if target_style == 'academic' and avg_length < 15:
            recommendations.append({
                'category': 'sentence_structure',
                'recommendation': 'Increase sentence complexity for academic style',
                'priority': 'medium'
            })
        elif target_style == 'conversational' and avg_length > 20:
            recommendations.append({
                'category': 'sentence_structure',
                'recommendation': 'Shorten sentences for conversational flow',
                'priority': 'high'
            })
        
        # Vocabulary recommendations
        complexity_ratio = current_style.get('complexity_ratio', 0.2)
        if target_style == 'professional' and complexity_ratio < 0.2:
            recommendations.append({
                'category': 'vocabulary',
                'recommendation': 'Use more sophisticated vocabulary',
                'priority': 'medium'
            })
        elif target_style == 'simple' and complexity_ratio > 0.3:
            recommendations.append({
                'category': 'vocabulary',
                'recommendation': 'Simplify vocabulary for broader accessibility',
                'priority': 'high'
            })
        
        # Voice recommendations
        passive_ratio = current_style.get('passive_ratio', 0.2)
        if passive_ratio > 0.3:
            recommendations.append({
                'category': 'voice',
                'recommendation': 'Reduce passive voice usage for more engaging writing',
                'priority': 'high'
            })
        
        # Readability recommendations
        readability_level = readability.get('readability_level', 'standard')
        if readability_level in ['difficult', 'very_difficult']:
            recommendations.append({
                'category': 'readability',
                'recommendation': 'Improve readability with shorter sentences and simpler words',
                'priority': 'high'
            })
        
        # Add issue-specific recommendations
        for issue in style_issues:
            recommendations.append({
                'category': issue['type'],
                'recommendation': issue['suggestion'],
                'priority': issue['severity']
            })
        
        return recommendations
    
    def _prioritize_improvements(self, style_issues: List[Dict[str, Any]]) -> List[str]:
        """Prioritize style improvements by severity"""
        high_priority = [issue['type'] for issue in style_issues if issue['severity'] == 'high']
        medium_priority = [issue['type'] for issue in style_issues if issue['severity'] == 'medium']
        low_priority = [issue['type'] for issue in style_issues if issue['severity'] == 'low']
        
        return high_priority + medium_priority + low_priority


class StyleEnhancementTool(BaseTool):
    """Tool for applying style enhancements to text"""
    
    name: str = "style_enhancer"
    description: str = "Apply specific style enhancements and improvements to text"
    
    def _run(self, text: str, enhancements: List[str], target_style: str = "professional") -> Dict[str, Any]:
        """Apply style enhancements to text"""
        try:
            enhanced_text = text
            applied_enhancements = []
            
            for enhancement in enhancements:
                if enhancement == 'improve_sentence_variety':
                    enhanced_text, applied = self._improve_sentence_variety(enhanced_text)
                elif enhancement == 'strengthen_vocabulary':
                    enhanced_text, applied = self._strengthen_vocabulary(enhanced_text)
                elif enhancement == 'reduce_passive_voice':
                    enhanced_text, applied = self._reduce_passive_voice(enhanced_text)
                elif enhancement == 'improve_transitions':
                    enhanced_text, applied = self._improve_transitions(enhanced_text)
                elif enhancement == 'enhance_clarity':
                    enhanced_text, applied = self._enhance_clarity(enhanced_text)
                elif enhancement == 'adjust_tone':
                    enhanced_text, applied = self._adjust_tone(enhanced_text, target_style)
                else:
                    applied = False
                
                if applied:
                    applied_enhancements.append(enhancement)
            
            return {
                'original_text': text,
                'enhanced_text': enhanced_text,
                'applied_enhancements': applied_enhancements,
                'improvement_summary': self._generate_improvement_summary(applied_enhancements)
            }
            
        except Exception as e:
            logger.error("Style enhancement failed", error=str(e))
            return {
                'original_text': text,
                'enhanced_text': text,
                'error': str(e),
                'applied_enhancements': []
            }
    
    def _improve_sentence_variety(self, text: str) -> Tuple[str, bool]:
        """Improve sentence variety and structure"""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        if len(sentences) < 3:
            return text, False
        
        # Simple sentence variety improvements
        enhanced_sentences = []
        
        for i, sentence in enumerate(sentences):
            words = sentence.split()
            if not words:
                continue
            
            # Add variety to sentence starters
            if i > 0 and words[0].lower() == sentences[i-1].split()[0].lower():
                # Try to vary the sentence starter
                if words[0].lower() == 'the':
                    enhanced_sentences.append(sentence)  # Keep as is for now
                elif words[0].lower() in ['this', 'that', 'these', 'those']:
                    enhanced_sentences.append(sentence)  # Keep as is for now
                else:
                    enhanced_sentences.append(sentence)
            else:
                enhanced_sentences.append(sentence)
        
        enhanced_text = '. '.join(enhanced_sentences) + '.'
        return enhanced_text, True
    
    def _strengthen_vocabulary(self, text: str) -> Tuple[str, bool]:
        """Strengthen vocabulary with more precise words"""
        # Simple vocabulary improvements
        vocabulary_improvements = {
            'very good': 'excellent',
            'very bad': 'terrible',
            'very big': 'enormous',
            'very small': 'tiny',
            'very important': 'crucial',
            'very easy': 'effortless',
            'very hard': 'challenging',
            'really good': 'outstanding',
            'pretty good': 'commendable',
            'quite nice': 'pleasant'
        }
        
        enhanced_text = text
        improvements_made = False
        
        for weak_phrase, strong_word in vocabulary_improvements.items():
            if weak_phrase in enhanced_text.lower():
                # Case-sensitive replacement
                enhanced_text = re.sub(
                    re.escape(weak_phrase), 
                    strong_word, 
                    enhanced_text, 
                    flags=re.IGNORECASE
                )
                improvements_made = True
        
        return enhanced_text, improvements_made
    
    def _reduce_passive_voice(self, text: str) -> Tuple[str, bool]:
        """Reduce passive voice constructions"""
        # Simple passive voice patterns and their active alternatives
        passive_patterns = [
            (r'\bwas (\w+)ed by (.+)', r'\2 \1ed'),
            (r'\bwere (\w+)ed by (.+)', r'\2 \1ed'),
            (r'\bis (\w+)ed by (.+)', r'\2 \1s'),
            (r'\bare (\w+)ed by (.+)', r'\2 \1')
        ]
        
        enhanced_text = text
        improvements_made = False
        
        for passive_pattern, active_replacement in passive_patterns:
            if re.search(passive_pattern, enhanced_text):
                enhanced_text = re.sub(passive_pattern, active_replacement, enhanced_text)
                improvements_made = True
        
        return enhanced_text, improvements_made
    
    def _improve_transitions(self, text: str) -> Tuple[str, bool]:
        """Improve transitions between sentences and paragraphs"""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        if len(sentences) < 3:
            return text, False
        
        # Add transition words where appropriate
        transition_words = [
            'Furthermore', 'Additionally', 'Moreover', 'However', 'Nevertheless',
            'Consequently', 'Therefore', 'In contrast', 'Similarly', 'Meanwhile'
        ]
        
        enhanced_sentences = [sentences[0]]  # Keep first sentence as is
        
        for i in range(1, len(sentences)):
            sentence = sentences[i]
            
            # Simple logic to add transitions (very basic)
            if i == len(sentences) - 1:  # Last sentence
                if not sentence.lower().startswith(('in conclusion', 'finally', 'ultimately')):
                    sentence = f"Finally, {sentence.lower()}"
            elif i == len(sentences) // 2:  # Middle sentence
                if not any(sentence.lower().startswith(tw.lower()) for tw in transition_words):
                    sentence = f"Furthermore, {sentence.lower()}"
            
            enhanced_sentences.append(sentence)
        
        enhanced_text = '. '.join(enhanced_sentences) + '.'
        return enhanced_text, True
    
    def _enhance_clarity(self, text: str) -> Tuple[str, bool]:
        """Enhance clarity by removing unnecessary words"""
        clarity_improvements = {
            'in order to': 'to',
            'due to the fact that': 'because',
            'at this point in time': 'now',
            'for the purpose of': 'to',
            'in the event that': 'if',
            'with regard to': 'regarding',
            'it is important to note that': '',
            'it should be noted that': ''
        }
        
        enhanced_text = text
        improvements_made = False
        
        for wordy_phrase, concise_replacement in clarity_improvements.items():
            if wordy_phrase in enhanced_text.lower():
                enhanced_text = re.sub(
                    re.escape(wordy_phrase), 
                    concise_replacement, 
                    enhanced_text, 
                    flags=re.IGNORECASE
                )
                improvements_made = True
        
        return enhanced_text, improvements_made
    
    def _adjust_tone(self, text: str, target_style: str) -> Tuple[str, bool]:
        """Adjust tone to match target style"""
        if target_style == 'formal':
            # Make more formal
            informal_to_formal = {
                "don't": "do not",
                "can't": "cannot",
                "won't": "will not",
                "isn't": "is not",
                "aren't": "are not",
                "doesn't": "does not"
            }
            
            enhanced_text = text
            for informal, formal in informal_to_formal.items():
                enhanced_text = enhanced_text.replace(informal, formal)
            
            return enhanced_text, True
        
        elif target_style == 'conversational':
            # Make more conversational
            if 'you' not in text.lower():
                # Add some direct address (very simple implementation)
                enhanced_text = text.replace('people', 'you')
                enhanced_text = enhanced_text.replace('individuals', 'you')
                return enhanced_text, True
        
        return text, False
    
    def _generate_improvement_summary(self, applied_enhancements: List[str]) -> str:
        """Generate summary of applied improvements"""
        if not applied_enhancements:
            return "No enhancements were applied."
        
        enhancement_descriptions = {
            'improve_sentence_variety': 'Improved sentence variety and structure',
            'strengthen_vocabulary': 'Strengthened vocabulary with more precise words',
            'reduce_passive_voice': 'Reduced passive voice constructions',
            'improve_transitions': 'Enhanced transitions between ideas',
            'enhance_clarity': 'Improved clarity by removing unnecessary words',
            'adjust_tone': 'Adjusted tone to match target style'
        }
        
        descriptions = [enhancement_descriptions.get(e, e) for e in applied_enhancements]
        
        if len(descriptions) == 1:
            return descriptions[0]
        elif len(descriptions) == 2:
            return f"{descriptions[0]} and {descriptions[1]}"
        else:
            return f"{', '.join(descriptions[:-1])}, and {descriptions[-1]}"


class StyleEditorAgent(BaseWritingAgent):
    """Style Editor Agent for writing enhancement and polish"""
    
    def __init__(self, ai_provider_service: AIProviderService):
        super().__init__(
            agent_id="style_editor",
            name="Style Editor",
            ai_provider_service=ai_provider_service
        )
        
        # Initialize CrewAI agent
        self.crew_agent = Agent(
            role="Expert Writing Style Editor and Enhancement Specialist",
            goal="Improve writing style, enhance readability, and polish content for maximum impact and clarity",
            backstory=STYLE_EDITOR_PROMPTS["backstory"],
            verbose=True,
            allow_delegation=False,
            tools=[StyleAnalysisTool(), StyleEnhancementTool()],
            llm=ai_provider_service.get_primary_llm(),
            max_iter=3,
            memory=True
        )
        
        # Specializations
        self.specializations = [
            "Writing style analysis",
            "Readability improvement",
            "Tone adjustment",
            "Sentence structure enhancement",
            "Vocabulary strengthening",
            "Flow and transitions",
            "Clarity optimization",
            "Voice consistency"
        ]
        
        # Style expertise levels
        self.style_expertise = {
            'readability_improvement': 0.95,
            'tone_adjustment': 0.92,
            'sentence_structure': 0.90,
            'vocabulary_enhancement': 0.88,
            'flow_improvement': 0.85,
            'clarity_optimization': 0.93,
            'style_consistency': 0.87,
            'voice_development': 0.82
        }
        
        # Supported styles
        self.supported_styles = [
            'professional', 'academic', 'conversational', 'formal', 'informal',
            'technical', 'creative', 'journalistic', 'business', 'casual'
        ]
        
        logger.info("Style Editor Agent initialized", specializations=len(self.specializations))
    
    async def execute_task(self, task_request: TaskRequest) -> TaskResponse:
        """Execute style editing task"""
        try:
            self._start_timing()
            logger.info("Executing style editing task", task_id=task_request.task_id)
            
            # Analyze style requirements
            style_analysis = await self._analyze_style_requirements(task_request)
            
            # Perform style analysis on current text
            current_style_analysis = await self._analyze_current_style(task_request, style_analysis)
            
            # Generate style improvements
            style_improvements = await self._generate_style_improvements(
                task_request, style_analysis, current_style_analysis
            )
            
            # Apply enhancements
            enhanced_content = await self._apply_style_enhancements(
                task_request.content, style_improvements, style_analysis
            )
            
            # Create response
            response = TaskResponse(
                task_id=task_request.task_id,
                agent_id=self.agent_id,
                status="completed",
                content=enhanced_content,
                metadata={
                    "target_style": style_analysis.get("target_style"),
                    "target_audience": style_analysis.get("target_audience"),
                    "improvements_applied": style_improvements.get("applied_enhancements", []),
                    "readability_score": current_style_analysis.get("readability", {}).get("flesch_score"),
                    "style_issues_found": len(current_style_analysis.get("style_issues", [])),
                    "enhancement_summary": style_improvements.get("improvement_summary", "")
                },
                confidence_score=self._calculate_style_confidence(style_analysis, style_improvements),
                processing_time=self._get_processing_time()
            )
            
            await self._update_performance_metrics(response)
            
            logger.info(
                "Style editing task completed",
                task_id=task_request.task_id,
                target_style=style_analysis.get("target_style"),
                improvements=len(style_improvements.get("applied_enhancements", [])),
                confidence=response.confidence_score
            )
            
            return response
            
        except Exception as e:
            logger.error("Style editing task failed", task_id=task_request.task_id, error=str(e))
            return self._create_error_response(task_request, str(e))
    
    async def _analyze_style_requirements(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Analyze style requirements from task request"""
        try:
            # Extract target style from content or context
            target_style = self._determine_target_style(task_request.content, task_request.context)
            
            # Determine target audience
            target_audience = self._determine_target_audience(task_request.context, task_request.user_preferences)
            
            # Identify specific style objectives
            objectives = self._identify_style_objectives(task_request.content, task_request.task_type)
            
            # Determine enhancement priorities
            priorities = self._determine_enhancement_priorities(task_request.content, target_style)
            
            return {
                "target_style": target_style,
                "target_audience": target_audience,
                "objectives": objectives,
                "priorities": priorities,
                "preserve_voice": self._should_preserve_voice(task_request.user_preferences),
                "enhancement_level": self._determine_enhancement_level(task_request.user_preferences)
            }
            
        except Exception as e:
            logger.error("Style requirements analysis failed", error=str(e))
            return {
                "target_style": "professional",
                "target_audience": "general",
                "objectives": ["improve_readability"],
                "priorities": ["clarity", "flow"]
            }
    
    def _determine_target_style(self, content: str, context: Optional[str]) -> str:
        """Determine target style from content and context"""
        combined_text = f"{content} {context or ''}".lower()
        
        # Style indicators
        style_keywords = {
            'academic': ['research', 'study', 'analysis', 'methodology', 'hypothesis', 'peer-reviewed'],
            'business': ['strategy', 'objectives', 'stakeholders', 'roi', 'metrics', 'corporate'],
            'technical': ['implementation', 'specifications', 'architecture', 'documentation', 'api'],
            'creative': ['story', 'narrative', 'character', 'imagery', 'metaphor', 'artistic'],
            'journalistic': ['news', 'report', 'investigation', 'sources', 'facts', 'breaking'],
            'conversational': ['you', 'your', 'we', 'our', 'let\'s', 'here\'s', 'friendly'],
            'formal': ['therefore', 'furthermore', 'consequently', 'moreover', 'nevertheless']
        }
        
        style_scores = {}
        for style, keywords in style_keywords.items():
            score = sum(1 for keyword in keywords if keyword in combined_text)
            if score > 0:
                style_scores[style] = score
        
        if style_scores:
            return max(style_scores, key=style_scores.get)
        
        return 'professional'  # Default style
    
    def _determine_target_audience(self, context: Optional[str], user_preferences: Optional[Dict[str, Any]]) -> str:
        """Determine target audience"""
        if user_preferences and 'audience' in user_preferences:
            return user_preferences['audience']
        
        if context:
            context_lower = context.lower()
            
            audience_indicators = {
                'expert': ['expert', 'professional', 'specialist', 'advanced', 'technical'],
                'academic': ['student', 'researcher', 'scholar', 'university', 'academic'],
                'business': ['executive', 'manager', 'stakeholder', 'corporate', 'business'],
                'general': ['public', 'general', 'everyone', 'broad', 'wide']
            }
            
            for audience, indicators in audience_indicators.items():
                if any(indicator in context_lower for indicator in indicators):
                    return audience
        
        return 'general'
    
    def _identify_style_objectives(self, content: str, task_type: str) -> List[str]:
        """Identify specific style objectives"""
        objectives = []
        content_lower = content.lower()
        
        # Task type based objectives
        if task_type in ['improve', 'enhance', 'polish']:
            objectives.extend(['improve_readability', 'enhance_clarity', 'strengthen_vocabulary'])
        elif task_type in ['rewrite', 'revise']:
            objectives.extend(['improve_flow', 'adjust_tone', 'enhance_structure'])
        
        # Content based objectives
        if any(word in content_lower for word in ['boring', 'dull', 'unengaging']):
            objectives.append('increase_engagement')
        
        if any(word in content_lower for word in ['confusing', 'unclear', 'complex']):
            objectives.append('enhance_clarity')
        
        if any(word in content_lower for word in ['repetitive', 'monotonous']):
            objectives.append('improve_variety')
        
        if any(word in content_lower for word in ['formal', 'professional']):
            objectives.append('adjust_tone')
        
        return objectives if objectives else ['improve_readability']
    
    def _determine_enhancement_priorities(self, content: str, target_style: str) -> List[str]:
        """Determine enhancement priorities"""
        priorities = ['clarity']  # Always prioritize clarity
        
        # Add priorities based on target style
        style_priorities = {
            'academic': ['precision', 'formality', 'structure'],
            'business': ['conciseness', 'professionalism', 'impact'],
            'creative': ['voice', 'imagery', 'flow'],
            'conversational': ['engagement', 'accessibility', 'warmth'],
            'technical': ['precision', 'clarity', 'structure']
        }
        
        priorities.extend(style_priorities.get(target_style, ['flow', 'readability']))
        
        return list(set(priorities))  # Remove duplicates
    
    def _should_preserve_voice(self, user_preferences: Optional[Dict[str, Any]]) -> bool:
        """Determine if original voice should be preserved"""
        if user_preferences and 'preserve_voice' in user_preferences:
            return user_preferences['preserve_voice']
        
        return True  # Default to preserving voice
    
    def _determine_enhancement_level(self, user_preferences: Optional[Dict[str, Any]]) -> str:
        """Determine level of enhancement to apply"""
        if user_preferences and 'enhancement_level' in user_preferences:
            return user_preferences['enhancement_level']
        
        return 'moderate'  # light, moderate, heavy
    
    async def _analyze_current_style(self, task_request: TaskRequest, style_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current style of the text"""
        try:
            analysis_task = Task(
                description=f"""
                Analyze the writing style of the following text:
                
                Text: {task_request.content}
                Target Style: {style_analysis['target_style']}
                Target Audience: {style_analysis['target_audience']}
                
                Provide detailed analysis including:
                1. Current style characteristics
                2. Readability assessment
                3. Tone consistency
                4. Specific style issues
                5. Improvement recommendations
                
                Focus on identifying areas that need enhancement to match the target style and audience.
                """,
                agent=self.crew_agent,
                expected_output="Comprehensive style analysis with specific improvement recommendations"
            )
            
            crew = Crew(
                agents=[self.crew_agent],
                tasks=[analysis_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Also use tools for detailed analysis
            style_tool = StyleAnalysisTool()
            tool_analysis = style_tool._run(
                task_request.content,
                style_analysis['target_style'],
                style_analysis['target_audience']
            )
            
            return {
                'ai_analysis': str(result),
                'tool_analysis': tool_analysis,
                'current_style': tool_analysis.get('current_style', {}),
                'readability': tool_analysis.get('readability', {}),
                'tone_analysis': tool_analysis.get('tone_analysis', {}),
                'style_issues': tool_analysis.get('style_issues', []),
                'recommendations': tool_analysis.get('recommendations', [])
            }
            
        except Exception as e:
            logger.error("Current style analysis failed", error=str(e))
            return {
                'error': str(e),
                'current_style': {},
                'style_issues': [],
                'recommendations': []
            }
    
    async def _generate_style_improvements(self, task_request: TaskRequest, 
                                         style_analysis: Dict[str, Any], 
                                         current_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate specific style improvements"""
        try:
            improvement_task = Task(
                description=f"""
                Generate specific style improvements for the following text:
                
                Original Text: {task_request.content}
                Target Style: {style_analysis['target_style']}
                Target Audience: {style_analysis['target_audience']}
                Enhancement Level: {style_analysis['enhancement_level']}
                
                Current Analysis: {current_analysis.get('ai_analysis', 'No analysis available')}
                
                Style Issues Found: {current_analysis.get('style_issues', [])}
                
                Generate improvements that:
                1. Address identified style issues
                2. Match the target style and audience
                3. Preserve the original voice and meaning
                4. Enhance readability and engagement
                5. Apply appropriate enhancement level
                
                Provide specific, actionable improvements with explanations.
                """,
                agent=self.crew_agent,
                expected_output="Specific style improvements with detailed explanations"
            )
            
            crew = Crew(
                agents=[self.crew_agent],
                tasks=[improvement_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Determine which enhancements to apply
            enhancements_to_apply = self._select_enhancements(
                current_analysis.get('style_issues', []),
                style_analysis['objectives'],
                style_analysis['enhancement_level']
            )
            
            return {
                'ai_improvements': str(result),
                'selected_enhancements': enhancements_to_apply,
                'enhancement_rationale': self._explain_enhancement_selection(enhancements_to_apply)
            }
            
        except Exception as e:
            logger.error("Style improvement generation failed", error=str(e))
            return {
                'error': str(e),
                'selected_enhancements': ['enhance_clarity'],
                'ai_improvements': 'Error generating improvements'
            }
    
    def _select_enhancements(self, style_issues: List[Dict[str, Any]], 
                           objectives: List[str], enhancement_level: str) -> List[str]:
        """Select which enhancements to apply"""
        enhancements = []
        
        # Add enhancements based on style issues
        issue_types = [issue['type'] for issue in style_issues]
        
        if 'repetitive_sentence_starters' in issue_types:
            enhancements.append('improve_sentence_variety')
        
        if 'excessive_adverbs' in issue_types or 'weak_modifiers' in issue_types:
            enhancements.append('strengthen_vocabulary')
        
        if 'excessive_passive_voice' in issue_types:
            enhancements.append('reduce_passive_voice')
        
        # Add enhancements based on objectives
        objective_enhancements = {
            'improve_readability': ['enhance_clarity', 'improve_sentence_variety'],
            'enhance_clarity': ['enhance_clarity'],
            'strengthen_vocabulary': ['strengthen_vocabulary'],
            'improve_flow': ['improve_transitions'],
            'adjust_tone': ['adjust_tone'],
            'increase_engagement': ['improve_sentence_variety', 'strengthen_vocabulary']
        }
        
        for objective in objectives:
            enhancements.extend(objective_enhancements.get(objective, []))
        
        # Adjust based on enhancement level
        if enhancement_level == 'light':
            enhancements = enhancements[:2]  # Limit to 2 enhancements
        elif enhancement_level == 'heavy':
            enhancements.extend(['improve_transitions', 'adjust_tone'])
        
        return list(set(enhancements))  # Remove duplicates
    
    def _explain_enhancement_selection(self, enhancements: List[str]) -> str:
        """Explain why specific enhancements were selected"""
        explanations = {
            'improve_sentence_variety': 'to create more engaging and varied sentence structures',
            'strengthen_vocabulary': 'to use more precise and impactful language',
            'reduce_passive_voice': 'to create more direct and engaging writing',
            'improve_transitions': 'to enhance flow and logical connections',
            'enhance_clarity': 'to improve readability and understanding',
            'adjust_tone': 'to better match the target style and audience'
        }
        
        if not enhancements:
            return "No specific enhancements selected."
        
        reasons = [explanations.get(e, e) for e in enhancements]
        
        if len(reasons) == 1:
            return f"Selected {reasons[0]}."
        elif len(reasons) == 2:
            return f"Selected {reasons[0]} and {reasons[1]}."
        else:
            return f"Selected {', '.join(reasons[:-1])}, and {reasons[-1]}."
    
    async def _apply_style_enhancements(self, content: str, improvements: Dict[str, Any], 
                                      style_analysis: Dict[str, Any]) -> str:
        """Apply style enhancements to the content"""
        try:
            enhancement_task = Task(
                description=f"""
                Apply the following style enhancements to improve the text:
                
                Original Text: {content}
                Target Style: {style_analysis['target_style']}
                Target Audience: {style_analysis['target_audience']}
                
                Enhancements to Apply: {improvements.get('selected_enhancements', [])}
                Enhancement Rationale: {improvements.get('enhancement_rationale', '')}
                
                AI Improvement Suggestions: {improvements.get('ai_improvements', '')}
                
                Apply the enhancements while:
                1. Preserving the original meaning and voice
                2. Maintaining factual accuracy
                3. Ensuring natural flow and readability
                4. Matching the target style and audience
                5. Creating engaging and polished content
                
                Return the enhanced text with improvements applied.
                """,
                agent=self.crew_agent,
                expected_output="Enhanced text with style improvements applied"
            )
            
            crew = Crew(
                agents=[self.crew_agent],
                tasks=[enhancement_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Also apply tool-based enhancements
            enhancement_tool = StyleEnhancementTool()
            tool_result = enhancement_tool._run(
                content,
                improvements.get('selected_enhancements', []),
                style_analysis['target_style']
            )
            
            # Combine AI and tool enhancements (prefer AI result)
            final_content = str(result) if str(result).strip() else tool_result.get('enhanced_text', content)
            
            return final_content
            
        except Exception as e:
            logger.error("Style enhancement application failed", error=str(e))
            return content  # Return original if enhancement fails
    
    def _calculate_style_confidence(self, style_analysis: Dict[str, Any], 
                                  improvements: Dict[str, Any]) -> float:
        """Calculate confidence score for style editing"""
        try:
            base_confidence = 0.8
            
            # Adjust based on target style expertise
            target_style = style_analysis.get('target_style', 'professional')
            style_confidence = 0.85  # Default for supported styles
            
            if target_style in self.supported_styles:
                style_confidence = 0.9
            
            # Adjust based on enhancement success
            selected_enhancements = improvements.get('selected_enhancements', [])
            if selected_enhancements:
                enhancement_confidence = 0.85
            else:
                enhancement_confidence = 0.7  # Lower if no enhancements applied
            
            # Adjust based on enhancement level
            enhancement_level = style_analysis.get('enhancement_level', 'moderate')
            level_adjustments = {'light': 0.1, 'moderate': 0.0, 'heavy': -0.05}
            level_adjustment = level_adjustments.get(enhancement_level, 0.0)
            
            final_confidence = (base_confidence + style_confidence + enhancement_confidence) / 3 + level_adjustment
            return round(min(max(final_confidence, 0.1), 1.0), 2)
            
        except Exception:
            return 0.8
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get style editor capabilities"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "specializations": self.specializations,
            "style_types": self.supported_styles,
            "expertise_levels": self.style_expertise,
            "supported_tasks": ["improve", "enhance", "polish", "rewrite", "revise", "edit"],
            "enhancement_types": [
                "improve_sentence_variety", "strengthen_vocabulary", "reduce_passive_voice",
                "improve_transitions", "enhance_clarity", "adjust_tone"
            ],
            "readability_analysis": True,
            "tone_adjustment": True,
            "voice_preservation": True,
            "enhancement_levels": ["light", "moderate", "heavy"],
            "languages": ["English"],
            "collaboration_ready": True,
            "max_text_length": 10000  # words
        }

