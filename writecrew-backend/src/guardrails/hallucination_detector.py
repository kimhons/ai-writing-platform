"""
Hallucination Detection System
Advanced AI content verification and fact-checking to prevent misinformation
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import re
import json
import hashlib

from ..services.ai_provider_service import AIProviderService
from ..config.settings import settings

logger = logging.getLogger(__name__)

class VerificationLevel(Enum):
    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"
    CRITICAL = "critical"

class FactCheckResult(Enum):
    VERIFIED = "verified"
    DISPUTED = "disputed"
    UNVERIFIABLE = "unverifiable"
    FALSE = "false"
    NEEDS_REVIEW = "needs_review"

@dataclass
class Claim:
    """Individual factual claim extracted from content"""
    id: str
    text: str
    category: str  # date, statistic, quote, fact, etc.
    confidence: float
    context: str
    source_sentence: str
    position: Tuple[int, int]  # start, end character positions

@dataclass
class VerificationResult:
    """Result of fact-checking a claim"""
    claim_id: str
    result: FactCheckResult
    confidence: float
    sources: List[str] = field(default_factory=list)
    explanation: str = ""
    suggested_correction: Optional[str] = None
    verification_time: float = 0.0

@dataclass
class HallucinationReport:
    """Comprehensive hallucination detection report"""
    content_id: str
    verification_level: VerificationLevel
    total_claims: int
    verified_claims: int
    disputed_claims: int
    false_claims: int
    unverifiable_claims: int
    overall_confidence: float
    risk_score: float
    claims: List[Claim] = field(default_factory=list)
    verification_results: List[VerificationResult] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)

class HallucinationDetector:
    """
    Advanced hallucination detection system that identifies and verifies
    factual claims in AI-generated content
    """
    
    def __init__(self, ai_provider_service: AIProviderService):
        self.ai_provider_service = ai_provider_service
        self.verification_cache = {}  # Cache for repeated claims
        self.performance_metrics = {
            'total_verifications': 0,
            'cache_hits': 0,
            'average_processing_time': 0.0,
            'accuracy_rate': 0.0
        }
        
        # Claim extraction patterns
        self.claim_patterns = {
            'statistics': [
                r'\b\d+(?:\.\d+)?%\b',  # Percentages
                r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\s+(?:million|billion|trillion)\b',  # Large numbers
                r'\b\d+(?:\.\d+)?\s+(?:times|fold)\b',  # Multipliers
                r'\b(?:increased|decreased|rose|fell)\s+by\s+\d+(?:\.\d+)?%?\b'  # Changes
            ],
            'dates': [
                r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
                r'\b\d{1,2}/\d{1,2}/\d{4}\b',
                r'\b\d{4}-\d{2}-\d{2}\b',
                r'\bin\s+\d{4}\b'
            ],
            'quotes': [
                r'"[^"]{20,200}"',  # Direct quotes
                r'said\s+"[^"]+"',  # Attributed quotes
                r'according\s+to\s+[^,]+,\s+"[^"]+"'  # Source quotes
            ],
            'facts': [
                r'\b(?:is|was|are|were)\s+(?:the\s+)?(?:first|last|only|largest|smallest|highest|lowest)\b',
                r'\b(?:founded|established|created|invented)\s+in\s+\d{4}\b',
                r'\b(?:located|situated)\s+in\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
            ]
        }
    
    async def detect_hallucinations(self, content: str, 
                                  verification_level: VerificationLevel = VerificationLevel.STANDARD,
                                  content_type: str = "general") -> HallucinationReport:
        """
        Comprehensive hallucination detection and fact-checking
        """
        start_time = datetime.utcnow()
        content_id = hashlib.md5(content.encode()).hexdigest()[:12]
        
        try:
            logger.info(f"Starting hallucination detection for content {content_id}")
            
            # Step 1: Extract factual claims
            claims = await self._extract_claims(content, content_type)
            logger.info(f"Extracted {len(claims)} claims from content")
            
            # Step 2: Verify claims based on verification level
            verification_results = await self._verify_claims(claims, verification_level)
            
            # Step 3: Generate comprehensive report
            report = self._generate_report(
                content_id, claims, verification_results, 
                verification_level, start_time
            )
            
            # Step 4: Update performance metrics
            self._update_metrics(report)
            
            logger.info(f"Hallucination detection completed for {content_id}")
            return report
            
        except Exception as e:
            logger.error(f"Error in hallucination detection: {str(e)}")
            raise
    
    async def _extract_claims(self, content: str, content_type: str) -> List[Claim]:
        """Extract factual claims from content using AI and pattern matching"""
        claims = []
        claim_counter = 1
        
        # AI-powered claim extraction
        ai_claims = await self._extract_claims_ai(content, content_type)
        
        # Pattern-based claim extraction
        pattern_claims = self._extract_claims_patterns(content)
        
        # Combine and deduplicate claims
        all_claims = ai_claims + pattern_claims
        unique_claims = self._deduplicate_claims(all_claims)
        
        return unique_claims[:50]  # Limit to 50 claims for performance
    
    async def _extract_claims_ai(self, content: str, content_type: str) -> List[Claim]:
        """Use AI to extract factual claims"""
        try:
            prompt = f"""
            Analyze the following {content_type} content and extract all factual claims that can be verified.
            Focus on:
            1. Statistical data and numbers
            2. Historical facts and dates
            3. Direct quotes and attributions
            4. Scientific or technical claims
            5. Geographic or demographic information
            
            For each claim, provide:
            - The exact text of the claim
            - The category (statistic, date, quote, fact, etc.)
            - The surrounding context
            - A confidence score (0.0-1.0) for how verifiable it appears
            
            Content:
            {content[:2000]}  # Limit content length for AI processing
            
            Return the results as a JSON array with the following structure:
            [
                {{
                    "text": "exact claim text",
                    "category": "category name",
                    "context": "surrounding context",
                    "confidence": 0.8,
                    "source_sentence": "full sentence containing the claim"
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
            claims_data = json.loads(response.get('content', '[]'))
            claims = []
            
            for i, claim_data in enumerate(claims_data[:20]):  # Limit AI claims
                # Find claim position in content
                claim_text = claim_data.get('text', '')
                start_pos = content.find(claim_text)
                end_pos = start_pos + len(claim_text) if start_pos != -1 else 0
                
                claim = Claim(
                    id=f"ai_claim_{i+1}",
                    text=claim_text,
                    category=claim_data.get('category', 'unknown'),
                    confidence=float(claim_data.get('confidence', 0.5)),
                    context=claim_data.get('context', ''),
                    source_sentence=claim_data.get('source_sentence', ''),
                    position=(start_pos, end_pos)
                )
                claims.append(claim)
            
            return claims
            
        except Exception as e:
            logger.error(f"Error in AI claim extraction: {str(e)}")
            return []
    
    def _extract_claims_patterns(self, content: str) -> List[Claim]:
        """Extract claims using regex patterns"""
        claims = []
        claim_counter = 1
        
        for category, patterns in self.claim_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                
                for match in matches:
                    # Get surrounding context
                    start = max(0, match.start() - 100)
                    end = min(len(content), match.end() + 100)
                    context = content[start:end]
                    
                    # Get source sentence
                    sentence_start = content.rfind('.', 0, match.start()) + 1
                    sentence_end = content.find('.', match.end())
                    if sentence_end == -1:
                        sentence_end = len(content)
                    source_sentence = content[sentence_start:sentence_end].strip()
                    
                    claim = Claim(
                        id=f"pattern_claim_{claim_counter}",
                        text=match.group(),
                        category=category,
                        confidence=0.7,  # Pattern-based claims have moderate confidence
                        context=context,
                        source_sentence=source_sentence,
                        position=(match.start(), match.end())
                    )
                    claims.append(claim)
                    claim_counter += 1
        
        return claims
    
    def _deduplicate_claims(self, claims: List[Claim]) -> List[Claim]:
        """Remove duplicate claims based on text similarity"""
        unique_claims = []
        seen_texts = set()
        
        for claim in claims:
            # Normalize claim text for comparison
            normalized_text = re.sub(r'\s+', ' ', claim.text.lower().strip())
            
            if normalized_text not in seen_texts:
                seen_texts.add(normalized_text)
                unique_claims.append(claim)
        
        return unique_claims
    
    async def _verify_claims(self, claims: List[Claim], 
                           verification_level: VerificationLevel) -> List[VerificationResult]:
        """Verify claims based on verification level"""
        verification_results = []
        
        # Determine verification strategy based on level
        if verification_level == VerificationLevel.BASIC:
            # Basic verification - pattern matching and simple checks
            verification_results = await self._verify_claims_basic(claims)
        elif verification_level == VerificationLevel.STANDARD:
            # Standard verification - AI-powered fact checking
            verification_results = await self._verify_claims_standard(claims)
        elif verification_level == VerificationLevel.COMPREHENSIVE:
            # Comprehensive verification - multiple sources and cross-referencing
            verification_results = await self._verify_claims_comprehensive(claims)
        elif verification_level == VerificationLevel.CRITICAL:
            # Critical verification - human review required
            verification_results = await self._verify_claims_critical(claims)
        
        return verification_results
    
    async def _verify_claims_basic(self, claims: List[Claim]) -> List[VerificationResult]:
        """Basic claim verification using pattern matching and heuristics"""
        results = []
        
        for claim in claims:
            start_time = datetime.utcnow()
            
            # Check cache first
            cache_key = hashlib.md5(claim.text.encode()).hexdigest()
            if cache_key in self.verification_cache:
                cached_result = self.verification_cache[cache_key]
                results.append(cached_result)
                self.performance_metrics['cache_hits'] += 1
                continue
            
            # Basic verification logic
            result = VerificationResult(
                claim_id=claim.id,
                result=FactCheckResult.NEEDS_REVIEW,
                confidence=0.5,
                explanation="Basic verification - requires manual review"
            )
            
            # Simple heuristics
            if claim.category == 'statistics':
                if re.search(r'\b(?:100|0)%\b', claim.text):
                    result.result = FactCheckResult.DISPUTED
                    result.explanation = "Absolute percentages (0% or 100%) are often inaccurate"
                    result.confidence = 0.7
            
            elif claim.category == 'dates':
                # Check for reasonable date ranges
                year_match = re.search(r'\b(\d{4})\b', claim.text)
                if year_match:
                    year = int(year_match.group(1))
                    current_year = datetime.now().year
                    if year > current_year:
                        result.result = FactCheckResult.FALSE
                        result.explanation = "Date is in the future"
                        result.confidence = 0.9
                    elif year < 1000:
                        result.result = FactCheckResult.DISPUTED
                        result.explanation = "Very old date - verify accuracy"
                        result.confidence = 0.6
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            result.verification_time = processing_time
            
            # Cache result
            self.verification_cache[cache_key] = result
            results.append(result)
        
        return results
    
    async def _verify_claims_standard(self, claims: List[Claim]) -> List[VerificationResult]:
        """Standard claim verification using AI fact-checking"""
        results = []
        
        # Process claims in batches for efficiency
        batch_size = 5
        for i in range(0, len(claims), batch_size):
            batch = claims[i:i + batch_size]
            batch_results = await self._verify_batch_ai(batch)
            results.extend(batch_results)
        
        return results
    
    async def _verify_batch_ai(self, claims: List[Claim]) -> List[VerificationResult]:
        """Verify a batch of claims using AI"""
        results = []
        
        for claim in claims:
            start_time = datetime.utcnow()
            
            # Check cache
            cache_key = hashlib.md5(claim.text.encode()).hexdigest()
            if cache_key in self.verification_cache:
                cached_result = self.verification_cache[cache_key]
                results.append(cached_result)
                self.performance_metrics['cache_hits'] += 1
                continue
            
            try:
                # AI fact-checking prompt
                prompt = f"""
                Fact-check the following claim and provide a detailed analysis:
                
                Claim: "{claim.text}"
                Category: {claim.category}
                Context: {claim.context}
                
                Please analyze this claim and provide:
                1. Verification result (VERIFIED, DISPUTED, UNVERIFIABLE, FALSE)
                2. Confidence score (0.0-1.0)
                3. Explanation of your reasoning
                4. Suggested correction if the claim is false or disputed
                5. Relevant sources or references if available
                
                Be thorough but concise. Focus on factual accuracy.
                
                Return your response as JSON:
                {{
                    "result": "VERIFIED|DISPUTED|UNVERIFIABLE|FALSE",
                    "confidence": 0.8,
                    "explanation": "detailed explanation",
                    "suggested_correction": "correction if needed",
                    "sources": ["source1", "source2"]
                }}
                """
                
                response = await self.ai_provider_service.generate_content(
                    prompt=prompt,
                    provider="openai",
                    model="gpt-4",
                    max_tokens=500,
                    temperature=0.1
                )
                
                # Parse AI response
                ai_result = json.loads(response.get('content', '{}'))
                
                result = VerificationResult(
                    claim_id=claim.id,
                    result=FactCheckResult(ai_result.get('result', 'NEEDS_REVIEW').lower()),
                    confidence=float(ai_result.get('confidence', 0.5)),
                    explanation=ai_result.get('explanation', ''),
                    suggested_correction=ai_result.get('suggested_correction'),
                    sources=ai_result.get('sources', []),
                    verification_time=(datetime.utcnow() - start_time).total_seconds()
                )
                
                # Cache result
                self.verification_cache[cache_key] = result
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error verifying claim {claim.id}: {str(e)}")
                
                # Fallback result
                result = VerificationResult(
                    claim_id=claim.id,
                    result=FactCheckResult.NEEDS_REVIEW,
                    confidence=0.3,
                    explanation=f"Verification failed: {str(e)}",
                    verification_time=(datetime.utcnow() - start_time).total_seconds()
                )
                results.append(result)
        
        return results
    
    async def _verify_claims_comprehensive(self, claims: List[Claim]) -> List[VerificationResult]:
        """Comprehensive verification with multiple sources and cross-referencing"""
        # For now, use standard verification with additional checks
        results = await self._verify_claims_standard(claims)
        
        # Add comprehensive analysis
        for result in results:
            if result.confidence < 0.7:
                result.explanation += " [Comprehensive review recommended]"
                result.result = FactCheckResult.NEEDS_REVIEW
        
        return results
    
    async def _verify_claims_critical(self, claims: List[Claim]) -> List[VerificationResult]:
        """Critical verification requiring human review"""
        results = []
        
        for claim in claims:
            result = VerificationResult(
                claim_id=claim.id,
                result=FactCheckResult.NEEDS_REVIEW,
                confidence=0.0,
                explanation="Critical verification level - human review required",
                verification_time=0.0
            )
            results.append(result)
        
        return results
    
    def _generate_report(self, content_id: str, claims: List[Claim], 
                        verification_results: List[VerificationResult],
                        verification_level: VerificationLevel,
                        start_time: datetime) -> HallucinationReport:
        """Generate comprehensive hallucination detection report"""
        
        # Count verification results
        result_counts = {
            FactCheckResult.VERIFIED: 0,
            FactCheckResult.DISPUTED: 0,
            FactCheckResult.FALSE: 0,
            FactCheckResult.UNVERIFIABLE: 0,
            FactCheckResult.NEEDS_REVIEW: 0
        }
        
        for result in verification_results:
            result_counts[result.result] += 1
        
        # Calculate overall confidence and risk score
        if verification_results:
            overall_confidence = sum(r.confidence for r in verification_results) / len(verification_results)
        else:
            overall_confidence = 1.0
        
        # Risk score calculation
        total_claims = len(claims)
        if total_claims > 0:
            risk_score = (
                (result_counts[FactCheckResult.FALSE] * 1.0 +
                 result_counts[FactCheckResult.DISPUTED] * 0.7 +
                 result_counts[FactCheckResult.NEEDS_REVIEW] * 0.5) / total_claims
            )
        else:
            risk_score = 0.0
        
        # Generate recommendations
        recommendations = []
        if result_counts[FactCheckResult.FALSE] > 0:
            recommendations.append("Content contains false information that should be corrected")
        if result_counts[FactCheckResult.DISPUTED] > 0:
            recommendations.append("Some claims are disputed and require verification")
        if result_counts[FactCheckResult.NEEDS_REVIEW] > 0:
            recommendations.append("Manual review recommended for unverified claims")
        if risk_score > 0.3:
            recommendations.append("High risk score - comprehensive fact-checking recommended")
        if overall_confidence < 0.6:
            recommendations.append("Low overall confidence - additional verification needed")
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return HallucinationReport(
            content_id=content_id,
            verification_level=verification_level,
            total_claims=total_claims,
            verified_claims=result_counts[FactCheckResult.VERIFIED],
            disputed_claims=result_counts[FactCheckResult.DISPUTED],
            false_claims=result_counts[FactCheckResult.FALSE],
            unverifiable_claims=result_counts[FactCheckResult.UNVERIFIABLE],
            overall_confidence=overall_confidence,
            risk_score=risk_score,
            claims=claims,
            verification_results=verification_results,
            recommendations=recommendations,
            processing_time=processing_time
        )
    
    def _update_metrics(self, report: HallucinationReport):
        """Update performance metrics"""
        self.performance_metrics['total_verifications'] += 1
        
        # Update average processing time
        current_avg = self.performance_metrics['average_processing_time']
        total_verifications = self.performance_metrics['total_verifications']
        
        self.performance_metrics['average_processing_time'] = (
            (current_avg * (total_verifications - 1) + report.processing_time) / 
            total_verifications
        )
        
        # Update accuracy rate (simplified metric)
        if report.total_claims > 0:
            accuracy = report.verified_claims / report.total_claims
            current_accuracy = self.performance_metrics['accuracy_rate']
            
            self.performance_metrics['accuracy_rate'] = (
                (current_accuracy * (total_verifications - 1) + accuracy) / 
                total_verifications
            )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get hallucination detector performance metrics"""
        return {
            'total_verifications': self.performance_metrics['total_verifications'],
            'cache_hits': self.performance_metrics['cache_hits'],
            'cache_hit_rate': (
                self.performance_metrics['cache_hits'] / 
                max(1, self.performance_metrics['total_verifications'])
            ) * 100,
            'average_processing_time': self.performance_metrics['average_processing_time'],
            'accuracy_rate': self.performance_metrics['accuracy_rate'] * 100,
            'cache_size': len(self.verification_cache)
        }
    
    def clear_cache(self):
        """Clear verification cache"""
        self.verification_cache.clear()
        logger.info("Verification cache cleared")

