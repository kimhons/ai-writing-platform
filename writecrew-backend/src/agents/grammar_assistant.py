"""
Grammar Assistant Agent - Language Correctness and Clarity
Specialized CrewAI agent for grammar checking, language correction, and clarity enhancement
"""

import asyncio
import re
import string
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import structlog

from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from ..models.task import TaskRequest, TaskResponse
from ..services.ai_providers import AIProviderService
from ..utils.prompts import GRAMMAR_ASSISTANT_PROMPTS
from .base_agent import BaseWritingAgent

logger = structlog.get_logger(__name__)


class GrammarCheckTool(BaseTool):
    """Tool for comprehensive grammar and language checking"""
    
    name: str = "grammar_checker"
    description: str = "Check grammar, punctuation, spelling, and language usage"
    
    def _run(self, text: str, check_level: str = "comprehensive") -> Dict[str, Any]:
        """Perform comprehensive grammar and language checking"""
        try:
            # Perform different types of checks
            spelling_errors = self._check_spelling(text)
            grammar_errors = self._check_grammar(text)
            punctuation_errors = self._check_punctuation(text)
            syntax_errors = self._check_syntax(text)
            word_usage_errors = self._check_word_usage(text)
            
            # Categorize errors by severity
            errors_by_severity = self._categorize_errors_by_severity([
                *spelling_errors, *grammar_errors, *punctuation_errors, 
                *syntax_errors, *word_usage_errors
            ])
            
            # Generate correction suggestions
            corrections = self._generate_corrections(text, errors_by_severity)
            
            # Calculate overall language quality score
            quality_score = self._calculate_language_quality(text, errors_by_severity)
            
            return {
                'text': text,
                'check_level': check_level,
                'spelling_errors': spelling_errors,
                'grammar_errors': grammar_errors,
                'punctuation_errors': punctuation_errors,
                'syntax_errors': syntax_errors,
                'word_usage_errors': word_usage_errors,
                'errors_by_severity': errors_by_severity,
                'corrections': corrections,
                'quality_score': quality_score,
                'total_errors': len(spelling_errors) + len(grammar_errors) + len(punctuation_errors) + len(syntax_errors) + len(word_usage_errors),
                'error_density': self._calculate_error_density(text, errors_by_severity)
            }
            
        except Exception as e:
            logger.error("Grammar checking failed", error=str(e))
            return {
                'text': text,
                'error': str(e),
                'total_errors': 0,
                'quality_score': 0.5,
                'corrections': []
            }
    
    def _check_spelling(self, text: str) -> List[Dict[str, Any]]:
        """Check for spelling errors (simplified implementation)"""
        errors = []
        
        # Common misspellings (in production, would use a proper spell checker)
        common_misspellings = {
            'recieve': 'receive',
            'seperate': 'separate',
            'definately': 'definitely',
            'occured': 'occurred',
            'begining': 'beginning',
            'existance': 'existence',
            'neccessary': 'necessary',
            'accomodate': 'accommodate',
            'embarass': 'embarrass',
            'maintainance': 'maintenance',
            'independant': 'independent',
            'priviledge': 'privilege',
            'recomend': 'recommend',
            'tommorrow': 'tomorrow',
            'alot': 'a lot',
            'thier': 'their',
            'wierd': 'weird',
            'freind': 'friend',
            'beleive': 'believe',
            'acheive': 'achieve'
        }
        
        words = re.findall(r'\b\w+\b', text.lower())
        word_positions = {}
        
        # Find positions of words in original text
        for match in re.finditer(r'\b\w+\b', text):
            word = match.group().lower()
            if word not in word_positions:
                word_positions[word] = []
            word_positions[word].append((match.start(), match.end()))
        
        for misspelled, correct in common_misspellings.items():
            if misspelled in words:
                positions = word_positions.get(misspelled, [])
                for start, end in positions:
                    errors.append({
                        'type': 'spelling',
                        'error': misspelled,
                        'correction': correct,
                        'position': (start, end),
                        'context': text[max(0, start-20):end+20],
                        'severity': 'high',
                        'description': f'Misspelled word: "{misspelled}" should be "{correct}"'
                    })
        
        return errors
    
    def _check_grammar(self, text: str) -> List[Dict[str, Any]]:
        """Check for grammar errors"""
        errors = []
        
        # Subject-verb agreement (simplified)
        # Pattern: singular subject + plural verb or vice versa
        sv_patterns = [
            (r'\b(he|she|it)\s+(are|were)\b', 'Subject-verb disagreement: singular subject with plural verb'),
            (r'\b(they|we)\s+(is|was)\b', 'Subject-verb disagreement: plural subject with singular verb'),
            (r'\b(I)\s+(is|are)\b', 'Incorrect verb form with "I"'),
            (r'\b(you)\s+(is)\b', 'Incorrect verb form with "you"')
        ]
        
        for pattern, description in sv_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                errors.append({
                    'type': 'grammar',
                    'error': match.group(),
                    'position': (match.start(), match.end()),
                    'context': text[max(0, match.start()-20):match.end()+20],
                    'severity': 'high',
                    'description': description,
                    'suggestion': self._suggest_sv_correction(match.group())
                })
        
        # Incorrect verb forms
        verb_errors = [
            (r'\bhave\s+went\b', 'have gone', 'Incorrect past participle'),
            (r'\bhave\s+came\b', 'have come', 'Incorrect past participle'),
            (r'\bhave\s+ran\b', 'have run', 'Incorrect past participle'),
            (r'\bhave\s+began\b', 'have begun', 'Incorrect past participle'),
            (r'\bcould\s+of\b', 'could have', 'Incorrect auxiliary verb'),
            (r'\bwould\s+of\b', 'would have', 'Incorrect auxiliary verb'),
            (r'\bshould\s+of\b', 'should have', 'Incorrect auxiliary verb')
        ]
        
        for pattern, correction, description in verb_errors:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                errors.append({
                    'type': 'grammar',
                    'error': match.group(),
                    'correction': correction,
                    'position': (match.start(), match.end()),
                    'context': text[max(0, match.start()-20):match.end()+20],
                    'severity': 'high',
                    'description': description
                })
        
        # Double negatives
        double_negative_pattern = r'\b(don\'t|doesn\'t|didn\'t|won\'t|wouldn\'t|can\'t|couldn\'t)\s+\w*\s+(no|nothing|nobody|nowhere|never|none)\b'
        for match in re.finditer(double_negative_pattern, text, re.IGNORECASE):
            errors.append({
                'type': 'grammar',
                'error': match.group(),
                'position': (match.start(), match.end()),
                'context': text[max(0, match.start()-20):match.end()+20],
                'severity': 'medium',
                'description': 'Double negative construction',
                'suggestion': 'Consider using a single negative for clarity'
            })
        
        return errors
    
    def _suggest_sv_correction(self, error_text: str) -> str:
        """Suggest correction for subject-verb agreement errors"""
        error_lower = error_text.lower()
        
        corrections = {
            'he are': 'he is',
            'she are': 'she is',
            'it are': 'it is',
            'he were': 'he was',
            'she were': 'she was',
            'it were': 'it was',
            'they is': 'they are',
            'they was': 'they were',
            'we is': 'we are',
            'we was': 'we were',
            'i is': 'I am',
            'i are': 'I am',
            'you is': 'you are'
        }
        
        return corrections.get(error_lower, error_text)
    
    def _check_punctuation(self, text: str) -> List[Dict[str, Any]]:
        """Check for punctuation errors"""
        errors = []
        
        # Missing spaces after punctuation
        space_patterns = [
            (r'[.!?][A-Z]', 'Missing space after sentence-ending punctuation'),
            (r',[A-Za-z]', 'Missing space after comma'),
            (r';[A-Za-z]', 'Missing space after semicolon'),
            (r':[A-Za-z]', 'Missing space after colon')
        ]
        
        for pattern, description in space_patterns:
            for match in re.finditer(pattern, text):
                errors.append({
                    'type': 'punctuation',
                    'error': match.group(),
                    'position': (match.start(), match.end()),
                    'context': text[max(0, match.start()-10):match.end()+10],
                    'severity': 'medium',
                    'description': description,
                    'correction': match.group()[0] + ' ' + match.group()[1:]
                })
        
        # Multiple punctuation marks
        multiple_punct_pattern = r'[.!?]{2,}|[,;:]{2,}'
        for match in re.finditer(multiple_punct_pattern, text):
            errors.append({
                'type': 'punctuation',
                'error': match.group(),
                'position': (match.start(), match.end()),
                'context': text[max(0, match.start()-10):match.end()+10],
                'severity': 'low',
                'description': 'Multiple consecutive punctuation marks',
                'correction': match.group()[0]  # Keep only the first punctuation mark
            })
        
        # Incorrect apostrophe usage
        apostrophe_patterns = [
            (r'\bits\'\b', 'its', 'Incorrect apostrophe in possessive "its"'),
            (r'\byour\'s\b', 'yours', 'Incorrect apostrophe in possessive "yours"'),
            (r'\bher\'s\b', 'hers', 'Incorrect apostrophe in possessive "hers"'),
            (r'\btheir\'s\b', 'theirs', 'Incorrect apostrophe in possessive "theirs"')
        ]
        
        for pattern, correction, description in apostrophe_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                errors.append({
                    'type': 'punctuation',
                    'error': match.group(),
                    'correction': correction,
                    'position': (match.start(), match.end()),
                    'context': text[max(0, match.start()-10):match.end()+10],
                    'severity': 'high',
                    'description': description
                })
        
        return errors
    
    def _check_syntax(self, text: str) -> List[Dict[str, Any]]:
        """Check for syntax errors"""
        errors = []
        
        # Sentence fragments (very basic detection)
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        
        for i, sentence in enumerate(sentences):
            words = sentence.split()
            if len(words) < 3:  # Very short sentences might be fragments
                # Check if it has a verb (simplified)
                has_verb = any(word.lower() in ['is', 'are', 'was', 'were', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'can', 'could', 'should', 'may', 'might'] for word in words)
                
                if not has_verb and len(words) > 1:
                    # Find position in original text
                    sentence_start = text.find(sentence)
                    if sentence_start != -1:
                        errors.append({
                            'type': 'syntax',
                            'error': sentence,
                            'position': (sentence_start, sentence_start + len(sentence)),
                            'context': sentence,
                            'severity': 'medium',
                            'description': 'Possible sentence fragment - missing verb',
                            'suggestion': 'Consider adding a verb or combining with adjacent sentence'
                        })
        
        # Run-on sentences (very basic detection)
        for sentence in sentences:
            if len(sentence.split()) > 40:  # Very long sentences
                sentence_start = text.find(sentence)
                if sentence_start != -1:
                    errors.append({
                        'type': 'syntax',
                        'error': sentence[:100] + '...' if len(sentence) > 100 else sentence,
                        'position': (sentence_start, sentence_start + len(sentence)),
                        'context': sentence[:100] + '...' if len(sentence) > 100 else sentence,
                        'severity': 'low',
                        'description': 'Possible run-on sentence - consider breaking into shorter sentences',
                        'suggestion': 'Break into multiple sentences for better readability'
                    })
        
        return errors
    
    def _check_word_usage(self, text: str) -> List[Dict[str, Any]]:
        """Check for incorrect word usage"""
        errors = []
        
        # Common word confusion
        word_confusions = [
            (r'\bthere\s+(is|are)\s+\d+', 'their', 'Possible confusion: "there" vs "their"'),
            (r'\byour\s+(going|coming|doing)', 'you\'re', 'Possible confusion: "your" vs "you\'re"'),
            (r'\bits\s+(a|an|the)', 'it\'s', 'Possible confusion: "its" vs "it\'s"'),
            (r'\bthen\s+(I|you|he|she|we|they)', 'than', 'Possible confusion: "then" vs "than"'),
            (r'\baffect\s+(on|upon)', 'effect', 'Possible confusion: "affect" vs "effect"'),
            (r'\baccept\s+(for|that)', 'except', 'Possible confusion: "accept" vs "except"')
        ]
        
        for pattern, suggestion, description in word_confusions:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                errors.append({
                    'type': 'word_usage',
                    'error': match.group(),
                    'suggestion': suggestion,
                    'position': (match.start(), match.end()),
                    'context': text[max(0, match.start()-20):match.end()+20],
                    'severity': 'medium',
                    'description': description
                })
        
        # Redundant phrases
        redundant_phrases = [
            (r'\bfree\s+gift\b', 'gift', 'Redundant: gifts are inherently free'),
            (r'\bunexpected\s+surprise\b', 'surprise', 'Redundant: surprises are inherently unexpected'),
            (r'\badvance\s+planning\b', 'planning', 'Redundant: planning is inherently done in advance'),
            (r'\bfuture\s+plans\b', 'plans', 'Redundant: plans are inherently for the future'),
            (r'\bpersonal\s+opinion\b', 'opinion', 'Redundant: opinions are inherently personal'),
            (r'\bexact\s+same\b', 'same', 'Redundant: "same" implies exactness')
        ]
        
        for pattern, correction, description in redundant_phrases:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                errors.append({
                    'type': 'word_usage',
                    'error': match.group(),
                    'correction': correction,
                    'position': (match.start(), match.end()),
                    'context': text[max(0, match.start()-10):match.end()+10],
                    'severity': 'low',
                    'description': description
                })
        
        return errors
    
    def _categorize_errors_by_severity(self, all_errors: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize errors by severity level"""
        categorized = {
            'high': [],
            'medium': [],
            'low': []
        }
        
        for error in all_errors:
            severity = error.get('severity', 'medium')
            categorized[severity].append(error)
        
        return categorized
    
    def _generate_corrections(self, text: str, errors_by_severity: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Generate correction suggestions"""
        corrections = []
        
        # Process errors by severity (high priority first)
        for severity in ['high', 'medium', 'low']:
            for error in errors_by_severity[severity]:
                correction = {
                    'error': error,
                    'original_text': error.get('error', ''),
                    'suggested_correction': error.get('correction', error.get('suggestion', '')),
                    'explanation': error.get('description', ''),
                    'confidence': self._calculate_correction_confidence(error),
                    'priority': severity
                }
                corrections.append(correction)
        
        return corrections
    
    def _calculate_correction_confidence(self, error: Dict[str, Any]) -> float:
        """Calculate confidence level for a correction"""
        error_type = error.get('type', '')
        severity = error.get('severity', 'medium')
        
        # Base confidence by error type
        type_confidence = {
            'spelling': 0.95,
            'punctuation': 0.90,
            'grammar': 0.85,
            'syntax': 0.70,
            'word_usage': 0.75
        }
        
        base_confidence = type_confidence.get(error_type, 0.8)
        
        # Adjust by severity
        severity_adjustments = {
            'high': 0.05,
            'medium': 0.0,
            'low': -0.05
        }
        
        adjustment = severity_adjustments.get(severity, 0.0)
        
        return min(1.0, max(0.1, base_confidence + adjustment))
    
    def _calculate_language_quality(self, text: str, errors_by_severity: Dict[str, List[Dict[str, Any]]]) -> float:
        """Calculate overall language quality score"""
        if not text.strip():
            return 0.0
        
        word_count = len(text.split())
        total_errors = sum(len(errors) for errors in errors_by_severity.values())
        
        if total_errors == 0:
            return 1.0
        
        # Weight errors by severity
        weighted_errors = (
            len(errors_by_severity['high']) * 3 +
            len(errors_by_severity['medium']) * 2 +
            len(errors_by_severity['low']) * 1
        )
        
        # Calculate error rate per 100 words
        error_rate = (weighted_errors / word_count) * 100 if word_count > 0 else weighted_errors
        
        # Convert to quality score (0-1)
        quality_score = max(0.0, 1.0 - (error_rate / 20))  # Assuming 20 weighted errors per 100 words = 0 quality
        
        return round(quality_score, 2)
    
    def _calculate_error_density(self, text: str, errors_by_severity: Dict[str, List[Dict[str, Any]]]) -> float:
        """Calculate error density (errors per 100 words)"""
        word_count = len(text.split())
        total_errors = sum(len(errors) for errors in errors_by_severity.values())
        
        if word_count == 0:
            return 0.0
        
        return round((total_errors / word_count) * 100, 2)


class LanguageClarityTool(BaseTool):
    """Tool for improving language clarity and readability"""
    
    name: str = "clarity_enhancer"
    description: str = "Improve language clarity, readability, and communication effectiveness"
    
    def _run(self, text: str, target_audience: str = "general") -> Dict[str, Any]:
        """Analyze and improve language clarity"""
        try:
            # Analyze current clarity issues
            clarity_issues = self._identify_clarity_issues(text)
            
            # Assess readability
            readability_analysis = self._analyze_readability(text)
            
            # Identify complex language
            complexity_analysis = self._analyze_language_complexity(text)
            
            # Generate clarity improvements
            clarity_suggestions = self._generate_clarity_suggestions(
                text, clarity_issues, readability_analysis, target_audience
            )
            
            return {
                'text': text,
                'target_audience': target_audience,
                'clarity_issues': clarity_issues,
                'readability_analysis': readability_analysis,
                'complexity_analysis': complexity_analysis,
                'clarity_suggestions': clarity_suggestions,
                'clarity_score': self._calculate_clarity_score(clarity_issues, readability_analysis),
                'improvement_priority': self._prioritize_clarity_improvements(clarity_issues)
            }
            
        except Exception as e:
            logger.error("Clarity analysis failed", error=str(e))
            return {
                'text': text,
                'error': str(e),
                'clarity_score': 0.5,
                'clarity_suggestions': []
            }
    
    def _identify_clarity_issues(self, text: str) -> List[Dict[str, Any]]:
        """Identify issues that affect clarity"""
        issues = []
        
        # Ambiguous pronouns
        pronoun_pattern = r'\b(it|this|that|they|them)\b'
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        
        for sentence in sentences:
            pronouns = re.findall(pronoun_pattern, sentence, re.IGNORECASE)
            if len(pronouns) > 2:  # Multiple pronouns might cause confusion
                sentence_start = text.find(sentence)
                if sentence_start != -1:
                    issues.append({
                        'type': 'ambiguous_pronouns',
                        'text': sentence,
                        'position': (sentence_start, sentence_start + len(sentence)),
                        'severity': 'medium',
                        'description': 'Multiple pronouns may cause confusion',
                        'suggestion': 'Consider replacing some pronouns with specific nouns'
                    })
        
        # Vague words
        vague_words = ['thing', 'stuff', 'something', 'someone', 'somewhere', 'somehow', 'various', 'several', 'many', 'some']
        for word in vague_words:
            pattern = r'\b' + re.escape(word) + r'\b'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                issues.append({
                    'type': 'vague_language',
                    'text': match.group(),
                    'position': (match.start(), match.end()),
                    'severity': 'low',
                    'description': f'Vague word: "{word}"',
                    'suggestion': 'Use more specific language'
                })
        
        # Nominalizations (turning verbs into nouns)
        nominalizations = [
            'implementation', 'utilization', 'optimization', 'maximization',
            'minimization', 'facilitation', 'demonstration', 'consideration'
        ]
        
        for nom in nominalizations:
            pattern = r'\b' + re.escape(nom) + r'\b'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                issues.append({
                    'type': 'nominalization',
                    'text': match.group(),
                    'position': (match.start(), match.end()),
                    'severity': 'low',
                    'description': f'Nominalization: "{nom}"',
                    'suggestion': f'Consider using the verb form instead'
                })
        
        # Wordy phrases
        wordy_phrases = {
            'in order to': 'to',
            'due to the fact that': 'because',
            'at this point in time': 'now',
            'for the purpose of': 'to',
            'in the event that': 'if',
            'with regard to': 'regarding',
            'in spite of the fact that': 'although',
            'by means of': 'by',
            'in the process of': 'while',
            'make use of': 'use'
        }
        
        for wordy, concise in wordy_phrases.items():
            pattern = r'\b' + re.escape(wordy) + r'\b'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                issues.append({
                    'type': 'wordy_phrase',
                    'text': match.group(),
                    'correction': concise,
                    'position': (match.start(), match.end()),
                    'severity': 'medium',
                    'description': f'Wordy phrase: "{wordy}"',
                    'suggestion': f'Replace with "{concise}"'
                })
        
        return issues
    
    def _analyze_readability(self, text: str) -> Dict[str, Any]:
        """Analyze text readability"""
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        words = text.split()
        
        if not sentences or not words:
            return {'avg_sentence_length': 0, 'readability_level': 'unknown'}
        
        # Average sentence length
        avg_sentence_length = len(words) / len(sentences)
        
        # Complex words (more than 2 syllables, simplified)
        complex_words = [w for w in words if len(w) > 6]
        complex_word_ratio = len(complex_words) / len(words) if words else 0
        
        # Readability assessment
        if avg_sentence_length > 25 or complex_word_ratio > 0.3:
            readability_level = 'difficult'
        elif avg_sentence_length > 20 or complex_word_ratio > 0.2:
            readability_level = 'moderate'
        else:
            readability_level = 'easy'
        
        return {
            'avg_sentence_length': round(avg_sentence_length, 1),
            'complex_word_ratio': round(complex_word_ratio, 2),
            'readability_level': readability_level,
            'total_sentences': len(sentences),
            'total_words': len(words)
        }
    
    def _analyze_language_complexity(self, text: str) -> Dict[str, Any]:
        """Analyze language complexity"""
        words = text.split()
        
        # Technical jargon detection (simplified)
        technical_indicators = [
            'implementation', 'infrastructure', 'methodology', 'optimization',
            'synchronization', 'configuration', 'authentication', 'authorization'
        ]
        
        jargon_count = sum(1 for word in words if word.lower() in technical_indicators)
        jargon_ratio = jargon_count / len(words) if words else 0
        
        # Formal language indicators
        formal_indicators = [
            'therefore', 'furthermore', 'consequently', 'nevertheless',
            'moreover', 'however', 'accordingly', 'subsequently'
        ]
        
        formal_count = sum(1 for word in words if word.lower() in formal_indicators)
        formal_ratio = formal_count / len(words) if words else 0
        
        return {
            'jargon_ratio': round(jargon_ratio, 3),
            'formal_ratio': round(formal_ratio, 3),
            'avg_word_length': round(sum(len(word) for word in words) / len(words), 1) if words else 0,
            'complexity_level': self._determine_complexity_level(jargon_ratio, formal_ratio)
        }
    
    def _determine_complexity_level(self, jargon_ratio: float, formal_ratio: float) -> str:
        """Determine overall complexity level"""
        if jargon_ratio > 0.05 or formal_ratio > 0.03:
            return 'high'
        elif jargon_ratio > 0.02 or formal_ratio > 0.01:
            return 'medium'
        else:
            return 'low'
    
    def _generate_clarity_suggestions(self, text: str, clarity_issues: List[Dict[str, Any]], 
                                    readability_analysis: Dict[str, Any], target_audience: str) -> List[Dict[str, str]]:
        """Generate suggestions for improving clarity"""
        suggestions = []
        
        # Suggestions based on clarity issues
        issue_types = [issue['type'] for issue in clarity_issues]
        
        if 'ambiguous_pronouns' in issue_types:
            suggestions.append({
                'category': 'pronoun_clarity',
                'suggestion': 'Replace ambiguous pronouns with specific nouns for clarity',
                'priority': 'high'
            })
        
        if 'vague_language' in issue_types:
            suggestions.append({
                'category': 'specificity',
                'suggestion': 'Replace vague words with specific, concrete terms',
                'priority': 'medium'
            })
        
        if 'wordy_phrase' in issue_types:
            suggestions.append({
                'category': 'conciseness',
                'suggestion': 'Replace wordy phrases with concise alternatives',
                'priority': 'high'
            })
        
        if 'nominalization' in issue_types:
            suggestions.append({
                'category': 'active_language',
                'suggestion': 'Convert nominalizations to active verb forms',
                'priority': 'medium'
            })
        
        # Suggestions based on readability
        readability_level = readability_analysis.get('readability_level', 'moderate')
        
        if readability_level == 'difficult':
            suggestions.append({
                'category': 'readability',
                'suggestion': 'Break long sentences into shorter ones for better readability',
                'priority': 'high'
            })
            
            if readability_analysis.get('complex_word_ratio', 0) > 0.25:
                suggestions.append({
                    'category': 'vocabulary',
                    'suggestion': 'Replace complex words with simpler alternatives where possible',
                    'priority': 'medium'
                })
        
        # Audience-specific suggestions
        if target_audience == 'general':
            suggestions.append({
                'category': 'accessibility',
                'suggestion': 'Ensure language is accessible to a general audience',
                'priority': 'medium'
            })
        elif target_audience == 'expert':
            suggestions.append({
                'category': 'precision',
                'suggestion': 'Use precise technical language appropriate for expert audience',
                'priority': 'low'
            })
        
        return suggestions
    
    def _calculate_clarity_score(self, clarity_issues: List[Dict[str, Any]], 
                               readability_analysis: Dict[str, Any]]) -> float:
        """Calculate overall clarity score"""
        base_score = 1.0
        
        # Deduct for clarity issues
        issue_penalties = {
            'ambiguous_pronouns': 0.1,
            'vague_language': 0.05,
            'wordy_phrase': 0.08,
            'nominalization': 0.03
        }
        
        for issue in clarity_issues:
            penalty = issue_penalties.get(issue['type'], 0.05)
            base_score -= penalty
        
        # Adjust for readability
        readability_level = readability_analysis.get('readability_level', 'moderate')
        readability_adjustments = {
            'easy': 0.1,
            'moderate': 0.0,
            'difficult': -0.2
        }
        
        base_score += readability_adjustments.get(readability_level, 0.0)
        
        return round(max(0.0, min(1.0, base_score)), 2)
    
    def _prioritize_clarity_improvements(self, clarity_issues: List[Dict[str, Any]]) -> List[str]:
        """Prioritize clarity improvements"""
        high_priority = [issue['type'] for issue in clarity_issues if issue.get('severity') == 'high']
        medium_priority = [issue['type'] for issue in clarity_issues if issue.get('severity') == 'medium']
        low_priority = [issue['type'] for issue in clarity_issues if issue.get('severity') == 'low']
        
        # Remove duplicates while preserving order
        all_priorities = []
        for priority_list in [high_priority, medium_priority, low_priority]:
            for item in priority_list:
                if item not in all_priorities:
                    all_priorities.append(item)
        
        return all_priorities


class GrammarAssistantAgent(BaseWritingAgent):
    """Grammar Assistant Agent for language correctness and clarity"""
    
    def __init__(self, ai_provider_service: AIProviderService):
        super().__init__(
            agent_id="grammar_assistant",
            name="Grammar Assistant",
            ai_provider_service=ai_provider_service
        )
        
        # Initialize CrewAI agent
        self.crew_agent = Agent(
            role="Expert Grammar Specialist and Language Clarity Consultant",
            goal="Ensure grammatical correctness, proper language usage, and clear communication in all written content",
            backstory=GRAMMAR_ASSISTANT_PROMPTS["backstory"],
            verbose=True,
            allow_delegation=False,
            tools=[GrammarCheckTool(), LanguageClarityTool()],
            llm=ai_provider_service.get_primary_llm(),
            max_iter=3,
            memory=True
        )
        
        # Specializations
        self.specializations = [
            "Grammar checking and correction",
            "Spelling and punctuation",
            "Language clarity and readability",
            "Syntax and sentence structure",
            "Word usage and vocabulary",
            "Style consistency",
            "Proofreading and editing",
            "Communication effectiveness"
        ]
        
        # Grammar expertise levels
        self.grammar_expertise = {
            'spelling_correction': 0.95,
            'grammar_checking': 0.92,
            'punctuation_correction': 0.90,
            'syntax_analysis': 0.85,
            'clarity_improvement': 0.88,
            'readability_enhancement': 0.87,
            'word_usage_correction': 0.83,
            'style_consistency': 0.80
        }
        
        # Supported check levels
        self.check_levels = ['basic', 'standard', 'comprehensive', 'expert']
        
        logger.info("Grammar Assistant Agent initialized", specializations=len(self.specializations))
    
    async def execute_task(self, task_request: TaskRequest) -> TaskResponse:
        """Execute grammar checking and correction task"""
        try:
            self._start_timing()
            logger.info("Executing grammar checking task", task_id=task_request.task_id)
            
            # Analyze grammar requirements
            grammar_analysis = await self._analyze_grammar_requirements(task_request)
            
            # Perform comprehensive grammar check
            grammar_check_results = await self._perform_grammar_check(task_request, grammar_analysis)
            
            # Analyze clarity and readability
            clarity_analysis = await self._analyze_clarity(task_request, grammar_analysis)
            
            # Generate corrections and improvements
            corrections = await self._generate_corrections(
                task_request, grammar_check_results, clarity_analysis, grammar_analysis
            )
            
            # Apply corrections to create corrected text
            corrected_text = await self._apply_corrections(
                task_request.content, corrections, grammar_analysis
            )
            
            # Create response
            response = TaskResponse(
                task_id=task_request.task_id,
                agent_id=self.agent_id,
                status="completed",
                content=corrected_text,
                metadata={
                    "check_level": grammar_analysis.get("check_level"),
                    "total_errors": grammar_check_results.get("total_errors", 0),
                    "errors_corrected": len(corrections.get("applied_corrections", [])),
                    "language_quality_score": grammar_check_results.get("quality_score", 0.8),
                    "clarity_score": clarity_analysis.get("clarity_score", 0.8),
                    "error_density": grammar_check_results.get("error_density", 0.0),
                    "improvement_summary": corrections.get("improvement_summary", "")
                },
                confidence_score=self._calculate_grammar_confidence(
                    grammar_check_results, clarity_analysis, corrections
                ),
                processing_time=self._get_processing_time()
            )
            
            await self._update_performance_metrics(response)
            
            logger.info(
                "Grammar checking task completed",
                task_id=task_request.task_id,
                errors_found=grammar_check_results.get("total_errors", 0),
                errors_corrected=len(corrections.get("applied_corrections", [])),
                confidence=response.confidence_score
            )
            
            return response
            
        except Exception as e:
            logger.error("Grammar checking task failed", task_id=task_request.task_id, error=str(e))
            return self._create_error_response(task_request, str(e))
    
    async def _analyze_grammar_requirements(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Analyze grammar checking requirements"""
        try:
            # Determine check level
            check_level = self._determine_check_level(task_request.content, task_request.user_preferences)
            
            # Identify target audience for clarity adjustments
            target_audience = self._determine_target_audience(task_request.context, task_request.user_preferences)
            
            # Determine correction priorities
            priorities = self._determine_correction_priorities(task_request.content, task_request.task_type)
            
            # Check for specific requirements
            requirements = self._identify_specific_requirements(task_request.content, task_request.context)
            
            return {
                "check_level": check_level,
                "target_audience": target_audience,
                "priorities": priorities,
                "requirements": requirements,
                "preserve_style": self._should_preserve_style(task_request.user_preferences),
                "correction_aggressiveness": self._determine_correction_aggressiveness(task_request.user_preferences)
            }
            
        except Exception as e:
            logger.error("Grammar requirements analysis failed", error=str(e))
            return {
                "check_level": "standard",
                "target_audience": "general",
                "priorities": ["grammar", "spelling", "punctuation"],
                "requirements": []
            }
    
    def _determine_check_level(self, content: str, user_preferences: Optional[Dict[str, Any]]) -> str:
        """Determine appropriate checking level"""
        if user_preferences and 'check_level' in user_preferences:
            return user_preferences['check_level']
        
        content_lower = content.lower()
        
        # Expert level indicators
        if any(word in content_lower for word in ['academic', 'research', 'publication', 'formal']):
            return 'expert'
        
        # Comprehensive level indicators
        if any(word in content_lower for word in ['business', 'professional', 'important', 'official']):
            return 'comprehensive'
        
        # Basic level indicators
        if any(word in content_lower for word in ['casual', 'informal', 'quick', 'draft']):
            return 'basic'
        
        return 'standard'
    
    def _determine_target_audience(self, context: Optional[str], user_preferences: Optional[Dict[str, Any]]) -> str:
        """Determine target audience for clarity adjustments"""
        if user_preferences and 'audience' in user_preferences:
            return user_preferences['audience']
        
        if context:
            context_lower = context.lower()
            
            if any(word in context_lower for word in ['expert', 'specialist', 'professional']):
                return 'expert'
            elif any(word in context_lower for word in ['student', 'academic', 'educational']):
                return 'academic'
            elif any(word in context_lower for word in ['general', 'public', 'everyone']):
                return 'general'
        
        return 'general'
    
    def _determine_correction_priorities(self, content: str, task_type: str) -> List[str]:
        """Determine correction priorities"""
        priorities = ['grammar', 'spelling']  # Always include these
        
        content_lower = content.lower()
        
        # Add priorities based on content
        if any(word in content_lower for word in ['punctuation', 'comma', 'period', 'semicolon']):
            priorities.append('punctuation')
        
        if any(word in content_lower for word in ['clear', 'clarity', 'understand', 'confusing']):
            priorities.append('clarity')
        
        if any(word in content_lower for word in ['read', 'readable', 'flow', 'structure']):
            priorities.append('readability')
        
        # Add priorities based on task type
        if task_type in ['proofread', 'edit', 'correct']:
            priorities.extend(['punctuation', 'syntax'])
        elif task_type in ['improve', 'enhance', 'clarify']:
            priorities.extend(['clarity', 'readability'])
        
        return list(set(priorities))  # Remove duplicates
    
    def _identify_specific_requirements(self, content: str, context: Optional[str]) -> List[str]:
        """Identify specific grammar requirements"""
        requirements = []
        combined_text = f"{content} {context or ''}".lower()
        
        if 'formal' in combined_text:
            requirements.append('formal_language')
        
        if 'academic' in combined_text:
            requirements.append('academic_style')
        
        if 'business' in combined_text:
            requirements.append('business_writing')
        
        if any(word in combined_text for word in ['consistent', 'consistency']):
            requirements.append('style_consistency')
        
        return requirements
    
    def _should_preserve_style(self, user_preferences: Optional[Dict[str, Any]]) -> bool:
        """Determine if original style should be preserved"""
        if user_preferences and 'preserve_style' in user_preferences:
            return user_preferences['preserve_style']
        
        return True  # Default to preserving style
    
    def _determine_correction_aggressiveness(self, user_preferences: Optional[Dict[str, Any]]) -> str:
        """Determine how aggressively to apply corrections"""
        if user_preferences and 'correction_level' in user_preferences:
            return user_preferences['correction_level']
        
        return 'moderate'  # conservative, moderate, aggressive
    
    async def _perform_grammar_check(self, task_request: TaskRequest, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive grammar check"""
        try:
            grammar_task = Task(
                description=f"""
                Perform comprehensive grammar and language checking on the following text:
                
                Text: {task_request.content}
                Check Level: {analysis['check_level']}
                Target Audience: {analysis['target_audience']}
                Priorities: {', '.join(analysis['priorities'])}
                
                Check for:
                1. Grammar errors (subject-verb agreement, verb tenses, etc.)
                2. Spelling mistakes
                3. Punctuation errors
                4. Syntax issues
                5. Word usage problems
                6. Style inconsistencies
                
                Provide detailed analysis with specific error locations and corrections.
                Rate the overall language quality and provide improvement recommendations.
                """,
                agent=self.crew_agent,
                expected_output="Comprehensive grammar analysis with specific errors identified and corrections suggested"
            )
            
            crew = Crew(
                agents=[self.crew_agent],
                tasks=[grammar_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Also use grammar checking tool
            grammar_tool = GrammarCheckTool()
            tool_results = grammar_tool._run(task_request.content, analysis['check_level'])
            
            return {
                'ai_analysis': str(result),
                'tool_results': tool_results,
                'total_errors': tool_results.get('total_errors', 0),
                'quality_score': tool_results.get('quality_score', 0.8),
                'error_density': tool_results.get('error_density', 0.0),
                'errors_by_severity': tool_results.get('errors_by_severity', {}),
                'corrections': tool_results.get('corrections', [])
            }
            
        except Exception as e:
            logger.error("Grammar check failed", error=str(e))
            return {
                'error': str(e),
                'total_errors': 0,
                'quality_score': 0.5,
                'corrections': []
            }
    
    async def _analyze_clarity(self, task_request: TaskRequest, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze language clarity and readability"""
        try:
            clarity_task = Task(
                description=f"""
                Analyze the clarity and readability of the following text:
                
                Text: {task_request.content}
                Target Audience: {analysis['target_audience']}
                
                Analyze:
                1. Language clarity and precision
                2. Readability level
                3. Sentence structure and flow
                4. Word choice and vocabulary
                5. Communication effectiveness
                6. Potential ambiguities or confusion
                
                Provide specific recommendations for improving clarity and readability.
                """,
                agent=self.crew_agent,
                expected_output="Detailed clarity analysis with specific improvement recommendations"
            )
            
            crew = Crew(
                agents=[self.crew_agent],
                tasks=[clarity_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Also use clarity tool
            clarity_tool = LanguageClarityTool()
            tool_results = clarity_tool._run(task_request.content, analysis['target_audience'])
            
            return {
                'ai_analysis': str(result),
                'tool_results': tool_results,
                'clarity_score': tool_results.get('clarity_score', 0.8),
                'clarity_issues': tool_results.get('clarity_issues', []),
                'readability_analysis': tool_results.get('readability_analysis', {}),
                'clarity_suggestions': tool_results.get('clarity_suggestions', [])
            }
            
        except Exception as e:
            logger.error("Clarity analysis failed", error=str(e))
            return {
                'error': str(e),
                'clarity_score': 0.5,
                'clarity_issues': [],
                'clarity_suggestions': []
            }
    
    async def _generate_corrections(self, task_request: TaskRequest, 
                                  grammar_results: Dict[str, Any], 
                                  clarity_results: Dict[str, Any], 
                                  analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive corrections and improvements"""
        try:
            correction_task = Task(
                description=f"""
                Generate comprehensive corrections and improvements for the following text:
                
                Original Text: {task_request.content}
                
                Grammar Analysis: {grammar_results.get('ai_analysis', 'No analysis available')}
                Clarity Analysis: {clarity_results.get('ai_analysis', 'No analysis available')}
                
                Grammar Errors Found: {grammar_results.get('total_errors', 0)}
                Clarity Issues Found: {len(clarity_results.get('clarity_issues', []))}
                
                Correction Priorities: {', '.join(analysis['priorities'])}
                Correction Aggressiveness: {analysis['correction_aggressiveness']}
                Preserve Style: {analysis['preserve_style']}
                
                Generate corrections that:
                1. Fix all grammar, spelling, and punctuation errors
                2. Improve clarity and readability
                3. Maintain the original meaning and voice
                4. Match the target audience needs
                5. Follow the specified correction priorities
                
                Provide the corrected text with explanations for major changes.
                """,
                agent=self.crew_agent,
                expected_output="Corrected text with explanations for improvements made"
            )
            
            crew = Crew(
                agents=[self.crew_agent],
                tasks=[correction_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Compile corrections from tools
            grammar_corrections = grammar_results.get('corrections', [])
            clarity_suggestions = clarity_results.get('clarity_suggestions', [])
            
            return {
                'ai_corrections': str(result),
                'grammar_corrections': grammar_corrections,
                'clarity_suggestions': clarity_suggestions,
                'applied_corrections': self._compile_applied_corrections(grammar_corrections, clarity_suggestions),
                'improvement_summary': self._generate_improvement_summary(grammar_corrections, clarity_suggestions)
            }
            
        except Exception as e:
            logger.error("Correction generation failed", error=str(e))
            return {
                'error': str(e),
                'ai_corrections': 'Error generating corrections',
                'applied_corrections': [],
                'improvement_summary': 'Error generating improvements'
            }
    
    def _compile_applied_corrections(self, grammar_corrections: List[Dict[str, Any]], 
                                   clarity_suggestions: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Compile list of applied corrections"""
        applied = []
        
        # Add high-confidence grammar corrections
        for correction in grammar_corrections:
            if correction.get('confidence', 0) > 0.8:
                applied.append({
                    'type': 'grammar',
                    'description': correction.get('explanation', ''),
                    'confidence': correction.get('confidence', 0)
                })
        
        # Add high-priority clarity suggestions
        for suggestion in clarity_suggestions:
            if suggestion.get('priority') == 'high':
                applied.append({
                    'type': 'clarity',
                    'description': suggestion.get('suggestion', ''),
                    'confidence': 0.8  # Default confidence for clarity suggestions
                })
        
        return applied
    
    def _generate_improvement_summary(self, grammar_corrections: List[Dict[str, Any]], 
                                    clarity_suggestions: List[Dict[str, str]]) -> str:
        """Generate summary of improvements made"""
        improvements = []
        
        if grammar_corrections:
            grammar_count = len([c for c in grammar_corrections if c.get('confidence', 0) > 0.8])
            if grammar_count > 0:
                improvements.append(f"corrected {grammar_count} grammar/language errors")
        
        clarity_count = len([s for s in clarity_suggestions if s.get('priority') == 'high'])
        if clarity_count > 0:
            improvements.append(f"applied {clarity_count} clarity improvements")
        
        if not improvements:
            return "Text reviewed with minimal corrections needed"
        
        if len(improvements) == 1:
            return f"Applied improvements: {improvements[0]}"
        else:
            return f"Applied improvements: {', '.join(improvements[:-1])}, and {improvements[-1]}"
    
    async def _apply_corrections(self, content: str, corrections: Dict[str, Any], 
                               analysis: Dict[str, Any]) -> str:
        """Apply corrections to create final corrected text"""
        try:
            application_task = Task(
                description=f"""
                Apply the following corrections to improve the text:
                
                Original Text: {content}
                
                AI Corrections: {corrections.get('ai_corrections', '')}
                Grammar Corrections: {len(corrections.get('grammar_corrections', []))} corrections available
                Clarity Suggestions: {len(corrections.get('clarity_suggestions', []))} suggestions available
                
                Correction Guidelines:
                - Preserve original style: {analysis['preserve_style']}
                - Correction level: {analysis['correction_aggressiveness']}
                - Target audience: {analysis['target_audience']}
                
                Apply corrections while:
                1. Maintaining the original meaning and voice
                2. Ensuring grammatical correctness
                3. Improving clarity and readability
                4. Preserving the author's intended style
                5. Making text appropriate for target audience
                
                Return the corrected text with all improvements applied.
                """,
                agent=self.crew_agent,
                expected_output="Final corrected text with all improvements applied"
            )
            
            crew = Crew(
                agents=[self.crew_agent],
                tasks=[application_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            return str(result) if str(result).strip() else content
            
        except Exception as e:
            logger.error("Correction application failed", error=str(e))
            return content  # Return original if correction fails
    
    def _calculate_grammar_confidence(self, grammar_results: Dict[str, Any], 
                                    clarity_results: Dict[str, Any], 
                                    corrections: Dict[str, Any]) -> float:
        """Calculate confidence score for grammar checking"""
        try:
            base_confidence = 0.85
            
            # Adjust based on error detection confidence
            total_errors = grammar_results.get('total_errors', 0)
            quality_score = grammar_results.get('quality_score', 0.8)
            
            # Higher confidence for texts with fewer errors
            error_adjustment = min(0.1, total_errors * 0.02)  # Reduce confidence for more errors
            quality_adjustment = (quality_score - 0.5) * 0.2  # Adjust based on quality
            
            # Adjust based on clarity analysis
            clarity_score = clarity_results.get('clarity_score', 0.8)
            clarity_adjustment = (clarity_score - 0.5) * 0.1
            
            # Adjust based on correction success
            applied_corrections = corrections.get('applied_corrections', [])
            correction_confidence = sum(c.get('confidence', 0.8) for c in applied_corrections)
            if applied_corrections:
                correction_adjustment = (correction_confidence / len(applied_corrections) - 0.8) * 0.1
            else:
                correction_adjustment = 0.05  # Slight boost if no corrections needed
            
            final_confidence = base_confidence - error_adjustment + quality_adjustment + clarity_adjustment + correction_adjustment
            return round(min(max(final_confidence, 0.1), 1.0), 2)
            
        except Exception:
            return 0.85
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get grammar assistant capabilities"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "specializations": self.specializations,
            "grammar_types": list(self.grammar_expertise.keys()),
            "expertise_levels": self.grammar_expertise,
            "supported_tasks": ["proofread", "correct", "check", "improve", "edit", "clarify"],
            "check_levels": self.check_levels,
            "error_types": [
                "spelling", "grammar", "punctuation", "syntax", 
                "word_usage", "clarity", "readability"
            ],
            "correction_levels": ["conservative", "moderate", "aggressive"],
            "style_preservation": True,
            "clarity_analysis": True,
            "readability_assessment": True,
            "languages": ["English"],
            "collaboration_ready": True,
            "max_text_length": 15000  # words
        }

