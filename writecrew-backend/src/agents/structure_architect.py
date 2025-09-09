"""
Structure Architect Agent - Document Organization and Flow Optimization
Specialized CrewAI agent for document structure, organization, and narrative flow
"""

import asyncio
import re
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import structlog

from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from ..models.task import TaskRequest, TaskResponse
from ..services.ai_providers import AIProviderService
from ..utils.prompts import STRUCTURE_ARCHITECT_PROMPTS
from .base_agent import BaseWritingAgent

logger = structlog.get_logger(__name__)


class DocumentStructureTool(BaseTool):
    """Tool for analyzing and optimizing document structure"""
    
    name: str = "document_structure_analyzer"
    description: str = "Analyze document structure, organization, and hierarchical flow"
    
    def _run(self, text: str, document_type: str = "general") -> Dict[str, Any]:
        """Analyze document structure and organization"""
        try:
            # Analyze current structure
            current_structure = self._analyze_current_structure(text)
            
            # Identify structural issues
            structural_issues = self._identify_structural_issues(text, current_structure)
            
            # Analyze content hierarchy
            hierarchy_analysis = self._analyze_content_hierarchy(text, current_structure)
            
            # Generate structure recommendations
            structure_recommendations = self._generate_structure_recommendations(
                text, current_structure, structural_issues, document_type
            )
            
            # Assess structural coherence
            coherence_score = self._calculate_structural_coherence(
                current_structure, structural_issues
            )
            
            return {
                'text': text,
                'document_type': document_type,
                'current_structure': current_structure,
                'structural_issues': structural_issues,
                'hierarchy_analysis': hierarchy_analysis,
                'structure_recommendations': structure_recommendations,
                'coherence_score': coherence_score,
                'structure_quality': self._assess_structure_quality(current_structure, structural_issues)
            }
            
        except Exception as e:
            logger.error("Document structure analysis failed", error=str(e))
            return {
                'text': text,
                'error': str(e),
                'coherence_score': 0.5,
                'structure_recommendations': []
            }
    
    def _analyze_current_structure(self, text: str) -> Dict[str, Any]:
        """Analyze the current document structure"""
        # Identify headings and sections
        headings = self._extract_headings(text)
        
        # Analyze paragraphs
        paragraphs = self._analyze_paragraphs(text)
        
        # Identify transitions
        transitions = self._identify_transitions(text)
        
        # Analyze document flow
        flow_analysis = self._analyze_document_flow(text, paragraphs)
        
        # Calculate structural metrics
        structural_metrics = self._calculate_structural_metrics(headings, paragraphs)
        
        return {
            'headings': headings,
            'paragraphs': paragraphs,
            'transitions': transitions,
            'flow_analysis': flow_analysis,
            'structural_metrics': structural_metrics,
            'total_sections': len(headings),
            'total_paragraphs': len(paragraphs),
            'average_paragraph_length': structural_metrics.get('avg_paragraph_length', 0)
        }
    
    def _extract_headings(self, text: str) -> List[Dict[str, Any]]:
        """Extract and analyze headings"""
        headings = []
        
        # Markdown-style headings
        markdown_pattern = r'^(#{1,6})\s+(.+)$'
        for match in re.finditer(markdown_pattern, text, re.MULTILINE):
            level = len(match.group(1))
            title = match.group(2).strip()
            headings.append({
                'type': 'markdown',
                'level': level,
                'title': title,
                'position': match.start(),
                'raw': match.group(0)
            })
        
        # Numbered headings (1., 1.1, etc.)
        numbered_pattern = r'^(\d+(?:\.\d+)*\.?)\s+(.+)$'
        for match in re.finditer(numbered_pattern, text, re.MULTILINE):
            number = match.group(1)
            title = match.group(2).strip()
            level = number.count('.') + 1
            headings.append({
                'type': 'numbered',
                'level': level,
                'number': number,
                'title': title,
                'position': match.start(),
                'raw': match.group(0)
            })
        
        # All caps headings (potential headings)
        caps_pattern = r'^([A-Z][A-Z\s]{3,})$'
        for match in re.finditer(caps_pattern, text, re.MULTILINE):
            title = match.group(1).strip()
            if len(title.split()) <= 8:  # Reasonable heading length
                headings.append({
                    'type': 'caps',
                    'level': 1,  # Assume top level
                    'title': title,
                    'position': match.start(),
                    'raw': match.group(0)
                })
        
        # Sort by position
        headings.sort(key=lambda x: x['position'])
        
        return headings
    
    def _analyze_paragraphs(self, text: str) -> List[Dict[str, Any]]:
        """Analyze paragraph structure and characteristics"""
        paragraphs = []
        
        # Split into paragraphs (double newline or significant whitespace)
        paragraph_texts = re.split(r'\n\s*\n', text)
        current_position = 0
        
        for i, para_text in enumerate(paragraph_texts):
            para_text = para_text.strip()
            if not para_text:
                continue
            
            # Find position in original text
            para_start = text.find(para_text, current_position)
            if para_start == -1:
                para_start = current_position
            
            # Analyze paragraph characteristics
            sentences = self._split_sentences(para_text)
            words = para_text.split()
            
            paragraph_info = {
                'index': i,
                'text': para_text,
                'position': para_start,
                'length': len(para_text),
                'word_count': len(words),
                'sentence_count': len(sentences),
                'avg_sentence_length': len(words) / len(sentences) if sentences else 0,
                'starts_with_transition': self._starts_with_transition(para_text),
                'topic_sentence_strength': self._assess_topic_sentence(sentences[0] if sentences else ''),
                'coherence_indicators': self._identify_coherence_indicators(para_text),
                'paragraph_type': self._classify_paragraph_type(para_text)
            }
            
            paragraphs.append(paragraph_info)
            current_position = para_start + len(para_text)
        
        return paragraphs
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting (can be enhanced with NLP libraries)
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _starts_with_transition(self, paragraph: str) -> bool:
        """Check if paragraph starts with a transition word/phrase"""
        transition_words = [
            'however', 'therefore', 'furthermore', 'moreover', 'consequently',
            'nevertheless', 'additionally', 'meanwhile', 'subsequently', 'thus',
            'hence', 'accordingly', 'similarly', 'conversely', 'in contrast',
            'on the other hand', 'as a result', 'in addition', 'for example',
            'for instance', 'in conclusion', 'to summarize', 'finally'
        ]
        
        first_words = paragraph.lower().split()[:3]  # Check first few words
        first_phrase = ' '.join(first_words)
        
        return any(transition in first_phrase for transition in transition_words)
    
    def _assess_topic_sentence(self, sentence: str) -> float:
        """Assess the strength of a topic sentence"""
        if not sentence:
            return 0.0
        
        score = 0.5  # Base score
        
        # Strong topic sentence indicators
        if any(word in sentence.lower() for word in ['this', 'these', 'the main', 'key', 'important']):
            score += 0.2
        
        # Weak topic sentence indicators
        if sentence.lower().startswith(('i', 'we', 'you', 'it')):
            score -= 0.1
        
        # Length consideration
        word_count = len(sentence.split())
        if 10 <= word_count <= 25:  # Optimal topic sentence length
            score += 0.1
        elif word_count > 35:  # Too long
            score -= 0.2
        
        return min(1.0, max(0.0, score))
    
    def _identify_coherence_indicators(self, paragraph: str) -> List[str]:
        """Identify coherence indicators in paragraph"""
        indicators = []
        para_lower = paragraph.lower()
        
        # Pronoun references
        if any(pronoun in para_lower for pronoun in ['this', 'that', 'these', 'those', 'it', 'they']):
            indicators.append('pronoun_reference')
        
        # Repetition of key terms
        words = para_lower.split()
        word_freq = {}
        for word in words:
            if len(word) > 4:  # Only consider substantial words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        repeated_words = [word for word, freq in word_freq.items() if freq > 1]
        if repeated_words:
            indicators.append('key_term_repetition')
        
        # Logical connectors
        connectors = ['because', 'since', 'although', 'while', 'whereas', 'if', 'when', 'after', 'before']
        if any(connector in para_lower for connector in connectors):
            indicators.append('logical_connectors')
        
        return indicators
    
    def _classify_paragraph_type(self, paragraph: str) -> str:
        """Classify the type/purpose of paragraph"""
        para_lower = paragraph.lower()
        
        # Introduction paragraph
        if any(phrase in para_lower for phrase in ['introduce', 'begin', 'start', 'overview', 'this paper', 'this document']):
            return 'introduction'
        
        # Conclusion paragraph
        if any(phrase in para_lower for phrase in ['conclude', 'in conclusion', 'finally', 'to summarize', 'in summary']):
            return 'conclusion'
        
        # Example paragraph
        if any(phrase in para_lower for phrase in ['for example', 'for instance', 'such as', 'consider']):
            return 'example'
        
        # Transition paragraph
        if len(paragraph.split()) < 50 and self._starts_with_transition(paragraph):
            return 'transition'
        
        # Evidence/support paragraph
        if any(phrase in para_lower for phrase in ['research shows', 'studies indicate', 'evidence suggests', 'data reveals']):
            return 'evidence'
        
        return 'body'  # Default
    
    def _identify_transitions(self, text: str) -> List[Dict[str, Any]]:
        """Identify transition words and phrases in text"""
        transitions = []
        
        transition_patterns = {
            'addition': r'\b(furthermore|moreover|additionally|also|besides|in addition)\b',
            'contrast': r'\b(however|nevertheless|nonetheless|conversely|on the other hand|in contrast)\b',
            'cause_effect': r'\b(therefore|thus|consequently|as a result|hence|accordingly)\b',
            'sequence': r'\b(first|second|third|next|then|finally|subsequently|meanwhile)\b',
            'example': r'\b(for example|for instance|such as|namely|specifically)\b',
            'emphasis': r'\b(indeed|certainly|obviously|clearly|undoubtedly)\b',
            'conclusion': r'\b(in conclusion|to conclude|in summary|to summarize|overall)\b'
        }
        
        for category, pattern in transition_patterns.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                transitions.append({
                    'category': category,
                    'text': match.group(),
                    'position': match.start(),
                    'context': text[max(0, match.start()-30):match.end()+30]
                })
        
        return sorted(transitions, key=lambda x: x['position'])
    
    def _analyze_document_flow(self, text: str, paragraphs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the flow and progression of the document"""
        if not paragraphs:
            return {'flow_score': 0.0, 'issues': ['No paragraphs found']}
        
        flow_issues = []
        flow_score = 1.0
        
        # Check paragraph length consistency
        lengths = [p['word_count'] for p in paragraphs]
        avg_length = sum(lengths) / len(lengths)
        
        very_short = [i for i, length in enumerate(lengths) if length < avg_length * 0.3]
        very_long = [i for i, length in enumerate(lengths) if length > avg_length * 3]
        
        if very_short:
            flow_issues.append(f"Very short paragraphs at positions: {very_short}")
            flow_score -= 0.1
        
        if very_long:
            flow_issues.append(f"Very long paragraphs at positions: {very_long}")
            flow_score -= 0.1
        
        # Check transition usage
        transition_count = sum(1 for p in paragraphs if p['starts_with_transition'])
        transition_ratio = transition_count / len(paragraphs)
        
        if transition_ratio < 0.2:
            flow_issues.append("Few transition words between paragraphs")
            flow_score -= 0.2
        elif transition_ratio > 0.8:
            flow_issues.append("Overuse of transition words")
            flow_score -= 0.1
        
        # Check topic sentence strength
        topic_scores = [p['topic_sentence_strength'] for p in paragraphs]
        avg_topic_strength = sum(topic_scores) / len(topic_scores)
        
        if avg_topic_strength < 0.5:
            flow_issues.append("Weak topic sentences")
            flow_score -= 0.2
        
        # Check coherence indicators
        coherent_paragraphs = sum(1 for p in paragraphs if p['coherence_indicators'])
        coherence_ratio = coherent_paragraphs / len(paragraphs)
        
        if coherence_ratio < 0.4:
            flow_issues.append("Limited coherence indicators between ideas")
            flow_score -= 0.2
        
        return {
            'flow_score': max(0.0, flow_score),
            'issues': flow_issues,
            'transition_ratio': transition_ratio,
            'avg_topic_strength': avg_topic_strength,
            'coherence_ratio': coherence_ratio,
            'paragraph_length_consistency': self._calculate_length_consistency(lengths)
        }
    
    def _calculate_length_consistency(self, lengths: List[int]) -> float:
        """Calculate consistency of paragraph lengths"""
        if len(lengths) < 2:
            return 1.0
        
        avg_length = sum(lengths) / len(lengths)
        variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
        std_dev = variance ** 0.5
        
        # Coefficient of variation (lower is more consistent)
        cv = std_dev / avg_length if avg_length > 0 else 1.0
        
        # Convert to consistency score (0-1, higher is more consistent)
        consistency = max(0.0, 1.0 - min(cv, 1.0))
        return consistency
    
    def _calculate_structural_metrics(self, headings: List[Dict[str, Any]], 
                                    paragraphs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate structural metrics"""
        metrics = {}
        
        if paragraphs:
            word_counts = [p['word_count'] for p in paragraphs]
            metrics['avg_paragraph_length'] = sum(word_counts) / len(word_counts)
            metrics['min_paragraph_length'] = min(word_counts)
            metrics['max_paragraph_length'] = max(word_counts)
            
            sentence_counts = [p['sentence_count'] for p in paragraphs]
            metrics['avg_sentences_per_paragraph'] = sum(sentence_counts) / len(sentence_counts)
        
        if headings:
            levels = [h['level'] for h in headings]
            metrics['heading_levels_used'] = len(set(levels))
            metrics['max_heading_level'] = max(levels)
            metrics['heading_distribution'] = {level: levels.count(level) for level in set(levels)}
        
        return metrics
    
    def _identify_structural_issues(self, text: str, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify structural issues in the document"""
        issues = []
        
        headings = structure.get('headings', [])
        paragraphs = structure.get('paragraphs', [])
        flow_analysis = structure.get('flow_analysis', {})
        
        # Heading structure issues
        if not headings:
            issues.append({
                'type': 'missing_headings',
                'severity': 'medium',
                'description': 'Document lacks clear headings for organization',
                'suggestion': 'Add descriptive headings to organize content into sections'
            })
        else:
            # Check heading hierarchy
            levels = [h['level'] for h in headings]
            if levels:
                # Check for skipped levels
                unique_levels = sorted(set(levels))
                for i in range(1, len(unique_levels)):
                    if unique_levels[i] - unique_levels[i-1] > 1:
                        issues.append({
                            'type': 'skipped_heading_level',
                            'severity': 'low',
                            'description': f'Heading hierarchy skips from level {unique_levels[i-1]} to {unique_levels[i]}',
                            'suggestion': 'Use consecutive heading levels for better hierarchy'
                        })
        
        # Paragraph structure issues
        if paragraphs:
            # Very short paragraphs
            short_paragraphs = [p for p in paragraphs if p['word_count'] < 20]
            if len(short_paragraphs) > len(paragraphs) * 0.3:
                issues.append({
                    'type': 'too_many_short_paragraphs',
                    'severity': 'medium',
                    'description': f'{len(short_paragraphs)} paragraphs are very short (< 20 words)',
                    'suggestion': 'Consider combining short paragraphs or developing ideas more fully'
                })
            
            # Very long paragraphs
            long_paragraphs = [p for p in paragraphs if p['word_count'] > 200]
            if long_paragraphs:
                issues.append({
                    'type': 'overly_long_paragraphs',
                    'severity': 'medium',
                    'description': f'{len(long_paragraphs)} paragraphs are very long (> 200 words)',
                    'suggestion': 'Break long paragraphs into smaller, focused units'
                })
            
            # Weak topic sentences
            weak_topic_paragraphs = [p for p in paragraphs if p['topic_sentence_strength'] < 0.3]
            if len(weak_topic_paragraphs) > len(paragraphs) * 0.4:
                issues.append({
                    'type': 'weak_topic_sentences',
                    'severity': 'high',
                    'description': f'{len(weak_topic_paragraphs)} paragraphs have weak topic sentences',
                    'suggestion': 'Strengthen topic sentences to clearly introduce paragraph main ideas'
                })
        
        # Flow issues
        flow_issues = flow_analysis.get('issues', [])
        for flow_issue in flow_issues:
            issues.append({
                'type': 'flow_issue',
                'severity': 'medium',
                'description': flow_issue,
                'suggestion': 'Improve document flow with better transitions and organization'
            })
        
        # Missing introduction/conclusion
        if paragraphs:
            paragraph_types = [p['paragraph_type'] for p in paragraphs]
            if 'introduction' not in paragraph_types:
                issues.append({
                    'type': 'missing_introduction',
                    'severity': 'high',
                    'description': 'Document appears to lack a clear introduction',
                    'suggestion': 'Add an introduction paragraph to orient readers'
                })
            
            if 'conclusion' not in paragraph_types and len(paragraphs) > 3:
                issues.append({
                    'type': 'missing_conclusion',
                    'severity': 'medium',
                    'description': 'Document appears to lack a clear conclusion',
                    'suggestion': 'Add a conclusion to summarize key points'
                })
        
        return issues
    
    def _analyze_content_hierarchy(self, text: str, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content hierarchy and organization"""
        headings = structure.get('headings', [])
        paragraphs = structure.get('paragraphs', [])
        
        if not headings:
            return {
                'hierarchy_type': 'flat',
                'depth': 0,
                'organization_score': 0.3,
                'sections': []
            }
        
        # Build hierarchy tree
        hierarchy_tree = self._build_hierarchy_tree(headings)
        
        # Analyze sections
        sections = self._analyze_sections(text, headings, paragraphs)
        
        # Calculate organization score
        organization_score = self._calculate_organization_score(hierarchy_tree, sections)
        
        return {
            'hierarchy_type': self._classify_hierarchy_type(hierarchy_tree),
            'depth': self._calculate_hierarchy_depth(hierarchy_tree),
            'organization_score': organization_score,
            'sections': sections,
            'hierarchy_tree': hierarchy_tree,
            'balance_score': self._calculate_hierarchy_balance(sections)
        }
    
    def _build_hierarchy_tree(self, headings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build hierarchical tree from headings"""
        if not headings:
            return {}
        
        root = {'level': 0, 'children': [], 'title': 'Document Root'}
        stack = [root]
        
        for heading in headings:
            level = heading['level']
            
            # Find appropriate parent
            while len(stack) > 1 and stack[-1]['level'] >= level:
                stack.pop()
            
            parent = stack[-1]
            node = {
                'level': level,
                'title': heading['title'],
                'type': heading.get('type', 'unknown'),
                'position': heading['position'],
                'children': []
            }
            
            parent['children'].append(node)
            stack.append(node)
        
        return root
    
    def _classify_hierarchy_type(self, hierarchy_tree: Dict[str, Any]) -> str:
        """Classify the type of hierarchy"""
        if not hierarchy_tree.get('children'):
            return 'none'
        
        levels_used = set()
        self._collect_levels(hierarchy_tree, levels_used)
        
        max_level = max(levels_used) if levels_used else 0
        
        if max_level <= 1:
            return 'flat'
        elif max_level <= 2:
            return 'shallow'
        elif max_level <= 3:
            return 'moderate'
        else:
            return 'deep'
    
    def _collect_levels(self, node: Dict[str, Any], levels: set):
        """Recursively collect all levels in hierarchy"""
        if 'level' in node:
            levels.add(node['level'])
        
        for child in node.get('children', []):
            self._collect_levels(child, levels)
    
    def _calculate_hierarchy_depth(self, hierarchy_tree: Dict[str, Any]) -> int:
        """Calculate maximum depth of hierarchy"""
        if not hierarchy_tree.get('children'):
            return 0
        
        max_depth = 0
        for child in hierarchy_tree['children']:
            child_depth = self._calculate_hierarchy_depth(child)
            max_depth = max(max_depth, child_depth + 1)
        
        return max_depth
    
    def _analyze_sections(self, text: str, headings: List[Dict[str, Any]], 
                         paragraphs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze individual sections of the document"""
        sections = []
        
        if not headings:
            # Treat entire document as one section
            return [{
                'title': 'Main Content',
                'start_position': 0,
                'end_position': len(text),
                'paragraph_count': len(paragraphs),
                'word_count': len(text.split()),
                'level': 1
            }]
        
        for i, heading in enumerate(headings):
            start_pos = heading['position']
            end_pos = headings[i + 1]['position'] if i + 1 < len(headings) else len(text)
            
            section_text = text[start_pos:end_pos]
            section_paragraphs = [p for p in paragraphs if start_pos <= p['position'] < end_pos]
            
            sections.append({
                'title': heading['title'],
                'level': heading['level'],
                'start_position': start_pos,
                'end_position': end_pos,
                'paragraph_count': len(section_paragraphs),
                'word_count': len(section_text.split()),
                'avg_paragraph_length': sum(p['word_count'] for p in section_paragraphs) / len(section_paragraphs) if section_paragraphs else 0,
                'section_type': self._classify_section_type(heading['title'], section_text)
            })
        
        return sections
    
    def _classify_section_type(self, title: str, content: str) -> str:
        """Classify the type of section based on title and content"""
        title_lower = title.lower()
        content_lower = content.lower()
        
        # Introduction section
        if any(word in title_lower for word in ['introduction', 'intro', 'overview', 'background']):
            return 'introduction'
        
        # Conclusion section
        if any(word in title_lower for word in ['conclusion', 'summary', 'final', 'closing']):
            return 'conclusion'
        
        # Methods/methodology section
        if any(word in title_lower for word in ['method', 'methodology', 'approach', 'procedure']):
            return 'methodology'
        
        # Results section
        if any(word in title_lower for word in ['result', 'finding', 'outcome', 'data']):
            return 'results'
        
        # Discussion section
        if any(word in title_lower for word in ['discussion', 'analysis', 'interpretation']):
            return 'discussion'
        
        # Literature review
        if any(word in title_lower for word in ['literature', 'review', 'related work', 'background']):
            return 'literature_review'
        
        return 'content'  # Default
    
    def _calculate_organization_score(self, hierarchy_tree: Dict[str, Any], 
                                    sections: List[Dict[str, Any]]) -> float:
        """Calculate overall organization score"""
        score = 0.5  # Base score
        
        # Hierarchy bonus
        if hierarchy_tree.get('children'):
            depth = self._calculate_hierarchy_depth(hierarchy_tree)
            if 1 <= depth <= 3:  # Optimal depth
                score += 0.2
            elif depth > 3:
                score += 0.1  # Deep hierarchy is okay but not optimal
        
        # Section balance bonus
        if sections:
            word_counts = [s['word_count'] for s in sections]
            if word_counts:
                avg_words = sum(word_counts) / len(word_counts)
                # Check if sections are reasonably balanced
                balanced_sections = sum(1 for wc in word_counts if 0.3 * avg_words <= wc <= 3 * avg_words)
                balance_ratio = balanced_sections / len(sections)
                score += balance_ratio * 0.2
        
        # Section type diversity bonus
        section_types = [s.get('section_type', 'content') for s in sections]
        unique_types = len(set(section_types))
        if unique_types > 1:
            score += min(0.1, unique_types * 0.02)
        
        return min(1.0, score)
    
    def _calculate_hierarchy_balance(self, sections: List[Dict[str, Any]]) -> float:
        """Calculate balance of hierarchy (how evenly distributed sections are)"""
        if not sections:
            return 0.0
        
        word_counts = [s['word_count'] for s in sections]
        if not word_counts:
            return 0.0
        
        avg_words = sum(word_counts) / len(word_counts)
        variance = sum((wc - avg_words) ** 2 for wc in word_counts) / len(word_counts)
        std_dev = variance ** 0.5
        
        # Coefficient of variation
        cv = std_dev / avg_words if avg_words > 0 else 1.0
        
        # Convert to balance score (lower CV = higher balance)
        balance_score = max(0.0, 1.0 - min(cv, 1.0))
        return balance_score
    
    def _generate_structure_recommendations(self, text: str, structure: Dict[str, Any], 
                                          issues: List[Dict[str, Any]], 
                                          document_type: str) -> List[Dict[str, Any]]:
        """Generate recommendations for improving document structure"""
        recommendations = []
        
        # Recommendations based on document type
        type_recommendations = self._get_type_specific_recommendations(document_type, structure)
        recommendations.extend(type_recommendations)
        
        # Recommendations based on identified issues
        for issue in issues:
            if issue['type'] == 'missing_headings':
                recommendations.append({
                    'type': 'add_headings',
                    'priority': 'high',
                    'description': 'Add descriptive headings to organize content',
                    'specific_suggestion': 'Consider adding headings every 3-5 paragraphs or at major topic changes'
                })
            
            elif issue['type'] == 'weak_topic_sentences':
                recommendations.append({
                    'type': 'strengthen_topic_sentences',
                    'priority': 'high',
                    'description': 'Improve topic sentences to better introduce paragraph ideas',
                    'specific_suggestion': 'Start paragraphs with clear, specific statements about the main point'
                })
            
            elif issue['type'] == 'overly_long_paragraphs':
                recommendations.append({
                    'type': 'break_long_paragraphs',
                    'priority': 'medium',
                    'description': 'Break long paragraphs into smaller, focused units',
                    'specific_suggestion': 'Aim for 3-5 sentences per paragraph, with one main idea each'
                })
            
            elif issue['type'] == 'too_many_short_paragraphs':
                recommendations.append({
                    'type': 'develop_short_paragraphs',
                    'priority': 'medium',
                    'description': 'Develop short paragraphs with more detail and examples',
                    'specific_suggestion': 'Add supporting details, examples, or combine related short paragraphs'
                })
        
        # Flow improvement recommendations
        flow_analysis = structure.get('flow_analysis', {})
        if flow_analysis.get('transition_ratio', 0) < 0.2:
            recommendations.append({
                'type': 'add_transitions',
                'priority': 'medium',
                'description': 'Add transition words and phrases between paragraphs',
                'specific_suggestion': 'Use transitions like "however," "furthermore," "in addition" to connect ideas'
            })
        
        # Hierarchy recommendations
        hierarchy_analysis = structure.get('hierarchy_analysis', {})
        if hierarchy_analysis.get('organization_score', 0) < 0.6:
            recommendations.append({
                'type': 'improve_organization',
                'priority': 'high',
                'description': 'Improve overall document organization and structure',
                'specific_suggestion': 'Consider reorganizing content into clear, logical sections with descriptive headings'
            })
        
        return recommendations
    
    def _get_type_specific_recommendations(self, document_type: str, 
                                         structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get recommendations specific to document type"""
        recommendations = []
        paragraphs = structure.get('paragraphs', [])
        
        if document_type == 'academic':
            # Academic papers need specific structure
            paragraph_types = [p.get('paragraph_type', 'body') for p in paragraphs]
            
            if 'introduction' not in paragraph_types:
                recommendations.append({
                    'type': 'add_academic_introduction',
                    'priority': 'high',
                    'description': 'Add a clear introduction with thesis statement',
                    'specific_suggestion': 'Include background, research question, and thesis in introduction'
                })
            
            if len(paragraphs) > 5 and 'conclusion' not in paragraph_types:
                recommendations.append({
                    'type': 'add_academic_conclusion',
                    'priority': 'high',
                    'description': 'Add a conclusion that summarizes findings and implications',
                    'specific_suggestion': 'Restate thesis, summarize main points, discuss implications'
                })
        
        elif document_type == 'business':
            # Business documents need executive summary, clear sections
            if len(paragraphs) > 3:
                recommendations.append({
                    'type': 'add_executive_summary',
                    'priority': 'medium',
                    'description': 'Consider adding an executive summary',
                    'specific_suggestion': 'Summarize key points and recommendations at the beginning'
                })
        
        elif document_type == 'creative':
            # Creative writing has different structure needs
            recommendations.append({
                'type': 'creative_structure',
                'priority': 'low',
                'description': 'Ensure narrative structure supports story flow',
                'specific_suggestion': 'Consider story arc: setup, conflict, climax, resolution'
            })
        
        return recommendations
    
    def _calculate_structural_coherence(self, structure: Dict[str, Any], 
                                      issues: List[Dict[str, Any]]) -> float:
        """Calculate overall structural coherence score"""
        base_score = 1.0
        
        # Deduct for structural issues
        for issue in issues:
            severity = issue.get('severity', 'medium')
            if severity == 'high':
                base_score -= 0.2
            elif severity == 'medium':
                base_score -= 0.1
            else:  # low
                base_score -= 0.05
        
        # Bonus for good flow
        flow_analysis = structure.get('flow_analysis', {})
        flow_score = flow_analysis.get('flow_score', 0.5)
        base_score += (flow_score - 0.5) * 0.2
        
        # Bonus for good hierarchy
        hierarchy_analysis = structure.get('hierarchy_analysis', {})
        org_score = hierarchy_analysis.get('organization_score', 0.5)
        base_score += (org_score - 0.5) * 0.2
        
        return round(max(0.0, min(1.0, base_score)), 2)
    
    def _assess_structure_quality(self, structure: Dict[str, Any], 
                                issues: List[Dict[str, Any]]) -> str:
        """Assess overall structure quality"""
        coherence_score = self._calculate_structural_coherence(structure, issues)
        
        if coherence_score >= 0.8:
            return 'excellent'
        elif coherence_score >= 0.6:
            return 'good'
        elif coherence_score >= 0.4:
            return 'fair'
        else:
            return 'needs_improvement'


class FlowOptimizationTool(BaseTool):
    """Tool for optimizing document flow and narrative progression"""
    
    name: str = "flow_optimizer"
    description: str = "Optimize document flow, transitions, and narrative progression"
    
    def _run(self, text: str, optimization_level: str = "standard") -> Dict[str, Any]:
        """Optimize document flow and progression"""
        try:
            # Analyze current flow
            flow_analysis = self._analyze_current_flow(text)
            
            # Identify flow problems
            flow_problems = self._identify_flow_problems(text, flow_analysis)
            
            # Generate flow improvements
            flow_improvements = self._generate_flow_improvements(
                text, flow_analysis, flow_problems, optimization_level
            )
            
            # Optimize transitions
            transition_optimization = self._optimize_transitions(text, flow_analysis)
            
            # Assess narrative progression
            narrative_analysis = self._analyze_narrative_progression(text)
            
            return {
                'text': text,
                'optimization_level': optimization_level,
                'flow_analysis': flow_analysis,
                'flow_problems': flow_problems,
                'flow_improvements': flow_improvements,
                'transition_optimization': transition_optimization,
                'narrative_analysis': narrative_analysis,
                'flow_score': self._calculate_flow_score(flow_analysis, flow_problems),
                'optimization_priority': self._prioritize_flow_improvements(flow_problems)
            }
            
        except Exception as e:
            logger.error("Flow optimization failed", error=str(e))
            return {
                'text': text,
                'error': str(e),
                'flow_score': 0.5,
                'flow_improvements': []
            }
    
    def _analyze_current_flow(self, text: str) -> Dict[str, Any]:
        """Analyze current document flow"""
        sentences = self._split_into_sentences(text)
        paragraphs = text.split('\n\n')
        
        # Analyze sentence connections
        sentence_connections = self._analyze_sentence_connections(sentences)
        
        # Analyze paragraph transitions
        paragraph_transitions = self._analyze_paragraph_transitions(paragraphs)
        
        # Analyze logical progression
        logical_progression = self._analyze_logical_progression(text, sentences)
        
        # Analyze rhythm and pacing
        rhythm_analysis = self._analyze_rhythm_and_pacing(sentences)
        
        return {
            'sentence_connections': sentence_connections,
            'paragraph_transitions': paragraph_transitions,
            'logical_progression': logical_progression,
            'rhythm_analysis': rhythm_analysis,
            'total_sentences': len(sentences),
            'total_paragraphs': len(paragraphs)
        }
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Enhanced sentence splitting
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _analyze_sentence_connections(self, sentences: List[str]) -> Dict[str, Any]:
        """Analyze how sentences connect to each other"""
        connections = []
        
        for i in range(len(sentences) - 1):
            current = sentences[i]
            next_sent = sentences[i + 1]
            
            connection_strength = self._assess_sentence_connection(current, next_sent)
            connection_type = self._identify_connection_type(current, next_sent)
            
            connections.append({
                'index': i,
                'current_sentence': current[:50] + '...' if len(current) > 50 else current,
                'next_sentence': next_sent[:50] + '...' if len(next_sent) > 50 else next_sent,
                'connection_strength': connection_strength,
                'connection_type': connection_type
            })
        
        avg_connection_strength = sum(c['connection_strength'] for c in connections) / len(connections) if connections else 0
        
        return {
            'connections': connections,
            'average_connection_strength': avg_connection_strength,
            'weak_connections': [c for c in connections if c['connection_strength'] < 0.3],
            'strong_connections': [c for c in connections if c['connection_strength'] > 0.7]
        }
    
    def _assess_sentence_connection(self, sentence1: str, sentence2: str) -> float:
        """Assess connection strength between two sentences"""
        score = 0.3  # Base score
        
        s1_words = set(sentence1.lower().split())
        s2_words = set(sentence2.lower().split())
        
        # Word overlap
        common_words = s1_words.intersection(s2_words)
        significant_words = [w for w in common_words if len(w) > 3]  # Ignore short words
        
        if significant_words:
            score += min(0.3, len(significant_words) * 0.1)
        
        # Pronoun references
        pronouns = ['this', 'that', 'these', 'those', 'it', 'they', 'he', 'she']
        if any(sentence2.lower().startswith(pronoun) for pronoun in pronouns):
            score += 0.2
        
        # Transition words
        transition_words = ['however', 'therefore', 'furthermore', 'moreover', 'consequently']
        if any(sentence2.lower().startswith(tw) for tw in transition_words):
            score += 0.3
        
        # Similar sentence structure
        if self._have_similar_structure(sentence1, sentence2):
            score += 0.1
        
        return min(1.0, score)
    
    def _identify_connection_type(self, sentence1: str, sentence2: str) -> str:
        """Identify the type of connection between sentences"""
        s2_lower = sentence2.lower()
        
        # Contrast
        if any(word in s2_lower for word in ['however', 'but', 'nevertheless', 'conversely']):
            return 'contrast'
        
        # Addition
        if any(word in s2_lower for word in ['furthermore', 'moreover', 'additionally', 'also']):
            return 'addition'
        
        # Cause/effect
        if any(word in s2_lower for word in ['therefore', 'thus', 'consequently', 'as a result']):
            return 'cause_effect'
        
        # Example
        if any(phrase in s2_lower for phrase in ['for example', 'for instance', 'such as']):
            return 'example'
        
        # Continuation
        if self._assess_sentence_connection(sentence1, sentence2) > 0.6:
            return 'continuation'
        
        return 'weak'
    
    def _have_similar_structure(self, sentence1: str, sentence2: str) -> bool:
        """Check if sentences have similar structure"""
        # Simple structural similarity check
        s1_words = sentence1.split()
        s2_words = sentence2.split()
        
        # Similar length
        if abs(len(s1_words) - len(s2_words)) <= 3:
            return True
        
        # Similar starting pattern
        if len(s1_words) >= 2 and len(s2_words) >= 2:
            if s1_words[0].lower() == s2_words[0].lower():
                return True
        
        return False
    
    def _analyze_paragraph_transitions(self, paragraphs: List[str]) -> Dict[str, Any]:
        """Analyze transitions between paragraphs"""
        transitions = []
        
        for i in range(len(paragraphs) - 1):
            current_para = paragraphs[i].strip()
            next_para = paragraphs[i + 1].strip()
            
            if not current_para or not next_para:
                continue
            
            # Get last sentence of current paragraph
            current_sentences = self._split_into_sentences(current_para)
            last_sentence = current_sentences[-1] if current_sentences else ""
            
            # Get first sentence of next paragraph
            next_sentences = self._split_into_sentences(next_para)
            first_sentence = next_sentences[0] if next_sentences else ""
            
            transition_strength = self._assess_paragraph_transition(
                last_sentence, first_sentence, current_para, next_para
            )
            
            transitions.append({
                'paragraph_index': i,
                'transition_strength': transition_strength,
                'last_sentence': last_sentence[:100] + '...' if len(last_sentence) > 100 else last_sentence,
                'first_sentence': first_sentence[:100] + '...' if len(first_sentence) > 100 else first_sentence,
                'transition_type': self._identify_paragraph_transition_type(first_sentence)
            })
        
        avg_transition_strength = sum(t['transition_strength'] for t in transitions) / len(transitions) if transitions else 0
        
        return {
            'transitions': transitions,
            'average_transition_strength': avg_transition_strength,
            'weak_transitions': [t for t in transitions if t['transition_strength'] < 0.4],
            'strong_transitions': [t for t in transitions if t['transition_strength'] > 0.7]
        }
    
    def _assess_paragraph_transition(self, last_sentence: str, first_sentence: str, 
                                   current_para: str, next_para: str) -> float:
        """Assess transition strength between paragraphs"""
        score = 0.2  # Base score
        
        # Explicit transition words
        transition_words = [
            'however', 'therefore', 'furthermore', 'moreover', 'consequently',
            'nevertheless', 'additionally', 'meanwhile', 'subsequently'
        ]
        
        if any(first_sentence.lower().startswith(tw) for tw in transition_words):
            score += 0.4
        
        # Topic continuity
        last_words = set(last_sentence.lower().split())
        first_words = set(first_sentence.lower().split())
        common_significant = [w for w in last_words.intersection(first_words) if len(w) > 3]
        
        if common_significant:
            score += min(0.3, len(common_significant) * 0.1)
        
        # Pronoun references
        pronouns = ['this', 'that', 'these', 'those']
        if any(first_sentence.lower().startswith(pronoun) for pronoun in pronouns):
            score += 0.2
        
        # Parallel structure
        if self._have_parallel_paragraph_structure(current_para, next_para):
            score += 0.1
        
        return min(1.0, score)
    
    def _identify_paragraph_transition_type(self, first_sentence: str) -> str:
        """Identify type of paragraph transition"""
        first_lower = first_sentence.lower()
        
        if any(word in first_lower for word in ['however', 'nevertheless', 'conversely']):
            return 'contrast'
        elif any(word in first_lower for word in ['furthermore', 'moreover', 'additionally']):
            return 'addition'
        elif any(word in first_lower for word in ['therefore', 'thus', 'consequently']):
            return 'conclusion'
        elif any(word in first_lower for word in ['for example', 'for instance']):
            return 'example'
        elif any(word in first_lower for word in ['meanwhile', 'subsequently', 'then']):
            return 'sequence'
        else:
            return 'implicit'
    
    def _have_parallel_paragraph_structure(self, para1: str, para2: str) -> bool:
        """Check if paragraphs have parallel structure"""
        # Simple parallel structure detection
        p1_sentences = self._split_into_sentences(para1)
        p2_sentences = self._split_into_sentences(para2)
        
        if len(p1_sentences) == len(p2_sentences) and len(p1_sentences) > 1:
            return True
        
        # Similar starting patterns
        if p1_sentences and p2_sentences:
            p1_start = p1_sentences[0].split()[:2]
            p2_start = p2_sentences[0].split()[:2]
            
            if len(p1_start) >= 2 and len(p2_start) >= 2:
                if p1_start[0].lower() == p2_start[0].lower():
                    return True
        
        return False
    
    def _analyze_logical_progression(self, text: str, sentences: List[str]) -> Dict[str, Any]:
        """Analyze logical progression of ideas"""
        # Identify argument structure
        argument_indicators = self._identify_argument_indicators(sentences)
        
        # Analyze idea development
        idea_development = self._analyze_idea_development(text)
        
        # Check for logical gaps
        logical_gaps = self._identify_logical_gaps(sentences)
        
        return {
            'argument_indicators': argument_indicators,
            'idea_development': idea_development,
            'logical_gaps': logical_gaps,
            'progression_score': self._calculate_progression_score(argument_indicators, logical_gaps)
        }
    
    def _identify_argument_indicators(self, sentences: List[str]) -> Dict[str, List[int]]:
        """Identify sentences that indicate argument structure"""
        indicators = {
            'premises': [],
            'conclusions': [],
            'evidence': [],
            'counterarguments': []
        }
        
        for i, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()
            
            # Conclusion indicators
            if any(phrase in sentence_lower for phrase in ['therefore', 'thus', 'in conclusion', 'consequently']):
                indicators['conclusions'].append(i)
            
            # Evidence indicators
            if any(phrase in sentence_lower for phrase in ['research shows', 'studies indicate', 'evidence suggests']):
                indicators['evidence'].append(i)
            
            # Counterargument indicators
            if any(phrase in sentence_lower for phrase in ['however', 'on the other hand', 'critics argue']):
                indicators['counterarguments'].append(i)
            
            # Premise indicators (default for explanatory sentences)
            if not any(i in indicators[key] for key in ['conclusions', 'evidence', 'counterarguments']):
                if any(phrase in sentence_lower for phrase in ['because', 'since', 'given that']):
                    indicators['premises'].append(i)
        
        return indicators
    
    def _analyze_idea_development(self, text: str) -> Dict[str, Any]:
        """Analyze how ideas are developed throughout the text"""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        development_patterns = []
        
        for i, paragraph in enumerate(paragraphs):
            sentences = self._split_into_sentences(paragraph)
            
            if len(sentences) >= 2:
                # Analyze development within paragraph
                topic_sentence = sentences[0]
                supporting_sentences = sentences[1:]
                
                development_type = self._identify_development_type(topic_sentence, supporting_sentences)
                development_strength = self._assess_development_strength(topic_sentence, supporting_sentences)
                
                development_patterns.append({
                    'paragraph_index': i,
                    'development_type': development_type,
                    'development_strength': development_strength,
                    'sentence_count': len(sentences)
                })
        
        return {
            'development_patterns': development_patterns,
            'average_development_strength': sum(p['development_strength'] for p in development_patterns) / len(development_patterns) if development_patterns else 0,
            'development_variety': len(set(p['development_type'] for p in development_patterns))
        }
    
    def _identify_development_type(self, topic_sentence: str, supporting_sentences: List[str]) -> str:
        """Identify how the paragraph develops its main idea"""
        support_text = ' '.join(supporting_sentences).lower()
        
        # Example-based development
        if any(phrase in support_text for phrase in ['for example', 'for instance', 'such as']):
            return 'example'
        
        # Evidence-based development
        if any(phrase in support_text for phrase in ['research', 'study', 'data', 'statistics']):
            return 'evidence'
        
        # Explanation development
        if any(phrase in support_text for phrase in ['because', 'since', 'due to', 'as a result']):
            return 'explanation'
        
        # Comparison development
        if any(phrase in support_text for phrase in ['similarly', 'likewise', 'in contrast', 'however']):
            return 'comparison'
        
        # Process development
        if any(phrase in support_text for phrase in ['first', 'second', 'next', 'then', 'finally']):
            return 'process'
        
        return 'general'
    
    def _assess_development_strength(self, topic_sentence: str, supporting_sentences: List[str]) -> float:
        """Assess how well supporting sentences develop the topic sentence"""
        if not supporting_sentences:
            return 0.0
        
        topic_words = set(topic_sentence.lower().split())
        topic_keywords = [w for w in topic_words if len(w) > 4]  # Focus on substantial words
        
        development_score = 0.3  # Base score
        
        # Check keyword continuity
        for sentence in supporting_sentences:
            sentence_words = set(sentence.lower().split())
            common_keywords = [w for w in topic_keywords if w in sentence_words]
            
            if common_keywords:
                development_score += min(0.2, len(common_keywords) * 0.05)
        
        # Check for elaboration indicators
        elaboration_indicators = ['specifically', 'in particular', 'namely', 'that is']
        support_text = ' '.join(supporting_sentences).lower()
        
        if any(indicator in support_text for indicator in elaboration_indicators):
            development_score += 0.1
        
        # Check sentence count (optimal development)
        if 2 <= len(supporting_sentences) <= 4:
            development_score += 0.1
        elif len(supporting_sentences) > 6:
            development_score -= 0.1  # Too many might indicate lack of focus
        
        return min(1.0, development_score)
    
    def _identify_logical_gaps(self, sentences: List[str]) -> List[Dict[str, Any]]:
        """Identify potential logical gaps in the text"""
        gaps = []
        
        for i in range(len(sentences) - 1):
            current = sentences[i]
            next_sent = sentences[i + 1]
            
            # Check for abrupt topic changes
            if self._has_abrupt_topic_change(current, next_sent):
                gaps.append({
                    'type': 'topic_change',
                    'position': i,
                    'description': 'Abrupt topic change without transition',
                    'current_sentence': current[:100] + '...' if len(current) > 100 else current,
                    'next_sentence': next_sent[:100] + '...' if len(next_sent) > 100 else next_sent
                })
            
            # Check for missing logical connections
            if self._missing_logical_connection(current, next_sent):
                gaps.append({
                    'type': 'missing_connection',
                    'position': i,
                    'description': 'Missing logical connection between ideas',
                    'current_sentence': current[:100] + '...' if len(current) > 100 else current,
                    'next_sentence': next_sent[:100] + '...' if len(next_sent) > 100 else next_sent
                })
        
        return gaps
    
    def _has_abrupt_topic_change(self, sentence1: str, sentence2: str) -> bool:
        """Check if there's an abrupt topic change between sentences"""
        s1_words = set(sentence1.lower().split())
        s2_words = set(sentence2.lower().split())
        
        # Remove common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        s1_content = s1_words - common_words
        s2_content = s2_words - common_words
        
        # Check for significant word overlap
        if len(s1_content) > 0 and len(s2_content) > 0:
            overlap = len(s1_content.intersection(s2_content))
            overlap_ratio = overlap / min(len(s1_content), len(s2_content))
            
            # Low overlap might indicate topic change
            return overlap_ratio < 0.1
        
        return False
    
    def _missing_logical_connection(self, sentence1: str, sentence2: str) -> bool:
        """Check if logical connection is missing between sentences"""
        # If sentences have very different structures and no connecting words
        connection_strength = self._assess_sentence_connection(sentence1, sentence2)
        return connection_strength < 0.2
    
    def _calculate_progression_score(self, argument_indicators: Dict[str, List[int]], 
                                   logical_gaps: List[Dict[str, Any]]) -> float:
        """Calculate overall logical progression score"""
        base_score = 0.7
        
        # Bonus for argument structure
        total_indicators = sum(len(indicators) for indicators in argument_indicators.values())
        if total_indicators > 0:
            base_score += min(0.2, total_indicators * 0.02)
        
        # Penalty for logical gaps
        gap_penalty = min(0.3, len(logical_gaps) * 0.05)
        base_score -= gap_penalty
        
        return max(0.0, min(1.0, base_score))
    
    def _analyze_rhythm_and_pacing(self, sentences: List[str]) -> Dict[str, Any]:
        """Analyze rhythm and pacing of the text"""
        sentence_lengths = [len(sentence.split()) for sentence in sentences]
        
        if not sentence_lengths:
            return {'rhythm_score': 0.0, 'pacing_issues': []}
        
        # Calculate rhythm metrics
        avg_length = sum(sentence_lengths) / len(sentence_lengths)
        length_variance = sum((length - avg_length) ** 2 for length in sentence_lengths) / len(sentence_lengths)
        length_std = length_variance ** 0.5
        
        # Identify pacing issues
        pacing_issues = []
        
        # Check for monotonous rhythm (all sentences similar length)
        if length_std < 3:  # Very low variation
            pacing_issues.append({
                'type': 'monotonous_rhythm',
                'description': 'Sentences have very similar lengths, creating monotonous rhythm'
            })
        
        # Check for extremely long sentences
        very_long = [i for i, length in enumerate(sentence_lengths) if length > avg_length * 2.5]
        if very_long:
            pacing_issues.append({
                'type': 'overly_long_sentences',
                'description': f'Sentences at positions {very_long} are extremely long',
                'positions': very_long
            })
        
        # Check for too many short sentences in a row
        short_runs = self._find_short_sentence_runs(sentence_lengths, avg_length)
        if short_runs:
            pacing_issues.append({
                'type': 'choppy_rhythm',
                'description': 'Multiple short sentences in a row create choppy rhythm',
                'runs': short_runs
            })
        
        # Calculate rhythm score
        rhythm_score = self._calculate_rhythm_score(sentence_lengths, pacing_issues)
        
        return {
            'rhythm_score': rhythm_score,
            'pacing_issues': pacing_issues,
            'average_sentence_length': avg_length,
            'length_variation': length_std,
            'sentence_length_distribution': self._analyze_length_distribution(sentence_lengths)
        }
    
    def _find_short_sentence_runs(self, sentence_lengths: List[int], avg_length: float) -> List[Tuple[int, int]]:
        """Find runs of consecutive short sentences"""
        runs = []
        current_run_start = None
        short_threshold = avg_length * 0.6
        
        for i, length in enumerate(sentence_lengths):
            if length < short_threshold:
                if current_run_start is None:
                    current_run_start = i
            else:
                if current_run_start is not None:
                    run_length = i - current_run_start
                    if run_length >= 3:  # 3 or more short sentences in a row
                        runs.append((current_run_start, i - 1))
                    current_run_start = None
        
        # Check if run continues to end
        if current_run_start is not None:
            run_length = len(sentence_lengths) - current_run_start
            if run_length >= 3:
                runs.append((current_run_start, len(sentence_lengths) - 1))
        
        return runs
    
    def _calculate_rhythm_score(self, sentence_lengths: List[int], 
                              pacing_issues: List[Dict[str, Any]]) -> float:
        """Calculate rhythm quality score"""
        base_score = 0.7
        
        # Penalty for pacing issues
        for issue in pacing_issues:
            if issue['type'] == 'monotonous_rhythm':
                base_score -= 0.2
            elif issue['type'] == 'overly_long_sentences':
                base_score -= 0.15
            elif issue['type'] == 'choppy_rhythm':
                base_score -= 0.1
        
        # Bonus for good variation
        if sentence_lengths:
            avg_length = sum(sentence_lengths) / len(sentence_lengths)
            length_variance = sum((length - avg_length) ** 2 for length in sentence_lengths) / len(sentence_lengths)
            length_std = length_variance ** 0.5
            
            # Optimal variation (not too little, not too much)
            if 4 <= length_std <= 8:
                base_score += 0.1
        
        return max(0.0, min(1.0, base_score))
    
    def _analyze_length_distribution(self, sentence_lengths: List[int]) -> Dict[str, int]:
        """Analyze distribution of sentence lengths"""
        distribution = {
            'very_short': 0,  # < 5 words
            'short': 0,       # 5-10 words
            'medium': 0,      # 11-20 words
            'long': 0,        # 21-30 words
            'very_long': 0    # > 30 words
        }
        
        for length in sentence_lengths:
            if length < 5:
                distribution['very_short'] += 1
            elif length <= 10:
                distribution['short'] += 1
            elif length <= 20:
                distribution['medium'] += 1
            elif length <= 30:
                distribution['long'] += 1
            else:
                distribution['very_long'] += 1
        
        return distribution
    
    def _identify_flow_problems(self, text: str, flow_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify specific flow problems"""
        problems = []
        
        # Weak sentence connections
        sentence_connections = flow_analysis.get('sentence_connections', {})
        weak_connections = sentence_connections.get('weak_connections', [])
        
        if len(weak_connections) > len(sentence_connections.get('connections', [])) * 0.3:
            problems.append({
                'type': 'weak_sentence_connections',
                'severity': 'medium',
                'description': f'{len(weak_connections)} weak connections between sentences',
                'specific_issues': weak_connections[:3]  # Show first 3 examples
            })
        
        # Poor paragraph transitions
        paragraph_transitions = flow_analysis.get('paragraph_transitions', {})
        weak_transitions = paragraph_transitions.get('weak_transitions', [])
        
        if len(weak_transitions) > len(paragraph_transitions.get('transitions', [])) * 0.4:
            problems.append({
                'type': 'poor_paragraph_transitions',
                'severity': 'high',
                'description': f'{len(weak_transitions)} weak transitions between paragraphs',
                'specific_issues': weak_transitions[:3]
            })
        
        # Logical gaps
        logical_progression = flow_analysis.get('logical_progression', {})
        logical_gaps = logical_progression.get('logical_gaps', [])
        
        if logical_gaps:
            problems.append({
                'type': 'logical_gaps',
                'severity': 'high',
                'description': f'{len(logical_gaps)} logical gaps identified',
                'specific_issues': logical_gaps[:3]
            })
        
        # Rhythm problems
        rhythm_analysis = flow_analysis.get('rhythm_analysis', {})
        pacing_issues = rhythm_analysis.get('pacing_issues', [])
        
        if pacing_issues:
            problems.append({
                'type': 'rhythm_problems',
                'severity': 'low',
                'description': f'{len(pacing_issues)} rhythm/pacing issues',
                'specific_issues': pacing_issues
            })
        
        return problems
    
    def _generate_flow_improvements(self, text: str, flow_analysis: Dict[str, Any], 
                                  flow_problems: List[Dict[str, Any]], 
                                  optimization_level: str) -> List[Dict[str, Any]]:
        """Generate specific flow improvement suggestions"""
        improvements = []
        
        for problem in flow_problems:
            if problem['type'] == 'weak_sentence_connections':
                improvements.append({
                    'type': 'add_sentence_transitions',
                    'priority': 'medium',
                    'description': 'Add transition words and phrases between sentences',
                    'specific_actions': [
                        'Use pronouns to refer back to previous sentences',
                        'Add transition words like "however," "furthermore," "therefore"',
                        'Repeat key terms from previous sentences'
                    ]
                })
            
            elif problem['type'] == 'poor_paragraph_transitions':
                improvements.append({
                    'type': 'improve_paragraph_transitions',
                    'priority': 'high',
                    'description': 'Strengthen transitions between paragraphs',
                    'specific_actions': [
                        'Start paragraphs with transition words or phrases',
                        'Use bridge sentences that connect to previous paragraph',
                        'Ensure topic sentences relate to previous content'
                    ]
                })
            
            elif problem['type'] == 'logical_gaps':
                improvements.append({
                    'type': 'fill_logical_gaps',
                    'priority': 'high',
                    'description': 'Add missing logical connections between ideas',
                    'specific_actions': [
                        'Add explanatory sentences to bridge ideas',
                        'Include cause-and-effect relationships',
                        'Provide supporting evidence for claims'
                    ]
                })
            
            elif problem['type'] == 'rhythm_problems':
                improvements.append({
                    'type': 'improve_rhythm',
                    'priority': 'low',
                    'description': 'Vary sentence length and structure for better rhythm',
                    'specific_actions': [
                        'Break up very long sentences',
                        'Combine short, choppy sentences',
                        'Vary sentence beginnings and structures'
                    ]
                })
        
        # Add optimization-level specific improvements
        if optimization_level in ['comprehensive', 'expert']:
            improvements.extend(self._get_advanced_flow_improvements(flow_analysis))
        
        return improvements
    
    def _get_advanced_flow_improvements(self, flow_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get advanced flow improvements for higher optimization levels"""
        advanced_improvements = []
        
        # Narrative arc improvement
        advanced_improvements.append({
            'type': 'optimize_narrative_arc',
            'priority': 'medium',
            'description': 'Optimize overall narrative progression and story arc',
            'specific_actions': [
                'Ensure clear beginning, middle, and end structure',
                'Build tension and release appropriately',
                'Create satisfying resolution of introduced concepts'
            ]
        })
        
        # Coherence enhancement
        advanced_improvements.append({
            'type': 'enhance_coherence',
            'priority': 'medium',
            'description': 'Improve overall text coherence and unity',
            'specific_actions': [
                'Strengthen thematic connections throughout text',
                'Ensure consistent point of view and voice',
                'Create clear relationships between all sections'
            ]
        })
        
        return advanced_improvements
    
    def _optimize_transitions(self, text: str, flow_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimized transitions"""
        paragraph_transitions = flow_analysis.get('paragraph_transitions', {})
        weak_transitions = paragraph_transitions.get('weak_transitions', [])
        
        transition_suggestions = []
        
        for weak_transition in weak_transitions:
            paragraph_index = weak_transition.get('paragraph_index', 0)
            first_sentence = weak_transition.get('first_sentence', '')
            
            # Generate transition suggestions
            suggested_transitions = self._suggest_transitions(first_sentence, paragraph_index)
            
            transition_suggestions.append({
                'paragraph_index': paragraph_index,
                'original_first_sentence': first_sentence,
                'suggested_transitions': suggested_transitions,
                'improvement_type': 'add_transition_word'
            })
        
        return {
            'transition_suggestions': transition_suggestions,
            'total_suggestions': len(transition_suggestions),
            'improvement_potential': len(weak_transitions) / max(1, len(paragraph_transitions.get('transitions', [])))
        }
    
    def _suggest_transitions(self, first_sentence: str, paragraph_index: int) -> List[str]:
        """Suggest appropriate transitions for a sentence"""
        suggestions = []
        
        # Context-based suggestions
        if paragraph_index == 0:
            # First paragraph - no transition needed
            return []
        
        sentence_lower = first_sentence.lower()
        
        # If sentence already has transition, suggest alternatives
        if any(word in sentence_lower for word in ['however', 'therefore', 'furthermore']):
            suggestions.extend([
                'Nevertheless, ' + first_sentence,
                'Consequently, ' + first_sentence,
                'Moreover, ' + first_sentence
            ])
        else:
            # Suggest appropriate transitions based on content
            if any(word in sentence_lower for word in ['different', 'opposite', 'contrast']):
                suggestions.extend([
                    'However, ' + first_sentence,
                    'In contrast, ' + first_sentence,
                    'On the other hand, ' + first_sentence
                ])
            elif any(word in sentence_lower for word in ['result', 'because', 'cause']):
                suggestions.extend([
                    'Therefore, ' + first_sentence,
                    'Consequently, ' + first_sentence,
                    'As a result, ' + first_sentence
                ])
            else:
                suggestions.extend([
                    'Furthermore, ' + first_sentence,
                    'Additionally, ' + first_sentence,
                    'Moreover, ' + first_sentence
                ])
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def _analyze_narrative_progression(self, text: str) -> Dict[str, Any]:
        """Analyze narrative progression and story arc"""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        # Identify narrative elements
        narrative_elements = self._identify_narrative_elements(text)
        
        # Analyze progression patterns
        progression_patterns = self._analyze_progression_patterns(paragraphs)
        
        # Assess narrative arc
        narrative_arc = self._assess_narrative_arc(paragraphs, narrative_elements)
        
        return {
            'narrative_elements': narrative_elements,
            'progression_patterns': progression_patterns,
            'narrative_arc': narrative_arc,
            'progression_score': self._calculate_narrative_progression_score(narrative_elements, narrative_arc)
        }
    
    def _identify_narrative_elements(self, text: str) -> Dict[str, List[int]]:
        """Identify narrative elements in the text"""
        elements = {
            'setup': [],
            'conflict': [],
            'development': [],
            'climax': [],
            'resolution': []
        }
        
        sentences = self._split_into_sentences(text)
        
        for i, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()
            
            # Setup indicators
            if any(phrase in sentence_lower for phrase in ['begin', 'start', 'introduce', 'first']):
                elements['setup'].append(i)
            
            # Conflict indicators
            if any(phrase in sentence_lower for phrase in ['problem', 'challenge', 'difficulty', 'issue']):
                elements['conflict'].append(i)
            
            # Development indicators
            if any(phrase in sentence_lower for phrase in ['develop', 'progress', 'continue', 'further']):
                elements['development'].append(i)
            
            # Climax indicators
            if any(phrase in sentence_lower for phrase in ['crucial', 'critical', 'key moment', 'turning point']):
                elements['climax'].append(i)
            
            # Resolution indicators
            if any(phrase in sentence_lower for phrase in ['conclude', 'resolve', 'solution', 'final']):
                elements['resolution'].append(i)
        
        return elements
    
    def _analyze_progression_patterns(self, paragraphs: List[str]) -> List[Dict[str, Any]]:
        """Analyze progression patterns in paragraphs"""
        patterns = []
        
        for i, paragraph in enumerate(paragraphs):
            sentences = self._split_into_sentences(paragraph)
            
            if len(sentences) >= 2:
                pattern_type = self._identify_progression_pattern(sentences)
                pattern_strength = self._assess_progression_strength(sentences)
                
                patterns.append({
                    'paragraph_index': i,
                    'pattern_type': pattern_type,
                    'pattern_strength': pattern_strength,
                    'sentence_count': len(sentences)
                })
        
        return patterns
    
    def _identify_progression_pattern(self, sentences: List[str]) -> str:
        """Identify the progression pattern within a paragraph"""
        if len(sentences) < 2:
            return 'single'
        
        combined_text = ' '.join(sentences).lower()
        
        # Chronological progression
        if any(word in combined_text for word in ['first', 'then', 'next', 'finally', 'after']):
            return 'chronological'
        
        # Logical progression
        if any(word in combined_text for word in ['because', 'therefore', 'since', 'thus']):
            return 'logical'
        
        # Spatial progression
        if any(word in combined_text for word in ['above', 'below', 'beside', 'near', 'far']):
            return 'spatial'
        
        # Importance progression
        if any(word in combined_text for word in ['important', 'significant', 'crucial', 'key']):
            return 'importance'
        
        # Comparison progression
        if any(word in combined_text for word in ['similar', 'different', 'compare', 'contrast']):
            return 'comparison'
        
        return 'general'
    
    def _assess_progression_strength(self, sentences: List[str]) -> float:
        """Assess strength of progression within paragraph"""
        if len(sentences) < 2:
            return 0.5
        
        total_strength = 0
        connections = 0
        
        for i in range(len(sentences) - 1):
            connection_strength = self._assess_sentence_connection(sentences[i], sentences[i + 1])
            total_strength += connection_strength
            connections += 1
        
        return total_strength / connections if connections > 0 else 0.5
    
    def _assess_narrative_arc(self, paragraphs: List[str], 
                            narrative_elements: Dict[str, List[int]]) -> Dict[str, Any]:
        """Assess overall narrative arc"""
        total_paragraphs = len(paragraphs)
        
        if total_paragraphs == 0:
            return {'arc_quality': 'none', 'arc_score': 0.0}
        
        # Check for presence of narrative elements
        has_setup = len(narrative_elements['setup']) > 0
        has_conflict = len(narrative_elements['conflict']) > 0
        has_development = len(narrative_elements['development']) > 0
        has_resolution = len(narrative_elements['resolution']) > 0
        
        # Assess arc completeness
        arc_elements = sum([has_setup, has_conflict, has_development, has_resolution])
        
        # Assess arc positioning (elements should appear in roughly correct order)
        arc_positioning = self._assess_arc_positioning(narrative_elements, total_paragraphs)
        
        arc_score = (arc_elements / 4) * 0.6 + arc_positioning * 0.4
        
        if arc_score >= 0.8:
            arc_quality = 'excellent'
        elif arc_score >= 0.6:
            arc_quality = 'good'
        elif arc_score >= 0.4:
            arc_quality = 'fair'
        else:
            arc_quality = 'weak'
        
        return {
            'arc_quality': arc_quality,
            'arc_score': arc_score,
            'has_setup': has_setup,
            'has_conflict': has_conflict,
            'has_development': has_development,
            'has_resolution': has_resolution,
            'arc_positioning': arc_positioning
        }
    
    def _assess_arc_positioning(self, narrative_elements: Dict[str, List[int]], 
                              total_sentences: int) -> float:
        """Assess whether narrative elements appear in appropriate positions"""
        if total_sentences == 0:
            return 0.0
        
        positioning_score = 0.0
        checks = 0
        
        # Setup should be early
        if narrative_elements['setup']:
            avg_setup_position = sum(narrative_elements['setup']) / len(narrative_elements['setup'])
            relative_position = avg_setup_position / total_sentences
            if relative_position <= 0.3:  # First 30%
                positioning_score += 1.0
            elif relative_position <= 0.5:  # First 50%
                positioning_score += 0.5
            checks += 1
        
        # Resolution should be late
        if narrative_elements['resolution']:
            avg_resolution_position = sum(narrative_elements['resolution']) / len(narrative_elements['resolution'])
            relative_position = avg_resolution_position / total_sentences
            if relative_position >= 0.7:  # Last 30%
                positioning_score += 1.0
            elif relative_position >= 0.5:  # Last 50%
                positioning_score += 0.5
            checks += 1
        
        # Development should be in middle
        if narrative_elements['development']:
            avg_dev_position = sum(narrative_elements['development']) / len(narrative_elements['development'])
            relative_position = avg_dev_position / total_sentences
            if 0.3 <= relative_position <= 0.7:  # Middle 40%
                positioning_score += 1.0
            elif 0.2 <= relative_position <= 0.8:  # Middle 60%
                positioning_score += 0.5
            checks += 1
        
        return positioning_score / checks if checks > 0 else 0.5
    
    def _calculate_narrative_progression_score(self, narrative_elements: Dict[str, List[int]], 
                                             narrative_arc: Dict[str, Any]) -> float:
        """Calculate overall narrative progression score"""
        base_score = 0.5
        
        # Bonus for narrative elements
        element_count = sum(len(elements) for elements in narrative_elements.values())
        if element_count > 0:
            base_score += min(0.3, element_count * 0.02)
        
        # Bonus for good arc
        arc_score = narrative_arc.get('arc_score', 0.5)
        base_score += (arc_score - 0.5) * 0.4
        
        return min(1.0, max(0.0, base_score))
    
    def _calculate_flow_score(self, flow_analysis: Dict[str, Any], 
                            flow_problems: List[Dict[str, Any]]) -> float:
        """Calculate overall flow quality score"""
        base_score = 0.7
        
        # Adjust based on connection strengths
        sentence_connections = flow_analysis.get('sentence_connections', {})
        avg_connection = sentence_connections.get('average_connection_strength', 0.5)
        base_score += (avg_connection - 0.5) * 0.2
        
        paragraph_transitions = flow_analysis.get('paragraph_transitions', {})
        avg_transition = paragraph_transitions.get('average_transition_strength', 0.5)
        base_score += (avg_transition - 0.5) * 0.2
        
        # Adjust based on logical progression
        logical_progression = flow_analysis.get('logical_progression', {})
        progression_score = logical_progression.get('progression_score', 0.5)
        base_score += (progression_score - 0.5) * 0.2
        
        # Adjust based on rhythm
        rhythm_analysis = flow_analysis.get('rhythm_analysis', {})
        rhythm_score = rhythm_analysis.get('rhythm_score', 0.5)
        base_score += (rhythm_score - 0.5) * 0.1
        
        # Penalty for flow problems
        for problem in flow_problems:
            severity = problem.get('severity', 'medium')
            if severity == 'high':
                base_score -= 0.15
            elif severity == 'medium':
                base_score -= 0.1
            else:  # low
                base_score -= 0.05
        
        return round(max(0.0, min(1.0, base_score)), 2)
    
    def _prioritize_flow_improvements(self, flow_problems: List[Dict[str, Any]]) -> List[str]:
        """Prioritize flow improvements by importance"""
        high_priority = [p['type'] for p in flow_problems if p.get('severity') == 'high']
        medium_priority = [p['type'] for p in flow_problems if p.get('severity') == 'medium']
        low_priority = [p['type'] for p in flow_problems if p.get('severity') == 'low']
        
        # Remove duplicates while preserving order
        all_priorities = []
        for priority_list in [high_priority, medium_priority, low_priority]:
            for item in priority_list:
                if item not in all_priorities:
                    all_priorities.append(item)
        
        return all_priorities


class StructureArchitectAgent(BaseWritingAgent):
    """Structure Architect Agent for document organization and flow optimization"""
    
    def __init__(self, ai_provider_service: AIProviderService):
        super().__init__(
            agent_id="structure_architect",
            name="Structure Architect",
            ai_provider_service=ai_provider_service
        )
        
        # Initialize CrewAI agent
        self.crew_agent = Agent(
            role="Expert Document Structure Architect and Flow Optimization Specialist",
            goal="Optimize document organization, structure, and narrative flow for maximum clarity and impact",
            backstory=STRUCTURE_ARCHITECT_PROMPTS["backstory"],
            verbose=True,
            allow_delegation=False,
            tools=[DocumentStructureTool(), FlowOptimizationTool()],
            llm=ai_provider_service.get_primary_llm(),
            max_iter=3,
            memory=True
        )
        
        # Specializations
        self.specializations = [
            "Document structure analysis",
            "Hierarchical organization",
            "Flow optimization",
            "Narrative progression",
            "Paragraph structure",
            "Transition enhancement",
            "Logical coherence",
            "Content architecture"
        ]
        
        # Structure expertise levels
        self.structure_expertise = {
            'document_organization': 0.92,
            'hierarchical_structure': 0.90,
            'flow_optimization': 0.88,
            'paragraph_structure': 0.85,
            'transition_enhancement': 0.87,
            'logical_coherence': 0.89,
            'narrative_progression': 0.83,
            'content_architecture': 0.91
        }
        
        # Supported document types
        self.document_types = [
            'academic', 'business', 'creative', 'technical', 'journalistic',
            'legal', 'medical', 'educational', 'marketing', 'general'
        ]
        
        # Optimization levels
        self.optimization_levels = ['basic', 'standard', 'comprehensive', 'expert']
        
        logger.info("Structure Architect Agent initialized", specializations=len(self.specializations))
    
    async def execute_task(self, task_request: TaskRequest) -> TaskResponse:
        """Execute structure analysis and optimization task"""
        try:
            self._start_timing()
            logger.info("Executing structure optimization task", task_id=task_request.task_id)
            
            # Analyze structure requirements
            structure_analysis = await self._analyze_structure_requirements(task_request)
            
            # Perform document structure analysis
            document_analysis = await self._analyze_document_structure(task_request, structure_analysis)
            
            # Optimize flow and transitions
            flow_optimization = await self._optimize_document_flow(task_request, structure_analysis)
            
            # Generate structure improvements
            structure_improvements = await self._generate_structure_improvements(
                task_request, document_analysis, flow_optimization, structure_analysis
            )
            
            # Create optimized structure
            optimized_content = await self._create_optimized_structure(
                task_request.content, structure_improvements, structure_analysis
            )
            
            # Create response
            response = TaskResponse(
                task_id=task_request.task_id,
                agent_id=self.agent_id,
                status="completed",
                content=optimized_content,
                metadata={
                    "document_type": structure_analysis.get("document_type"),
                    "optimization_level": structure_analysis.get("optimization_level"),
                    "structural_coherence_score": document_analysis.get("coherence_score", 0.8),
                    "flow_score": flow_optimization.get("flow_score", 0.8),
                    "improvements_applied": len(structure_improvements.get("applied_improvements", [])),
                    "structure_quality": document_analysis.get("structure_quality", "good"),
                    "optimization_summary": structure_improvements.get("optimization_summary", "")
                },
                confidence_score=self._calculate_structure_confidence(
                    document_analysis, flow_optimization, structure_improvements
                ),
                processing_time=self._get_processing_time()
            )
            
            await self._update_performance_metrics(response)
            
            logger.info(
                "Structure optimization task completed",
                task_id=task_request.task_id,
                coherence_score=document_analysis.get("coherence_score", 0.8),
                flow_score=flow_optimization.get("flow_score", 0.8),
                confidence=response.confidence_score
            )
            
            return response
            
        except Exception as e:
            logger.error("Structure optimization task failed", task_id=task_request.task_id, error=str(e))
            return self._create_error_response(task_request, str(e))
    
    async def _analyze_structure_requirements(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Analyze structure optimization requirements"""
        try:
            # Determine document type
            document_type = self._determine_document_type(task_request.content, task_request.context)
            
            # Determine optimization level
            optimization_level = self._determine_optimization_level(task_request.user_preferences)
            
            # Identify structure priorities
            priorities = self._determine_structure_priorities(task_request.content, task_request.task_type)
            
            # Check for specific requirements
            requirements = self._identify_structure_requirements(task_request.content, task_request.context)
            
            return {
                "document_type": document_type,
                "optimization_level": optimization_level,
                "priorities": priorities,
                "requirements": requirements,
                "preserve_content": self._should_preserve_content(task_request.user_preferences),
                "target_audience": self._determine_target_audience(task_request.context, task_request.user_preferences)
            }
            
        except Exception as e:
            logger.error("Structure requirements analysis failed", error=str(e))
            return {
                "document_type": "general",
                "optimization_level": "standard",
                "priorities": ["organization", "flow", "coherence"],
                "requirements": []
            }
    
    def _determine_document_type(self, content: str, context: Optional[str]) -> str:
        """Determine the type of document for appropriate structuring"""
        combined_text = f"{content} {context or ''}".lower()
        
        # Academic indicators
        if any(word in combined_text for word in ['research', 'study', 'hypothesis', 'methodology', 'bibliography']):
            return 'academic'
        
        # Business indicators
        if any(word in combined_text for word in ['business', 'proposal', 'executive', 'strategy', 'revenue']):
            return 'business'
        
        # Creative indicators
        if any(word in combined_text for word in ['story', 'character', 'plot', 'narrative', 'fiction']):
            return 'creative'
        
        # Technical indicators
        if any(word in combined_text for word in ['technical', 'specification', 'implementation', 'system', 'algorithm']):
            return 'technical'
        
        # Legal indicators
        if any(word in combined_text for word in ['legal', 'contract', 'agreement', 'clause', 'liability']):
            return 'legal'
        
        # Medical indicators
        if any(word in combined_text for word in ['medical', 'patient', 'diagnosis', 'treatment', 'clinical']):
            return 'medical'
        
        return 'general'
    
    def _determine_optimization_level(self, user_preferences: Optional[Dict[str, Any]]) -> str:
        """Determine optimization level based on user preferences"""
        if user_preferences and 'optimization_level' in user_preferences:
            return user_preferences['optimization_level']
        
        return 'standard'
    
    def _determine_structure_priorities(self, content: str, task_type: str) -> List[str]:
        """Determine structure optimization priorities"""
        priorities = ['organization']  # Always include organization
        
        content_lower = content.lower()
        
        # Add priorities based on content characteristics
        if any(word in content_lower for word in ['flow', 'transition', 'connect']):
            priorities.append('flow')
        
        if any(word in content_lower for word in ['structure', 'organize', 'arrange']):
            priorities.append('hierarchy')
        
        if any(word in content_lower for word in ['coherent', 'logical', 'clear']):
            priorities.append('coherence')
        
        # Add priorities based on task type
        if task_type in ['restructure', 'organize', 'outline']:
            priorities.extend(['hierarchy', 'organization'])
        elif task_type in ['improve_flow', 'optimize', 'enhance']:
            priorities.extend(['flow', 'transitions'])
        
        return list(set(priorities))  # Remove duplicates
    
    def _identify_structure_requirements(self, content: str, context: Optional[str]) -> List[str]:
        """Identify specific structure requirements"""
        requirements = []
        combined_text = f"{content} {context or ''}".lower()
        
        if 'heading' in combined_text:
            requirements.append('add_headings')
        
        if 'introduction' in combined_text:
            requirements.append('clear_introduction')
        
        if 'conclusion' in combined_text:
            requirements.append('strong_conclusion')
        
        if any(word in combined_text for word in ['section', 'chapter', 'part']):
            requirements.append('section_organization')
        
        return requirements
    
    def _should_preserve_content(self, user_preferences: Optional[Dict[str, Any]]) -> bool:
        """Determine if content should be preserved during restructuring"""
        if user_preferences and 'preserve_content' in user_preferences:
            return user_preferences['preserve_content']
        
        return True  # Default to preserving content
    
    def _determine_target_audience(self, context: Optional[str], user_preferences: Optional[Dict[str, Any]]) -> str:
        """Determine target audience for structure optimization"""
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
    
    async def _analyze_document_structure(self, task_request: TaskRequest, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze document structure comprehensively"""
        try:
            structure_task = Task(
                description=f"""
                Analyze the structure and organization of the following document:
                
                Document: {task_request.content}
                Document Type: {analysis['document_type']}
                Target Audience: {analysis['target_audience']}
                Priorities: {', '.join(analysis['priorities'])}
                
                Analyze:
                1. Overall document structure and organization
                2. Heading hierarchy and section organization
                3. Paragraph structure and development
                4. Logical flow and coherence
                5. Introduction and conclusion effectiveness
                6. Structural issues and improvement opportunities
                
                Provide detailed analysis with specific recommendations for structural improvements.
                Rate the overall structural quality and identify priority areas for optimization.
                """,
                agent=self.crew_agent,
                expected_output="Comprehensive structural analysis with specific improvement recommendations"
            )
            
            crew = Crew(
                agents=[self.crew_agent],
                tasks=[structure_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Also use document structure tool
            structure_tool = DocumentStructureTool()
            tool_results = structure_tool._run(task_request.content, analysis['document_type'])
            
            return {
                'ai_analysis': str(result),
                'tool_results': tool_results,
                'coherence_score': tool_results.get('coherence_score', 0.8),
                'structure_quality': tool_results.get('structure_quality', 'good'),
                'structural_issues': tool_results.get('structural_issues', []),
                'structure_recommendations': tool_results.get('structure_recommendations', []),
                'current_structure': tool_results.get('current_structure', {}),
                'hierarchy_analysis': tool_results.get('hierarchy_analysis', {})
            }
            
        except Exception as e:
            logger.error("Document structure analysis failed", error=str(e))
            return {
                'error': str(e),
                'coherence_score': 0.5,
                'structure_quality': 'needs_improvement',
                'structural_issues': [],
                'structure_recommendations': []
            }
    
    async def _optimize_document_flow(self, task_request: TaskRequest, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize document flow and transitions"""
        try:
            flow_task = Task(
                description=f"""
                Optimize the flow and narrative progression of the following document:
                
                Document: {task_request.content}
                Document Type: {analysis['document_type']}
                Optimization Level: {analysis['optimization_level']}
                
                Optimize:
                1. Sentence connections and transitions
                2. Paragraph transitions and flow
                3. Logical progression of ideas
                4. Narrative arc and story development
                5. Rhythm and pacing
                6. Overall coherence and unity
                
                Provide specific recommendations for improving flow and transitions.
                Identify areas where logical connections are weak or missing.
                """,
                agent=self.crew_agent,
                expected_output="Detailed flow optimization analysis with specific improvement recommendations"
            )
            
            crew = Crew(
                agents=[self.crew_agent],
                tasks=[flow_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Also use flow optimization tool
            flow_tool = FlowOptimizationTool()
            tool_results = flow_tool._run(task_request.content, analysis['optimization_level'])
            
            return {
                'ai_analysis': str(result),
                'tool_results': tool_results,
                'flow_score': tool_results.get('flow_score', 0.8),
                'flow_problems': tool_results.get('flow_problems', []),
                'flow_improvements': tool_results.get('flow_improvements', []),
                'transition_optimization': tool_results.get('transition_optimization', {}),
                'narrative_analysis': tool_results.get('narrative_analysis', {})
            }
            
        except Exception as e:
            logger.error("Flow optimization failed", error=str(e))
            return {
                'error': str(e),
                'flow_score': 0.5,
                'flow_problems': [],
                'flow_improvements': []
            }
    
    async def _generate_structure_improvements(self, task_request: TaskRequest, 
                                             document_analysis: Dict[str, Any], 
                                             flow_optimization: Dict[str, Any], 
                                             analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive structure improvements"""
        try:
            improvement_task = Task(
                description=f"""
                Generate comprehensive structure improvements for the following document:
                
                Original Document: {task_request.content}
                
                Structure Analysis: {document_analysis.get('ai_analysis', 'No analysis available')}
                Flow Analysis: {flow_optimization.get('ai_analysis', 'No analysis available')}
                
                Structural Issues: {len(document_analysis.get('structural_issues', []))}
                Flow Problems: {len(flow_optimization.get('flow_problems', []))}
                
                Optimization Priorities: {', '.join(analysis['priorities'])}
                Document Type: {analysis['document_type']}
                Preserve Content: {analysis['preserve_content']}
                
                Generate improvements that:
                1. Optimize document organization and hierarchy
                2. Improve flow and transitions between sections
                3. Enhance logical coherence and progression
                4. Strengthen paragraph structure and development
                5. Address identified structural issues
                6. Maintain content integrity while improving structure
                
                Provide the restructured document with clear explanations for major changes.
                """,
                agent=self.crew_agent,
                expected_output="Restructured document with explanations for structural improvements"
            )
            
            crew = Crew(
                agents=[self.crew_agent],
                tasks=[improvement_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Compile improvements from tools
            structure_recommendations = document_analysis.get('structure_recommendations', [])
            flow_improvements = flow_optimization.get('flow_improvements', [])
            
            return {
                'ai_improvements': str(result),
                'structure_recommendations': structure_recommendations,
                'flow_improvements': flow_improvements,
                'applied_improvements': self._compile_applied_improvements(structure_recommendations, flow_improvements),
                'optimization_summary': self._generate_optimization_summary(structure_recommendations, flow_improvements)
            }
            
        except Exception as e:
            logger.error("Structure improvement generation failed", error=str(e))
            return {
                'error': str(e),
                'ai_improvements': 'Error generating improvements',
                'applied_improvements': [],
                'optimization_summary': 'Error generating optimization summary'
            }
    
    def _compile_applied_improvements(self, structure_recommendations: List[Dict[str, Any]], 
                                    flow_improvements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Compile list of applied improvements"""
        applied = []
        
        # Add high-priority structure recommendations
        for recommendation in structure_recommendations:
            if recommendation.get('priority') == 'high':
                applied.append({
                    'type': 'structure',
                    'description': recommendation.get('description', ''),
                    'priority': recommendation.get('priority', 'medium')
                })
        
        # Add high-priority flow improvements
        for improvement in flow_improvements:
            if improvement.get('priority') == 'high':
                applied.append({
                    'type': 'flow',
                    'description': improvement.get('description', ''),
                    'priority': improvement.get('priority', 'medium')
                })
        
        return applied
    
    def _generate_optimization_summary(self, structure_recommendations: List[Dict[str, Any]], 
                                     flow_improvements: List[Dict[str, Any]]) -> str:
        """Generate summary of optimizations made"""
        improvements = []
        
        structure_count = len([r for r in structure_recommendations if r.get('priority') == 'high'])
        if structure_count > 0:
            improvements.append(f"applied {structure_count} structural improvements")
        
        flow_count = len([i for i in flow_improvements if i.get('priority') == 'high'])
        if flow_count > 0:
            improvements.append(f"implemented {flow_count} flow optimizations")
        
        if not improvements:
            return "Document structure reviewed with minimal optimizations needed"
        
        if len(improvements) == 1:
            return f"Optimization summary: {improvements[0]}"
        else:
            return f"Optimization summary: {', '.join(improvements[:-1])}, and {improvements[-1]}"
    
    async def _create_optimized_structure(self, content: str, improvements: Dict[str, Any], 
                                        analysis: Dict[str, Any]) -> str:
        """Create optimized document structure"""
        try:
            optimization_task = Task(
                description=f"""
                Create an optimized version of the document with improved structure:
                
                Original Document: {content}
                
                AI Improvements: {improvements.get('ai_improvements', '')}
                Structure Recommendations: {len(improvements.get('structure_recommendations', []))} recommendations
                Flow Improvements: {len(improvements.get('flow_improvements', []))} improvements
                
                Optimization Guidelines:
                - Document type: {analysis['document_type']}
                - Preserve content: {analysis['preserve_content']}
                - Target audience: {analysis['target_audience']}
                - Optimization level: {analysis['optimization_level']}
                
                Apply optimizations while:
                1. Maintaining original meaning and content
                2. Improving document organization and hierarchy
                3. Enhancing flow and transitions
                4. Strengthening logical coherence
                5. Optimizing for target audience
                6. Following document type conventions
                
                Return the optimized document with improved structure and flow.
                """,
                agent=self.crew_agent,
                expected_output="Optimized document with improved structure and flow"
            )
            
            crew = Crew(
                agents=[self.crew_agent],
                tasks=[optimization_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            return str(result) if str(result).strip() else content
            
        except Exception as e:
            logger.error("Structure optimization application failed", error=str(e))
            return content  # Return original if optimization fails
    
    def _calculate_structure_confidence(self, document_analysis: Dict[str, Any], 
                                      flow_optimization: Dict[str, Any], 
                                      improvements: Dict[str, Any]) -> float:
        """Calculate confidence score for structure optimization"""
        try:
            base_confidence = 0.88
            
            # Adjust based on structural analysis quality
            coherence_score = document_analysis.get('coherence_score', 0.8)
            structure_adjustment = (coherence_score - 0.5) * 0.2
            
            # Adjust based on flow optimization quality
            flow_score = flow_optimization.get('flow_score', 0.8)
            flow_adjustment = (flow_score - 0.5) * 0.15
            
            # Adjust based on number of issues addressed
            structural_issues = len(document_analysis.get('structural_issues', []))
            flow_problems = len(flow_optimization.get('flow_problems', []))
            total_issues = structural_issues + flow_problems
            
            if total_issues == 0:
                issue_adjustment = 0.05  # Slight boost if no issues found
            else:
                applied_improvements = len(improvements.get('applied_improvements', []))
                resolution_rate = applied_improvements / total_issues if total_issues > 0 else 0
                issue_adjustment = (resolution_rate - 0.5) * 0.1
            
            final_confidence = base_confidence + structure_adjustment + flow_adjustment + issue_adjustment
            return round(min(max(final_confidence, 0.1), 1.0), 2)
            
        except Exception:
            return 0.88
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get structure architect capabilities"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "specializations": self.specializations,
            "structure_types": list(self.structure_expertise.keys()),
            "expertise_levels": self.structure_expertise,
            "supported_tasks": ["restructure", "organize", "optimize_flow", "improve_structure", "analyze_structure"],
            "document_types": self.document_types,
            "optimization_levels": self.optimization_levels,
            "structure_elements": [
                "headings", "paragraphs", "sections", "transitions", 
                "flow", "coherence", "hierarchy", "organization"
            ],
            "improvement_types": [
                "add_headings", "improve_transitions", "optimize_flow",
                "strengthen_paragraphs", "enhance_coherence", "reorganize_content"
            ],
            "content_preservation": True,
            "audience_adaptation": True,
            "narrative_optimization": True,
            "languages": ["English"],
            "collaboration_ready": True,
            "max_document_length": 20000  # words
        }

