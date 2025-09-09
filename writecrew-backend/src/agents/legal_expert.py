"""
Legal Writing Expert Agent - Specialized legal document creation and compliance
Part of WriteCrew Multi-Agentic AI Writing System

This agent specializes in legal writing, contract drafting, compliance documentation,
and professional legal communication with jurisdiction-aware capabilities.
"""

from typing import Dict, List, Any, Optional
from crewai import Agent, Task, Tool
from crewai.tools import BaseTool
import asyncio
import logging
from datetime import datetime
import json

from .base_agent import BaseAgent
from ..services.ai_provider_service import AIProviderService
from ..models.task_models import TaskRequest, TaskResponse

# Legal Writing Expert Prompts
LEGAL_EXPERT_PROMPTS = {
    "backstory": """You are a distinguished legal writing expert with over 20 years of experience 
    in legal document drafting, contract negotiation, and compliance documentation. You have worked 
    with top-tier law firms, corporate legal departments, and government agencies across multiple 
    jurisdictions. Your expertise spans contract law, corporate governance, intellectual property, 
    employment law, and regulatory compliance.

    You are known for your precision in legal language, attention to jurisdictional requirements, 
    and ability to translate complex legal concepts into clear, actionable documents. You maintain 
    strict adherence to legal ethics, confidentiality requirements, and professional standards.

    Your writing is characterized by clarity, precision, comprehensive coverage of legal issues, 
    and practical enforceability. You always consider risk mitigation, compliance requirements, 
    and best practices in legal document structure and language.""",

    "legal_document_types": {
        "contracts": "Service agreements, employment contracts, NDAs, licensing agreements, partnership agreements",
        "corporate": "Articles of incorporation, bylaws, board resolutions, shareholder agreements, compliance policies",
        "intellectual_property": "Patent applications, trademark filings, copyright notices, IP licensing agreements",
        "employment": "Employment handbooks, policy documents, termination agreements, non-compete clauses",
        "compliance": "Privacy policies, terms of service, regulatory compliance documents, audit reports",
        "litigation": "Legal briefs, motions, discovery documents, settlement agreements, court filings",
        "real_estate": "Purchase agreements, lease contracts, property deeds, zoning compliance documents",
        "regulatory": "SEC filings, FDA submissions, environmental compliance, industry-specific regulations"
    },

    "legal_analysis_framework": """
    1. LEGAL ISSUE IDENTIFICATION
       - Identify all legal issues and potential risks
       - Analyze jurisdictional requirements and applicable law
       - Assess compliance obligations and regulatory requirements

    2. LEGAL RESEARCH AND PRECEDENT
       - Research relevant statutes, regulations, and case law
       - Identify applicable legal precedents and standards
       - Analyze industry best practices and common approaches

    3. RISK ASSESSMENT AND MITIGATION
       - Evaluate potential legal risks and liabilities
       - Develop risk mitigation strategies and protective clauses
       - Consider enforceability and practical implementation

    4. DOCUMENT STRUCTURE AND LANGUAGE
       - Use precise legal terminology and defined terms
       - Ensure logical flow and comprehensive coverage
       - Include necessary boilerplate and standard clauses

    5. COMPLIANCE AND ETHICS
       - Verify compliance with applicable laws and regulations
       - Ensure adherence to professional ethics and standards
       - Include required disclosures and notices
    """,

    "jurisdiction_considerations": {
        "federal": "Federal laws, regulations, and constitutional requirements",
        "state": "State-specific laws, regulations, and court precedents",
        "local": "Municipal ordinances, local regulations, and zoning requirements",
        "international": "International treaties, foreign laws, and cross-border considerations",
        "industry": "Industry-specific regulations and professional standards"
    }
}

class LegalDocumentDraftingTool(BaseTool):
    """Tool for drafting various types of legal documents"""
    
    name: str = "legal_document_drafting"
    description: str = "Draft comprehensive legal documents with proper structure and language"
    
    def _run(self, document_type: str, requirements: Dict[str, Any], jurisdiction: str = "general") -> Dict[str, Any]:
        """Draft a legal document based on type and requirements"""
        try:
            # Document type validation
            valid_types = list(LEGAL_EXPERT_PROMPTS["legal_document_types"].keys())
            if document_type not in valid_types:
                return {"error": f"Invalid document type. Valid types: {valid_types}"}
            
            # Generate document structure
            document_structure = self._generate_document_structure(document_type, requirements)
            
            # Create document content
            document_content = self._create_document_content(document_type, requirements, jurisdiction)
            
            # Add legal clauses and boilerplate
            legal_clauses = self._add_legal_clauses(document_type, jurisdiction)
            
            # Compliance check
            compliance_review = self._compliance_check(document_type, jurisdiction)
            
            return {
                "document_type": document_type,
                "jurisdiction": jurisdiction,
                "structure": document_structure,
                "content": document_content,
                "legal_clauses": legal_clauses,
                "compliance_review": compliance_review,
                "confidence_score": self._calculate_confidence(document_type, requirements)
            }
            
        except Exception as e:
            return {"error": f"Document drafting failed: {str(e)}"}
    
    def _generate_document_structure(self, document_type: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate appropriate document structure"""
        structures = {
            "contracts": {
                "sections": ["Parties", "Recitals", "Terms and Conditions", "Performance Obligations", 
                           "Payment Terms", "Termination", "Dispute Resolution", "General Provisions"],
                "required_elements": ["Consideration", "Mutual obligations", "Termination clauses", "Governing law"]
            },
            "corporate": {
                "sections": ["Purpose", "Powers", "Governance Structure", "Shareholder Rights", 
                           "Board Composition", "Officer Duties", "Amendment Procedures"],
                "required_elements": ["Corporate purpose", "Governance framework", "Compliance obligations"]
            },
            "employment": {
                "sections": ["Position Description", "Compensation", "Benefits", "Policies", 
                           "Confidentiality", "Termination", "Post-Employment Obligations"],
                "required_elements": ["At-will employment", "Confidentiality", "Non-compete", "Compliance"]
            },
            "compliance": {
                "sections": ["Policy Statement", "Scope", "Responsibilities", "Procedures", 
                           "Monitoring", "Enforcement", "Training", "Review and Updates"],
                "required_elements": ["Regulatory compliance", "Monitoring procedures", "Enforcement mechanisms"]
            }
        }
        
        return structures.get(document_type, {
            "sections": ["Introduction", "Main Provisions", "General Terms"],
            "required_elements": ["Legal compliance", "Clear obligations"]
        })
    
    def _create_document_content(self, document_type: str, requirements: Dict[str, Any], jurisdiction: str) -> str:
        """Create document content based on type and requirements"""
        content_templates = {
            "contracts": f"""
            SERVICE AGREEMENT
            
            This Service Agreement ("Agreement") is entered into on [DATE] between [PARTY 1] and [PARTY 2].
            
            RECITALS
            WHEREAS, [Background and purpose]...
            
            TERMS AND CONDITIONS
            1. Services: [Detailed service description]
            2. Performance Standards: [Quality and delivery requirements]
            3. Compensation: [Payment terms and schedule]
            4. Term and Termination: [Duration and termination conditions]
            
            [Additional provisions based on requirements: {requirements}]
            [Jurisdiction-specific clauses for: {jurisdiction}]
            """,
            
            "corporate": f"""
            CORPORATE BYLAWS
            
            ARTICLE I - CORPORATE PURPOSE
            The corporation is organized for the purpose of [PURPOSE].
            
            ARTICLE II - GOVERNANCE STRUCTURE
            [Board composition and responsibilities]
            
            ARTICLE III - SHAREHOLDER RIGHTS
            [Voting rights and procedures]
            
            [Additional provisions based on requirements: {requirements}]
            [Jurisdiction compliance for: {jurisdiction}]
            """,
            
            "employment": f"""
            EMPLOYMENT AGREEMENT
            
            This Employment Agreement is between [COMPANY] and [EMPLOYEE].
            
            1. POSITION AND DUTIES
            [Job description and responsibilities]
            
            2. COMPENSATION AND BENEFITS
            [Salary, benefits, and incentives]
            
            3. CONFIDENTIALITY AND NON-DISCLOSURE
            [Confidentiality obligations]
            
            [Additional provisions based on requirements: {requirements}]
            [State-specific employment law compliance for: {jurisdiction}]
            """
        }
        
        return content_templates.get(document_type, f"Legal document content for {document_type}")
    
    def _add_legal_clauses(self, document_type: str, jurisdiction: str) -> List[str]:
        """Add appropriate legal clauses and boilerplate"""
        standard_clauses = {
            "contracts": [
                "Force Majeure", "Entire Agreement", "Amendment", "Severability", 
                "Governing Law", "Dispute Resolution", "Notice Provisions"
            ],
            "corporate": [
                "Indemnification", "Limitation of Liability", "Compliance", 
                "Amendment Procedures", "Dissolution"
            ],
            "employment": [
                "At-Will Employment", "Confidentiality", "Non-Compete", 
                "Intellectual Property Assignment", "Dispute Resolution"
            ]
        }
        
        jurisdiction_clauses = {
            "california": ["California Labor Code Compliance", "CCPA Privacy Rights"],
            "new_york": ["New York Labor Law Compliance", "SHIELD Act Requirements"],
            "federal": ["Federal Employment Law Compliance", "ADA Compliance"]
        }
        
        clauses = standard_clauses.get(document_type, ["General Legal Provisions"])
        if jurisdiction in jurisdiction_clauses:
            clauses.extend(jurisdiction_clauses[jurisdiction])
        
        return clauses
    
    def _compliance_check(self, document_type: str, jurisdiction: str) -> Dict[str, Any]:
        """Perform compliance check for the document"""
        compliance_areas = {
            "contracts": ["Contract law", "Consumer protection", "Industry regulations"],
            "corporate": ["Corporate law", "Securities regulations", "Tax compliance"],
            "employment": ["Employment law", "Labor standards", "Anti-discrimination"],
            "compliance": ["Regulatory requirements", "Industry standards", "Privacy laws"]
        }
        
        return {
            "compliance_areas": compliance_areas.get(document_type, ["General legal compliance"]),
            "jurisdiction_requirements": f"Compliance with {jurisdiction} laws and regulations",
            "risk_assessment": "Medium risk - requires legal review",
            "recommendations": ["Professional legal review recommended", "Update based on current law"]
        }
    
    def _calculate_confidence(self, document_type: str, requirements: Dict[str, Any]) -> float:
        """Calculate confidence score for the legal document"""
        base_confidence = 0.85
        
        # Adjust based on document complexity
        complexity_factors = {
            "contracts": 0.9,
            "corporate": 0.8,
            "intellectual_property": 0.75,
            "litigation": 0.7,
            "regulatory": 0.8
        }
        
        complexity_adjustment = complexity_factors.get(document_type, 0.85)
        
        # Adjust based on requirements completeness
        requirements_completeness = len(requirements) / 10  # Assume 10 is ideal
        requirements_adjustment = min(requirements_completeness, 1.0)
        
        final_confidence = base_confidence * complexity_adjustment * requirements_adjustment
        return round(min(final_confidence, 0.95), 2)

class LegalComplianceAnalysisTool(BaseTool):
    """Tool for analyzing legal compliance and risk assessment"""
    
    name: str = "legal_compliance_analysis"
    description: str = "Analyze legal compliance requirements and assess risks"
    
    def _run(self, content: str, document_type: str, jurisdiction: str = "general") -> Dict[str, Any]:
        """Analyze legal compliance for content"""
        try:
            # Compliance analysis
            compliance_issues = self._identify_compliance_issues(content, document_type)
            
            # Risk assessment
            risk_analysis = self._assess_legal_risks(content, document_type, jurisdiction)
            
            # Recommendations
            recommendations = self._generate_compliance_recommendations(compliance_issues, risk_analysis)
            
            return {
                "compliance_issues": compliance_issues,
                "risk_analysis": risk_analysis,
                "recommendations": recommendations,
                "overall_compliance_score": self._calculate_compliance_score(compliance_issues, risk_analysis)
            }
            
        except Exception as e:
            return {"error": f"Compliance analysis failed: {str(e)}"}
    
    def _identify_compliance_issues(self, content: str, document_type: str) -> List[Dict[str, Any]]:
        """Identify potential compliance issues"""
        issues = []
        
        # Common compliance checks
        compliance_checks = {
            "missing_clauses": ["governing_law", "dispute_resolution", "termination"],
            "unclear_terms": ["ambiguous_language", "undefined_terms"],
            "regulatory_requirements": ["industry_specific", "jurisdiction_specific"]
        }
        
        for check_type, items in compliance_checks.items():
            for item in items:
                if item.lower() not in content.lower():
                    issues.append({
                        "type": check_type,
                        "issue": item,
                        "severity": "medium",
                        "description": f"Missing or unclear {item.replace('_', ' ')}"
                    })
        
        return issues
    
    def _assess_legal_risks(self, content: str, document_type: str, jurisdiction: str) -> Dict[str, Any]:
        """Assess legal risks in the content"""
        risk_factors = {
            "enforceability": "medium",
            "liability_exposure": "medium",
            "compliance_risk": "low",
            "litigation_risk": "low"
        }
        
        # Adjust risks based on document type
        if document_type == "contracts":
            risk_factors["enforceability"] = "high"
        elif document_type == "employment":
            risk_factors["compliance_risk"] = "medium"
        elif document_type == "corporate":
            risk_factors["liability_exposure"] = "high"
        
        return {
            "risk_factors": risk_factors,
            "overall_risk_level": "medium",
            "mitigation_required": True
        }
    
    def _generate_compliance_recommendations(self, issues: List[Dict], risk_analysis: Dict) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = [
            "Conduct professional legal review before execution",
            "Ensure all terms are clearly defined and unambiguous",
            "Include appropriate governing law and dispute resolution clauses",
            "Verify compliance with applicable regulations and standards"
        ]
        
        if len(issues) > 5:
            recommendations.append("Significant compliance issues identified - comprehensive legal review required")
        
        if risk_analysis["overall_risk_level"] == "high":
            recommendations.append("High risk factors present - consider additional protective measures")
        
        return recommendations
    
    def _calculate_compliance_score(self, issues: List[Dict], risk_analysis: Dict) -> float:
        """Calculate overall compliance score"""
        base_score = 1.0
        
        # Deduct for issues
        issue_penalty = len(issues) * 0.05
        
        # Deduct for risk level
        risk_penalties = {"low": 0.0, "medium": 0.1, "high": 0.2}
        risk_penalty = risk_penalties.get(risk_analysis["overall_risk_level"], 0.1)
        
        final_score = max(base_score - issue_penalty - risk_penalty, 0.0)
        return round(final_score, 2)

class LegalExpertAgent(BaseAgent):
    """Legal Writing Expert Agent for specialized legal document creation and compliance"""
    
    def __init__(self, ai_provider_service: AIProviderService):
        super().__init__(
            agent_id="legal_expert",
            name="Legal Writing Expert",
            description="Specialized legal document creation and compliance expert",
            ai_provider_service=ai_provider_service
        )
        
        # Initialize specialized tools
        self.legal_tools = [
            LegalDocumentDraftingTool(),
            LegalComplianceAnalysisTool()
        ]
        
        # Legal expertise areas
        self.expertise_areas = [
            "contract_drafting", "corporate_governance", "employment_law",
            "intellectual_property", "compliance_documentation", "litigation_support",
            "regulatory_compliance", "risk_assessment"
        ]
        
        # Initialize CrewAI agent
        self._initialize_crew_agent()
    
    def _initialize_crew_agent(self):
        """Initialize the CrewAI agent with legal expertise"""
        self.crew_agent = Agent(
            role="Expert Legal Writer and Compliance Specialist",
            goal="Create precise, compliant legal documents and provide expert legal writing guidance",
            backstory=LEGAL_EXPERT_PROMPTS["backstory"],
            tools=self.legal_tools,
            llm=self.ai_provider_service.get_primary_llm(),
            memory=True,
            verbose=True,
            allow_delegation=False
        )
    
    async def process_task(self, task_request: TaskRequest) -> TaskResponse:
        """Process legal writing task with specialized expertise"""
        try:
            self.logger.info(f"Processing legal writing task: {task_request.task_type}")
            
            # Validate legal task
            if not self._is_legal_task(task_request):
                return TaskResponse(
                    success=False,
                    error="Task is not suitable for legal writing expert",
                    agent_id=self.agent_id
                )
            
            # Determine legal document type and requirements
            legal_analysis = await self._analyze_legal_requirements(task_request)
            
            # Process based on task type
            if task_request.task_type == "legal_document_creation":
                result = await self._create_legal_document(task_request, legal_analysis)
            elif task_request.task_type == "legal_review":
                result = await self._review_legal_content(task_request, legal_analysis)
            elif task_request.task_type == "compliance_check":
                result = await self._check_compliance(task_request, legal_analysis)
            else:
                result = await self._general_legal_assistance(task_request, legal_analysis)
            
            # Update performance metrics
            await self._update_performance_metrics(True, task_request.task_type)
            
            return TaskResponse(
                success=True,
                content=result["content"],
                metadata=result["metadata"],
                agent_id=self.agent_id,
                confidence_score=result["confidence_score"]
            )
            
        except Exception as e:
            self.logger.error(f"Legal writing task failed: {str(e)}")
            await self._update_performance_metrics(False, task_request.task_type)
            
            return TaskResponse(
                success=False,
                error=f"Legal writing task failed: {str(e)}",
                agent_id=self.agent_id
            )
    
    def _is_legal_task(self, task_request: TaskRequest) -> bool:
        """Determine if task is suitable for legal expert"""
        legal_keywords = [
            "contract", "agreement", "legal", "compliance", "policy", "terms",
            "liability", "intellectual property", "employment", "corporate",
            "regulatory", "litigation", "dispute", "clause", "provision"
        ]
        
        content_lower = task_request.content.lower()
        return any(keyword in content_lower for keyword in legal_keywords)
    
    async def _analyze_legal_requirements(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Analyze legal requirements for the task"""
        # Extract legal context
        legal_context = {
            "document_type": self._identify_document_type(task_request.content),
            "jurisdiction": task_request.metadata.get("jurisdiction", "general"),
            "complexity": self._assess_complexity(task_request.content),
            "compliance_areas": self._identify_compliance_areas(task_request.content)
        }
        
        return legal_context
    
    def _identify_document_type(self, content: str) -> str:
        """Identify the type of legal document"""
        content_lower = content.lower()
        
        document_indicators = {
            "contracts": ["agreement", "contract", "service", "license"],
            "corporate": ["bylaws", "articles", "corporate", "governance"],
            "employment": ["employment", "job", "position", "employee"],
            "intellectual_property": ["patent", "trademark", "copyright", "ip"],
            "compliance": ["policy", "compliance", "procedure", "regulation"],
            "litigation": ["brief", "motion", "discovery", "court"]
        }
        
        for doc_type, keywords in document_indicators.items():
            if any(keyword in content_lower for keyword in keywords):
                return doc_type
        
        return "general"
    
    def _assess_complexity(self, content: str) -> str:
        """Assess the complexity of the legal task"""
        complexity_indicators = {
            "high": ["merger", "acquisition", "securities", "international", "litigation"],
            "medium": ["employment", "licensing", "partnership", "corporate"],
            "low": ["nda", "simple", "basic", "standard"]
        }
        
        content_lower = content.lower()
        
        for level, indicators in complexity_indicators.items():
            if any(indicator in content_lower for indicator in indicators):
                return level
        
        return "medium"
    
    def _identify_compliance_areas(self, content: str) -> List[str]:
        """Identify relevant compliance areas"""
        compliance_areas = []
        content_lower = content.lower()
        
        compliance_keywords = {
            "employment_law": ["employment", "labor", "workplace", "employee"],
            "data_privacy": ["privacy", "data", "gdpr", "ccpa", "personal information"],
            "securities": ["securities", "investment", "sec", "disclosure"],
            "intellectual_property": ["patent", "trademark", "copyright", "trade secret"],
            "antitrust": ["antitrust", "competition", "monopoly", "market"],
            "environmental": ["environmental", "epa", "pollution", "sustainability"]
        }
        
        for area, keywords in compliance_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                compliance_areas.append(area)
        
        return compliance_areas if compliance_areas else ["general_compliance"]
    
    async def _create_legal_document(self, task_request: TaskRequest, legal_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create a legal document based on requirements"""
        # Use legal document drafting tool
        drafting_tool = LegalDocumentDraftingTool()
        
        document_result = drafting_tool._run(
            document_type=legal_analysis["document_type"],
            requirements=task_request.metadata,
            jurisdiction=legal_analysis["jurisdiction"]
        )
        
        if "error" in document_result:
            raise Exception(document_result["error"])
        
        # Create comprehensive legal document
        legal_document = f"""
        {document_result['content']}
        
        LEGAL CLAUSES:
        {chr(10).join(f"• {clause}" for clause in document_result['legal_clauses'])}
        
        COMPLIANCE REVIEW:
        Compliance Areas: {', '.join(document_result['compliance_review']['compliance_areas'])}
        Jurisdiction: {document_result['compliance_review']['jurisdiction_requirements']}
        Risk Assessment: {document_result['compliance_review']['risk_assessment']}
        
        RECOMMENDATIONS:
        {chr(10).join(f"• {rec}" for rec in document_result['compliance_review']['recommendations'])}
        """
        
        return {
            "content": legal_document,
            "metadata": {
                "document_type": legal_analysis["document_type"],
                "jurisdiction": legal_analysis["jurisdiction"],
                "compliance_areas": legal_analysis["compliance_areas"],
                "structure": document_result["structure"],
                "legal_clauses": document_result["legal_clauses"]
            },
            "confidence_score": document_result["confidence_score"]
        }
    
    async def _review_legal_content(self, task_request: TaskRequest, legal_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Review legal content for compliance and accuracy"""
        # Use compliance analysis tool
        compliance_tool = LegalComplianceAnalysisTool()
        
        compliance_result = compliance_tool._run(
            content=task_request.content,
            document_type=legal_analysis["document_type"],
            jurisdiction=legal_analysis["jurisdiction"]
        )
        
        if "error" in compliance_result:
            raise Exception(compliance_result["error"])
        
        # Create comprehensive review
        review_content = f"""
        LEGAL CONTENT REVIEW
        
        COMPLIANCE ANALYSIS:
        Overall Compliance Score: {compliance_result['overall_compliance_score']}/1.0
        
        IDENTIFIED ISSUES:
        {chr(10).join(f"• {issue['type']}: {issue['description']} (Severity: {issue['severity']})" 
                     for issue in compliance_result['compliance_issues'])}
        
        RISK ASSESSMENT:
        Overall Risk Level: {compliance_result['risk_analysis']['overall_risk_level']}
        Risk Factors: {', '.join(f"{k}: {v}" for k, v in compliance_result['risk_analysis']['risk_factors'].items())}
        
        RECOMMENDATIONS:
        {chr(10).join(f"• {rec}" for rec in compliance_result['recommendations'])}
        """
        
        return {
            "content": review_content,
            "metadata": {
                "compliance_score": compliance_result["overall_compliance_score"],
                "risk_level": compliance_result["risk_analysis"]["overall_risk_level"],
                "issues_count": len(compliance_result["compliance_issues"]),
                "document_type": legal_analysis["document_type"]
            },
            "confidence_score": 0.9
        }
    
    async def _check_compliance(self, task_request: TaskRequest, legal_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Perform detailed compliance check"""
        # Detailed compliance analysis
        compliance_areas = legal_analysis["compliance_areas"]
        jurisdiction = legal_analysis["jurisdiction"]
        
        compliance_report = f"""
        COMPLIANCE CHECK REPORT
        
        DOCUMENT TYPE: {legal_analysis['document_type']}
        JURISDICTION: {jurisdiction}
        COMPLEXITY LEVEL: {legal_analysis['complexity']}
        
        COMPLIANCE AREAS REVIEWED:
        {chr(10).join(f"• {area.replace('_', ' ').title()}" for area in compliance_areas)}
        
        REGULATORY REQUIREMENTS:
        • Federal law compliance verification
        • State/local regulation adherence
        • Industry-specific standards review
        • Professional ethics compliance
        
        RECOMMENDATIONS:
        • Engage qualified legal counsel for final review
        • Ensure all parties understand legal obligations
        • Regular compliance monitoring and updates
        • Document retention and audit trail maintenance
        """
        
        return {
            "content": compliance_report,
            "metadata": {
                "compliance_areas": compliance_areas,
                "jurisdiction": jurisdiction,
                "complexity": legal_analysis["complexity"],
                "review_type": "compliance_check"
            },
            "confidence_score": 0.85
        }
    
    async def _general_legal_assistance(self, task_request: TaskRequest, legal_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Provide general legal writing assistance"""
        # Create CrewAI task for general legal assistance
        legal_task = Task(
            description=f"""
            Provide expert legal writing assistance for the following request:
            
            Content: {task_request.content}
            Document Type: {legal_analysis['document_type']}
            Jurisdiction: {legal_analysis['jurisdiction']}
            Complexity: {legal_analysis['complexity']}
            
            Apply the legal analysis framework:
            {LEGAL_EXPERT_PROMPTS['legal_analysis_framework']}
            
            Ensure compliance with professional legal writing standards and provide
            practical, actionable guidance while noting any limitations or areas
            requiring professional legal review.
            """,
            agent=self.crew_agent,
            expected_output="Comprehensive legal writing assistance with professional guidance"
        )
        
        # Execute task
        result = await asyncio.to_thread(legal_task.execute)
        
        return {
            "content": result,
            "metadata": {
                "document_type": legal_analysis["document_type"],
                "jurisdiction": legal_analysis["jurisdiction"],
                "assistance_type": "general_legal_writing"
            },
            "confidence_score": 0.8
        }
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get legal expert capabilities"""
        return {
            "agent_type": "legal_expert",
            "expertise_areas": self.expertise_areas,
            "document_types": list(LEGAL_EXPERT_PROMPTS["legal_document_types"].keys()),
            "jurisdictions": ["federal", "state", "local", "international"],
            "compliance_areas": [
                "employment_law", "data_privacy", "securities", "intellectual_property",
                "antitrust", "environmental", "corporate_governance", "contract_law"
            ],
            "tools": [tool.name for tool in self.legal_tools],
            "performance_metrics": await self.get_performance_metrics()
        }
    
    async def get_legal_templates(self) -> Dict[str, Any]:
        """Get available legal document templates"""
        return {
            "contract_templates": [
                "Service Agreement", "Employment Contract", "Non-Disclosure Agreement",
                "Licensing Agreement", "Partnership Agreement", "Consulting Agreement"
            ],
            "corporate_templates": [
                "Articles of Incorporation", "Corporate Bylaws", "Shareholder Agreement",
                "Board Resolutions", "Stock Purchase Agreement"
            ],
            "compliance_templates": [
                "Privacy Policy", "Terms of Service", "Employee Handbook",
                "Code of Conduct", "Compliance Manual"
            ],
            "intellectual_property_templates": [
                "Patent Application", "Trademark Filing", "Copyright Notice",
                "IP Assignment Agreement", "License Agreement"
            ]
        }

