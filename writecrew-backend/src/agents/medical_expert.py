"""
Medical Writing Expert Agent - Specialized medical document creation and clinical research
Part of WriteCrew Multi-Agentic AI Writing System

This agent specializes in medical writing, clinical research documentation, regulatory submissions,
and professional medical communication with evidence-based methodology and compliance awareness.
"""

from typing import Dict, List, Any, Optional
from crewai import Agent, Task, Tool
from crewai.tools import BaseTool
import asyncio
import logging
from datetime import datetime
import json
import re

from .base_agent import BaseAgent
from ..services.ai_provider_service import AIProviderService
from ..models.task_models import TaskRequest, TaskResponse

# Medical Writing Expert Prompts
MEDICAL_EXPERT_PROMPTS = {
    "backstory": """You are a distinguished medical writing expert with over 15 years of experience 
    in clinical research, regulatory affairs, and medical communications. You hold advanced degrees 
    in life sciences and have worked with leading pharmaceutical companies, academic medical centers, 
    CROs, and regulatory agencies including FDA, EMA, and ICH.

    Your expertise spans clinical trial protocols, regulatory submissions, medical publications, 
    clinical study reports, investigator brochures, and patient education materials. You are 
    well-versed in GCP, ICH guidelines, FDA regulations, and international medical writing standards.

    You are known for your precision in medical terminology, adherence to evidence-based medicine 
    principles, and ability to communicate complex medical concepts clearly to diverse audiences 
    including healthcare professionals, regulatory authorities, and patients.

    Your writing is characterized by scientific rigor, regulatory compliance, ethical considerations, 
    and commitment to patient safety. You always ensure accuracy of medical information, proper 
    citation of evidence, and adherence to medical writing best practices.""",

    "medical_document_types": {
        "clinical_research": "Protocols, CSRs, investigator brochures, clinical overviews, study summaries",
        "regulatory": "CTD documents, FDA submissions, EMA applications, IND/NDA filings, safety reports",
        "publications": "Journal articles, abstracts, posters, case reports, review articles, meta-analyses",
        "educational": "Patient information leaflets, healthcare provider education, medical training materials",
        "commercial": "Medical affairs documents, product monographs, scientific communications, MSL materials",
        "safety": "Pharmacovigilance reports, risk management plans, safety updates, adverse event reports",
        "quality": "SOPs, validation reports, quality manuals, audit reports, compliance documentation",
        "healthcare": "Clinical guidelines, treatment protocols, care pathways, policy documents"
    },

    "medical_writing_framework": """
    1. SCIENTIFIC FOUNDATION
       - Evidence-based approach with systematic literature review
       - Critical appraisal of clinical data and research methodology
       - Statistical analysis interpretation and presentation
       - Risk-benefit assessment and clinical significance evaluation

    2. REGULATORY COMPLIANCE
       - ICH guidelines adherence (E6, E3, E2A, M4, etc.)
       - FDA/EMA regulatory requirements and formatting standards
       - GCP compliance and ethical considerations
       - Data integrity and audit trail requirements

    3. MEDICAL ACCURACY
       - Precise medical terminology and nomenclature
       - Accurate representation of clinical data and findings
       - Proper citation of medical literature and evidence
       - Clinical relevance and therapeutic context

    4. AUDIENCE CONSIDERATION
       - Healthcare professional vs. patient communication
       - Regulatory authority requirements and expectations
       - Scientific community standards and peer review criteria
       - Cultural and linguistic considerations for global submissions

    5. ETHICAL AND SAFETY CONSIDERATIONS
       - Patient safety and benefit-risk assessment
       - Informed consent and patient rights
       - Conflict of interest disclosure and transparency
       - Responsible medical communication practices
    """,

    "regulatory_standards": {
        "ich_guidelines": "ICH E6 (GCP), E3 (CSR), E2A (Pharmacovigilance), M4 (CTD)",
        "fda_requirements": "21 CFR Part 11, 312 (IND), 314 (NDA), 601 (BLA)",
        "ema_guidelines": "CHMP guidelines, EPAR requirements, EU CTR compliance",
        "quality_standards": "ISO 14155, CONSORT, STROBE, PRISMA guidelines"
    },

    "therapeutic_areas": {
        "oncology": "Cancer research, immunotherapy, targeted therapy, biomarkers",
        "cardiology": "Cardiovascular disease, interventional cardiology, heart failure",
        "neurology": "CNS disorders, neurodegenerative diseases, psychiatric conditions",
        "infectious_disease": "Antimicrobials, vaccines, viral infections, resistance",
        "endocrinology": "Diabetes, metabolic disorders, hormonal therapies",
        "immunology": "Autoimmune diseases, immunosuppression, biologics",
        "respiratory": "Pulmonary diseases, asthma, COPD, respiratory infections",
        "rare_diseases": "Orphan drugs, genetic disorders, specialized therapies"
    }
}

class ClinicalDocumentCreationTool(BaseTool):
    """Tool for creating clinical research and regulatory documents"""
    
    name: str = "clinical_document_creation"
    description: str = "Create comprehensive clinical research and regulatory documents"
    
    def _run(self, document_type: str, therapeutic_area: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create clinical document based on type and requirements"""
        try:
            # Document type validation
            valid_types = list(MEDICAL_EXPERT_PROMPTS["medical_document_types"].keys())
            if document_type not in valid_types:
                return {"error": f"Invalid document type. Valid types: {valid_types}"}
            
            # Generate document structure
            document_structure = self._generate_clinical_structure(document_type, therapeutic_area)
            
            # Create document content
            document_content = self._create_clinical_content(document_type, therapeutic_area, requirements)
            
            # Add regulatory compliance elements
            regulatory_elements = self._add_regulatory_compliance(document_type)
            
            # Evidence and citation framework
            evidence_framework = self._create_evidence_framework(document_type, therapeutic_area)
            
            return {
                "document_type": document_type,
                "therapeutic_area": therapeutic_area,
                "structure": document_structure,
                "content": document_content,
                "regulatory_elements": regulatory_elements,
                "evidence_framework": evidence_framework,
                "confidence_score": self._calculate_medical_confidence(document_type, therapeutic_area, requirements)
            }
            
        except Exception as e:
            return {"error": f"Clinical document creation failed: {str(e)}"}
    
    def _generate_clinical_structure(self, document_type: str, therapeutic_area: str) -> Dict[str, Any]:
        """Generate appropriate clinical document structure"""
        structures = {
            "clinical_research": {
                "protocol": ["Title", "Synopsis", "Background", "Objectives", "Study Design", 
                           "Study Population", "Treatments", "Assessments", "Statistical Analysis", 
                           "Ethics", "Data Management", "References", "Appendices"],
                "csr": ["Synopsis", "Introduction", "Study Objectives", "Investigational Plan", 
                       "Study Patients", "Efficacy Evaluation", "Safety Evaluation", 
                       "Discussion and Conclusions", "Tables and Figures", "Appendices"],
                "required_elements": ["ICH compliance", "GCP adherence", "Statistical plan", "Safety monitoring"]
            },
            "regulatory": {
                "sections": ["Administrative Information", "Quality", "Nonclinical", "Clinical", 
                           "Risk Management", "Product Information"],
                "ctd_modules": ["Module 1 (Regional)", "Module 2 (Summaries)", "Module 3 (Quality)", 
                              "Module 4 (Nonclinical)", "Module 5 (Clinical)"],
                "required_elements": ["Regulatory compliance", "Benefit-risk assessment", "Product labeling"]
            },
            "publications": {
                "sections": ["Abstract", "Introduction", "Methods", "Results", "Discussion", 
                           "Conclusions", "References", "Supplementary Material"],
                "journal_requirements": ["CONSORT compliance", "STROBE guidelines", "PRISMA standards"],
                "required_elements": ["Peer review readiness", "Statistical rigor", "Clinical significance"]
            },
            "safety": {
                "sections": ["Executive Summary", "Safety Overview", "Adverse Events Analysis", 
                           "Serious Adverse Events", "Deaths", "Laboratory Abnormalities", 
                           "Risk Assessment", "Conclusions"],
                "required_elements": ["Pharmacovigilance compliance", "Signal detection", "Risk mitigation"]
            }
        }
        
        return structures.get(document_type, {
            "sections": ["Introduction", "Main Content", "Conclusions"],
            "required_elements": ["Medical accuracy", "Evidence-based content"]
        })
    
    def _create_clinical_content(self, document_type: str, therapeutic_area: str, requirements: Dict[str, Any]) -> str:
        """Create clinical document content based on type and therapeutic area"""
        content_templates = {
            "clinical_research": f"""
            CLINICAL STUDY PROTOCOL
            
            TITLE: [Study Title for {therapeutic_area}]
            
            SYNOPSIS
            Study Design: [Randomized, double-blind, placebo-controlled study]
            Study Population: [Target patient population]
            Primary Objective: [Primary efficacy/safety endpoint]
            Secondary Objectives: [Secondary endpoints and exploratory analyses]
            
            BACKGROUND AND RATIONALE
            Medical Need: [Unmet medical need in {therapeutic_area}]
            Scientific Rationale: [Mechanism of action and preclinical data]
            Clinical Development Strategy: [Development plan and regulatory pathway]
            
            STUDY OBJECTIVES
            Primary: [Primary efficacy or safety objective]
            Secondary: [Secondary objectives including pharmacokinetics, biomarkers]
            Exploratory: [Exploratory endpoints and translational research]
            
            [Additional sections based on requirements: {requirements}]
            [Therapeutic area-specific considerations for: {therapeutic_area}]
            """,
            
            "regulatory": f"""
            CLINICAL OVERVIEW
            
            EXECUTIVE SUMMARY
            Product: [Investigational medicinal product]
            Indication: [{therapeutic_area} indication]
            Development Program: [Clinical development overview]
            
            BENEFIT-RISK ASSESSMENT
            Efficacy Summary: [Key efficacy findings]
            Safety Profile: [Safety overview and risk characterization]
            Benefit-Risk Conclusion: [Overall benefit-risk assessment]
            
            CLINICAL DEVELOPMENT PROGRAM
            Phase I Studies: [First-in-human and dose escalation]
            Phase II Studies: [Proof-of-concept and dose finding]
            Phase III Studies: [Pivotal efficacy and safety studies]
            
            [Additional sections based on requirements: {requirements}]
            [Regulatory pathway for: {therapeutic_area}]
            """,
            
            "publications": f"""
            RESEARCH ARTICLE
            
            ABSTRACT
            Background: [Clinical problem and rationale]
            Methods: [Study design and methodology]
            Results: [Key findings and statistical significance]
            Conclusions: [Clinical implications and significance]
            
            INTRODUCTION
            Clinical Context: [Disease burden and current treatment landscape]
            Rationale: [Scientific rationale for the study]
            Objectives: [Study objectives and hypotheses]
            
            METHODS
            Study Design: [Methodology and statistical plan]
            Participants: [Inclusion/exclusion criteria and demographics]
            Interventions: [Treatment protocols and procedures]
            Outcomes: [Primary and secondary endpoints]
            Statistical Analysis: [Statistical methods and analysis plan]
            
            [Additional sections based on requirements: {requirements}]
            [Therapeutic area-specific methodology for: {therapeutic_area}]
            """
        }
        
        return content_templates.get(document_type, f"Medical document content for {document_type} in {therapeutic_area}")
    
    def _add_regulatory_compliance(self, document_type: str) -> List[str]:
        """Add appropriate regulatory compliance elements"""
        compliance_elements = {
            "clinical_research": [
                "ICH E6 (GCP) Compliance", "Protocol Amendments Tracking", "Informed Consent Requirements",
                "Data Integrity Standards", "Safety Reporting Procedures", "Audit Trail Documentation"
            ],
            "regulatory": [
                "ICH M4 (CTD) Format", "Regional Regulatory Requirements", "Quality by Design Principles",
                "Risk Management Plan", "Pharmacovigilance System", "Post-Marketing Commitments"
            ],
            "publications": [
                "CONSORT Statement Compliance", "ICMJE Authorship Criteria", "Conflict of Interest Disclosure",
                "Clinical Trial Registration", "Data Sharing Statement", "Ethical Approval Documentation"
            ],
            "safety": [
                "ICH E2A Pharmacovigilance", "Expedited Reporting Requirements", "Signal Detection Methods",
                "Risk Minimization Measures", "Benefit-Risk Evaluation", "Regulatory Communication"
            ]
        }
        
        return compliance_elements.get(document_type, ["General Medical Writing Standards", "Ethical Guidelines"])
    
    def _create_evidence_framework(self, document_type: str, therapeutic_area: str) -> Dict[str, Any]:
        """Create evidence-based framework for the document"""
        return {
            "literature_search": {
                "databases": ["PubMed/MEDLINE", "Embase", "Cochrane Library", "ClinicalTrials.gov"],
                "search_strategy": f"Systematic search for {therapeutic_area} evidence",
                "inclusion_criteria": "Relevant clinical studies and systematic reviews",
                "quality_assessment": "Critical appraisal using appropriate tools"
            },
            "evidence_hierarchy": {
                "level_1": "Systematic reviews and meta-analyses",
                "level_2": "Randomized controlled trials",
                "level_3": "Cohort studies and case-control studies",
                "level_4": "Case series and expert opinion"
            },
            "statistical_considerations": {
                "sample_size": "Power calculation and statistical justification",
                "analysis_plan": "Pre-specified statistical analysis plan",
                "multiplicity": "Multiple comparison adjustments",
                "missing_data": "Missing data handling strategy"
            },
            "clinical_significance": {
                "primary_endpoint": "Clinically meaningful difference",
                "secondary_endpoints": "Supportive evidence evaluation",
                "subgroup_analyses": "Pre-specified subgroup considerations",
                "real_world_evidence": "External validity and generalizability"
            }
        }
    
    def _calculate_medical_confidence(self, document_type: str, therapeutic_area: str, requirements: Dict[str, Any]) -> float:
        """Calculate confidence score for medical document"""
        base_confidence = 0.85
        
        # Adjust based on document complexity
        complexity_factors = {
            "clinical_research": 0.9,
            "regulatory": 0.85,
            "publications": 0.9,
            "safety": 0.8,
            "educational": 0.95
        }
        
        # Adjust based on therapeutic area familiarity
        therapeutic_factors = {
            "oncology": 0.85,
            "cardiology": 0.9,
            "neurology": 0.8,
            "infectious_disease": 0.9,
            "rare_diseases": 0.75
        }
        
        complexity_adjustment = complexity_factors.get(document_type, 0.85)
        therapeutic_adjustment = therapeutic_factors.get(therapeutic_area, 0.85)
        
        # Adjust based on requirements completeness
        requirements_completeness = min(len(requirements) / 8, 1.0)  # Assume 8 is ideal
        
        final_confidence = base_confidence * complexity_adjustment * therapeutic_adjustment * requirements_completeness
        return round(min(final_confidence, 0.95), 2)

class MedicalLiteratureAnalysisTool(BaseTool):
    """Tool for analyzing medical literature and evidence"""
    
    name: str = "medical_literature_analysis"
    description: str = "Analyze medical literature and provide evidence-based insights"
    
    def _run(self, research_question: str, therapeutic_area: str, study_types: List[str] = None) -> Dict[str, Any]:
        """Analyze medical literature for research question"""
        try:
            if study_types is None:
                study_types = ["rct", "cohort", "case_control", "systematic_review"]
            
            # Literature search strategy
            search_strategy = self._develop_search_strategy(research_question, therapeutic_area)
            
            # Evidence synthesis
            evidence_synthesis = self._synthesize_evidence(research_question, study_types)
            
            # Quality assessment
            quality_assessment = self._assess_evidence_quality(study_types)
            
            # Clinical recommendations
            recommendations = self._generate_clinical_recommendations(research_question, therapeutic_area)
            
            return {
                "research_question": research_question,
                "therapeutic_area": therapeutic_area,
                "search_strategy": search_strategy,
                "evidence_synthesis": evidence_synthesis,
                "quality_assessment": quality_assessment,
                "recommendations": recommendations,
                "confidence_score": self._calculate_literature_confidence(study_types, therapeutic_area)
            }
            
        except Exception as e:
            return {"error": f"Literature analysis failed: {str(e)}"}
    
    def _develop_search_strategy(self, research_question: str, therapeutic_area: str) -> Dict[str, Any]:
        """Develop systematic literature search strategy"""
        # Extract key concepts from research question
        key_concepts = self._extract_key_concepts(research_question)
        
        return {
            "pico_framework": {
                "population": f"Patients with {therapeutic_area} conditions",
                "intervention": "Relevant therapeutic interventions",
                "comparator": "Standard of care or placebo",
                "outcomes": "Clinical efficacy and safety outcomes"
            },
            "search_terms": {
                "primary_terms": key_concepts,
                "mesh_terms": f"Medical Subject Headings for {therapeutic_area}",
                "synonyms": "Alternative terminology and abbreviations",
                "boolean_operators": "AND, OR, NOT combinations"
            },
            "databases": [
                "PubMed/MEDLINE", "Embase", "Cochrane Central", "ClinicalTrials.gov",
                "WHO ICTRP", "FDA Orange Book", "EMA Database"
            ],
            "filters": {
                "publication_date": "Last 10 years (or as appropriate)",
                "language": "English and major languages",
                "study_design": "RCTs, systematic reviews, cohort studies",
                "human_studies": "Human subjects only"
            }
        }
    
    def _extract_key_concepts(self, research_question: str) -> List[str]:
        """Extract key medical concepts from research question"""
        # Simple keyword extraction (in real implementation, would use NLP)
        medical_keywords = [
            "treatment", "therapy", "drug", "intervention", "efficacy", "safety",
            "outcome", "endpoint", "trial", "study", "patient", "disease", "condition"
        ]
        
        question_lower = research_question.lower()
        extracted_concepts = [keyword for keyword in medical_keywords if keyword in question_lower]
        
        # Add specific terms from the question
        words = re.findall(r'\b[a-zA-Z]{4,}\b', research_question)
        extracted_concepts.extend(words[:5])  # Add first 5 significant words
        
        return list(set(extracted_concepts))
    
    def _synthesize_evidence(self, research_question: str, study_types: List[str]) -> Dict[str, Any]:
        """Synthesize evidence from different study types"""
        evidence_levels = {
            "systematic_review": {
                "level": "1a",
                "description": "Systematic review of RCTs with meta-analysis",
                "strength": "Highest quality evidence",
                "limitations": "Heterogeneity between studies"
            },
            "rct": {
                "level": "1b",
                "description": "Individual randomized controlled trials",
                "strength": "High internal validity",
                "limitations": "Limited external validity"
            },
            "cohort": {
                "level": "2a",
                "description": "Prospective cohort studies",
                "strength": "Good for long-term outcomes",
                "limitations": "Potential confounding"
            },
            "case_control": {
                "level": "3a",
                "description": "Case-control studies",
                "strength": "Efficient for rare outcomes",
                "limitations": "Recall bias, selection bias"
            }
        }
        
        synthesis = {}
        for study_type in study_types:
            if study_type in evidence_levels:
                synthesis[study_type] = evidence_levels[study_type]
        
        return {
            "evidence_hierarchy": synthesis,
            "overall_quality": self._assess_overall_quality(study_types),
            "consistency": "Assessment of consistency across studies",
            "applicability": "Relevance to clinical practice",
            "precision": "Confidence intervals and statistical significance"
        }
    
    def _assess_evidence_quality(self, study_types: List[str]) -> Dict[str, Any]:
        """Assess quality of evidence using standard frameworks"""
        quality_frameworks = {
            "grade": {
                "description": "GRADE (Grading of Recommendations Assessment)",
                "domains": ["Risk of bias", "Inconsistency", "Indirectness", "Imprecision", "Publication bias"],
                "quality_levels": ["High", "Moderate", "Low", "Very low"]
            },
            "cochrane": {
                "description": "Cochrane Risk of Bias Tool",
                "domains": ["Random sequence generation", "Allocation concealment", "Blinding", "Incomplete outcome data"],
                "assessment": ["Low risk", "High risk", "Unclear risk"]
            },
            "newcastle_ottawa": {
                "description": "Newcastle-Ottawa Scale for observational studies",
                "domains": ["Selection", "Comparability", "Outcome"],
                "scoring": "Star system (maximum 9 stars)"
            }
        }
        
        return {
            "quality_frameworks": quality_frameworks,
            "overall_assessment": self._calculate_overall_quality(study_types),
            "recommendations": [
                "Use appropriate quality assessment tools",
                "Consider risk of bias in interpretation",
                "Assess consistency across studies",
                "Evaluate clinical significance"
            ]
        }
    
    def _assess_overall_quality(self, study_types: List[str]) -> str:
        """Assess overall quality based on study types"""
        if "systematic_review" in study_types:
            return "High quality"
        elif "rct" in study_types:
            return "Moderate to high quality"
        elif "cohort" in study_types:
            return "Moderate quality"
        else:
            return "Low to moderate quality"
    
    def _calculate_overall_quality(self, study_types: List[str]) -> str:
        """Calculate overall quality assessment"""
        quality_scores = {
            "systematic_review": 4,
            "rct": 3,
            "cohort": 2,
            "case_control": 1
        }
        
        max_score = max([quality_scores.get(st, 0) for st in study_types])
        
        if max_score >= 4:
            return "High quality evidence"
        elif max_score >= 3:
            return "Moderate to high quality evidence"
        elif max_score >= 2:
            return "Moderate quality evidence"
        else:
            return "Low quality evidence"
    
    def _generate_clinical_recommendations(self, research_question: str, therapeutic_area: str) -> List[str]:
        """Generate evidence-based clinical recommendations"""
        return [
            f"Based on current evidence in {therapeutic_area}:",
            "• Conduct systematic literature review for comprehensive evidence",
            "• Prioritize high-quality RCTs and systematic reviews",
            "• Consider real-world evidence for external validity",
            "• Assess benefit-risk profile in target population",
            "• Evaluate clinical significance beyond statistical significance",
            "• Consider guideline recommendations and expert consensus",
            "• Monitor for emerging evidence and safety signals"
        ]
    
    def _calculate_literature_confidence(self, study_types: List[str], therapeutic_area: str) -> float:
        """Calculate confidence in literature analysis"""
        base_confidence = 0.8
        
        # Adjust based on study quality
        quality_bonus = 0.0
        if "systematic_review" in study_types:
            quality_bonus += 0.1
        if "rct" in study_types:
            quality_bonus += 0.05
        
        # Adjust based on therapeutic area maturity
        area_factors = {
            "oncology": 0.95,
            "cardiology": 0.95,
            "infectious_disease": 0.9,
            "rare_diseases": 0.8
        }
        
        area_adjustment = area_factors.get(therapeutic_area, 0.85)
        
        final_confidence = (base_confidence + quality_bonus) * area_adjustment
        return round(min(final_confidence, 0.95), 2)

class MedicalExpertAgent(BaseAgent):
    """Medical Writing Expert Agent for specialized medical document creation and clinical research"""
    
    def __init__(self, ai_provider_service: AIProviderService):
        super().__init__(
            agent_id="medical_expert",
            name="Medical Writing Expert",
            description="Specialized medical document creation and clinical research expert",
            ai_provider_service=ai_provider_service
        )
        
        # Initialize specialized tools
        self.medical_tools = [
            ClinicalDocumentCreationTool(),
            MedicalLiteratureAnalysisTool()
        ]
        
        # Medical expertise areas
        self.expertise_areas = [
            "clinical_research", "regulatory_affairs", "medical_publications",
            "pharmacovigilance", "medical_communications", "clinical_data_analysis",
            "evidence_based_medicine", "medical_education"
        ]
        
        # Therapeutic areas
        self.therapeutic_areas = list(MEDICAL_EXPERT_PROMPTS["therapeutic_areas"].keys())
        
        # Initialize CrewAI agent
        self._initialize_crew_agent()
    
    def _initialize_crew_agent(self):
        """Initialize the CrewAI agent with medical expertise"""
        self.crew_agent = Agent(
            role="Expert Medical Writer and Clinical Research Specialist",
            goal="Create accurate, evidence-based medical documents and provide expert clinical guidance",
            backstory=MEDICAL_EXPERT_PROMPTS["backstory"],
            tools=self.medical_tools,
            llm=self.ai_provider_service.get_primary_llm(),
            memory=True,
            verbose=True,
            allow_delegation=False
        )
    
    async def process_task(self, task_request: TaskRequest) -> TaskResponse:
        """Process medical writing task with specialized expertise"""
        try:
            self.logger.info(f"Processing medical writing task: {task_request.task_type}")
            
            # Validate medical task
            if not self._is_medical_task(task_request):
                return TaskResponse(
                    success=False,
                    error="Task is not suitable for medical writing expert",
                    agent_id=self.agent_id
                )
            
            # Determine medical context and requirements
            medical_analysis = await self._analyze_medical_requirements(task_request)
            
            # Process based on task type
            if task_request.task_type == "clinical_document_creation":
                result = await self._create_clinical_document(task_request, medical_analysis)
            elif task_request.task_type == "literature_review":
                result = await self._conduct_literature_review(task_request, medical_analysis)
            elif task_request.task_type == "medical_publication":
                result = await self._create_medical_publication(task_request, medical_analysis)
            elif task_request.task_type == "regulatory_submission":
                result = await self._create_regulatory_submission(task_request, medical_analysis)
            else:
                result = await self._general_medical_assistance(task_request, medical_analysis)
            
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
            self.logger.error(f"Medical writing task failed: {str(e)}")
            await self._update_performance_metrics(False, task_request.task_type)
            
            return TaskResponse(
                success=False,
                error=f"Medical writing task failed: {str(e)}",
                agent_id=self.agent_id
            )
    
    def _is_medical_task(self, task_request: TaskRequest) -> bool:
        """Determine if task is suitable for medical expert"""
        medical_keywords = [
            "clinical", "medical", "patient", "treatment", "therapy", "drug", "study",
            "trial", "research", "protocol", "regulatory", "fda", "ema", "safety",
            "efficacy", "adverse", "pharmacology", "diagnosis", "disease", "condition",
            "healthcare", "medicine", "pharmaceutical", "biomedical", "therapeutic"
        ]
        
        content_lower = task_request.content.lower()
        return any(keyword in content_lower for keyword in medical_keywords)
    
    async def _analyze_medical_requirements(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Analyze medical requirements for the task"""
        medical_context = {
            "document_type": self._identify_medical_document_type(task_request.content),
            "therapeutic_area": self._identify_therapeutic_area(task_request.content),
            "regulatory_context": self._identify_regulatory_context(task_request.content),
            "target_audience": self._identify_target_audience(task_request.content),
            "evidence_level": self._assess_evidence_requirements(task_request.content)
        }
        
        return medical_context
    
    def _identify_medical_document_type(self, content: str) -> str:
        """Identify the type of medical document"""
        content_lower = content.lower()
        
        document_indicators = {
            "clinical_research": ["protocol", "study", "trial", "csr", "clinical study report"],
            "regulatory": ["submission", "fda", "ema", "ctd", "ind", "nda", "bla"],
            "publications": ["journal", "article", "manuscript", "publication", "abstract"],
            "educational": ["patient", "education", "training", "guideline", "information"],
            "safety": ["safety", "adverse", "pharmacovigilance", "risk", "signal"],
            "commercial": ["medical affairs", "msl", "commercial", "marketing"]
        }
        
        for doc_type, keywords in document_indicators.items():
            if any(keyword in content_lower for keyword in keywords):
                return doc_type
        
        return "general_medical"
    
    def _identify_therapeutic_area(self, content: str) -> str:
        """Identify the therapeutic area"""
        content_lower = content.lower()
        
        therapeutic_indicators = {
            "oncology": ["cancer", "tumor", "oncology", "chemotherapy", "radiation", "immunotherapy"],
            "cardiology": ["heart", "cardiac", "cardiovascular", "hypertension", "coronary"],
            "neurology": ["brain", "neurological", "alzheimer", "parkinson", "epilepsy", "stroke"],
            "infectious_disease": ["infection", "antibiotic", "antiviral", "vaccine", "pathogen"],
            "endocrinology": ["diabetes", "insulin", "hormone", "thyroid", "metabolic"],
            "immunology": ["immune", "autoimmune", "rheumatoid", "lupus", "inflammatory"],
            "respiratory": ["lung", "asthma", "copd", "respiratory", "pulmonary"],
            "rare_diseases": ["rare", "orphan", "genetic", "inherited", "syndrome"]
        }
        
        for area, keywords in therapeutic_indicators.items():
            if any(keyword in content_lower for keyword in keywords):
                return area
        
        return "general_medicine"
    
    def _identify_regulatory_context(self, content: str) -> str:
        """Identify regulatory context"""
        content_lower = content.lower()
        
        if any(term in content_lower for term in ["fda", "united states", "us", "america"]):
            return "fda"
        elif any(term in content_lower for term in ["ema", "europe", "eu", "european"]):
            return "ema"
        elif any(term in content_lower for term in ["ich", "international", "global"]):
            return "ich"
        else:
            return "general"
    
    def _identify_target_audience(self, content: str) -> str:
        """Identify target audience"""
        content_lower = content.lower()
        
        if any(term in content_lower for term in ["physician", "doctor", "healthcare professional", "clinician"]):
            return "healthcare_professionals"
        elif any(term in content_lower for term in ["patient", "consumer", "public"]):
            return "patients"
        elif any(term in content_lower for term in ["regulatory", "authority", "agency"]):
            return "regulatory_authorities"
        elif any(term in content_lower for term in ["scientific", "research", "academic"]):
            return "scientific_community"
        else:
            return "general_medical"
    
    def _assess_evidence_requirements(self, content: str) -> str:
        """Assess evidence level requirements"""
        content_lower = content.lower()
        
        if any(term in content_lower for term in ["systematic review", "meta-analysis", "cochrane"]):
            return "systematic_review"
        elif any(term in content_lower for term in ["randomized", "rct", "controlled trial"]):
            return "rct"
        elif any(term in content_lower for term in ["cohort", "longitudinal", "prospective"]):
            return "observational"
        else:
            return "general_evidence"
    
    async def _create_clinical_document(self, task_request: TaskRequest, medical_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create clinical research document"""
        # Use clinical document creation tool
        creation_tool = ClinicalDocumentCreationTool()
        
        document_result = creation_tool._run(
            document_type=medical_analysis["document_type"],
            therapeutic_area=medical_analysis["therapeutic_area"],
            requirements=task_request.metadata
        )
        
        if "error" in document_result:
            raise Exception(document_result["error"])
        
        # Create comprehensive clinical document
        clinical_document = f"""
        {document_result['content']}
        
        REGULATORY COMPLIANCE:
        {chr(10).join(f"• {element}" for element in document_result['regulatory_elements'])}
        
        EVIDENCE FRAMEWORK:
        Literature Search: {document_result['evidence_framework']['literature_search']['search_strategy']}
        Evidence Hierarchy: {', '.join(document_result['evidence_framework']['evidence_hierarchy'].keys())}
        Statistical Considerations: {document_result['evidence_framework']['statistical_considerations']['analysis_plan']}
        
        QUALITY ASSURANCE:
        • Medical accuracy review required
        • Regulatory compliance verification
        • Statistical analysis validation
        • Clinical significance assessment
        """
        
        return {
            "content": clinical_document,
            "metadata": {
                "document_type": medical_analysis["document_type"],
                "therapeutic_area": medical_analysis["therapeutic_area"],
                "regulatory_context": medical_analysis["regulatory_context"],
                "evidence_level": medical_analysis["evidence_level"],
                "structure": document_result["structure"],
                "compliance_elements": document_result["regulatory_elements"]
            },
            "confidence_score": document_result["confidence_score"]
        }
    
    async def _conduct_literature_review(self, task_request: TaskRequest, medical_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct systematic literature review"""
        # Use literature analysis tool
        literature_tool = MedicalLiteratureAnalysisTool()
        
        # Extract research question from content
        research_question = task_request.content
        
        literature_result = literature_tool._run(
            research_question=research_question,
            therapeutic_area=medical_analysis["therapeutic_area"],
            study_types=["systematic_review", "rct", "cohort", "case_control"]
        )
        
        if "error" in literature_result:
            raise Exception(literature_result["error"])
        
        # Create comprehensive literature review
        literature_review = f"""
        SYSTEMATIC LITERATURE REVIEW
        
        RESEARCH QUESTION: {research_question}
        THERAPEUTIC AREA: {medical_analysis['therapeutic_area']}
        
        SEARCH STRATEGY:
        PICO Framework:
        • Population: {literature_result['search_strategy']['pico_framework']['population']}
        • Intervention: {literature_result['search_strategy']['pico_framework']['intervention']}
        • Comparator: {literature_result['search_strategy']['pico_framework']['comparator']}
        • Outcomes: {literature_result['search_strategy']['pico_framework']['outcomes']}
        
        Databases: {', '.join(literature_result['search_strategy']['databases'])}
        
        EVIDENCE SYNTHESIS:
        Overall Quality: {literature_result['evidence_synthesis']['overall_quality']}
        Consistency: {literature_result['evidence_synthesis']['consistency']}
        Applicability: {literature_result['evidence_synthesis']['applicability']}
        
        QUALITY ASSESSMENT:
        Framework: GRADE and Cochrane Risk of Bias
        Assessment: {literature_result['quality_assessment']['overall_assessment']}
        
        CLINICAL RECOMMENDATIONS:
        {chr(10).join(literature_result['recommendations'])}
        """
        
        return {
            "content": literature_review,
            "metadata": {
                "research_question": research_question,
                "therapeutic_area": medical_analysis["therapeutic_area"],
                "search_strategy": literature_result["search_strategy"],
                "evidence_quality": literature_result["quality_assessment"]["overall_assessment"],
                "review_type": "systematic_literature_review"
            },
            "confidence_score": literature_result["confidence_score"]
        }
    
    async def _create_medical_publication(self, task_request: TaskRequest, medical_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create medical publication manuscript"""
        # Create CrewAI task for medical publication
        publication_task = Task(
            description=f"""
            Create a high-quality medical publication manuscript for the following:
            
            Content: {task_request.content}
            Document Type: {medical_analysis['document_type']}
            Therapeutic Area: {medical_analysis['therapeutic_area']}
            Target Audience: {medical_analysis['target_audience']}
            Evidence Level: {medical_analysis['evidence_level']}
            
            Apply the medical writing framework:
            {MEDICAL_EXPERT_PROMPTS['medical_writing_framework']}
            
            Ensure compliance with:
            • ICMJE guidelines for authorship and publication
            • CONSORT, STROBE, or PRISMA guidelines as appropriate
            • Journal-specific requirements and formatting
            • Evidence-based medicine principles
            • Ethical considerations and conflict of interest disclosure
            
            Create a publication-ready manuscript with proper structure,
            evidence-based content, and adherence to medical writing standards.
            """,
            agent=self.crew_agent,
            expected_output="High-quality medical publication manuscript ready for journal submission"
        )
        
        # Execute task
        result = await asyncio.to_thread(publication_task.execute)
        
        return {
            "content": result,
            "metadata": {
                "document_type": medical_analysis["document_type"],
                "therapeutic_area": medical_analysis["therapeutic_area"],
                "target_audience": medical_analysis["target_audience"],
                "publication_type": "journal_manuscript",
                "guidelines_compliance": ["ICMJE", "CONSORT/STROBE/PRISMA"]
            },
            "confidence_score": 0.9
        }
    
    async def _create_regulatory_submission(self, task_request: TaskRequest, medical_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create regulatory submission document"""
        regulatory_context = medical_analysis["regulatory_context"]
        therapeutic_area = medical_analysis["therapeutic_area"]
        
        # Create regulatory submission based on context
        regulatory_submission = f"""
        REGULATORY SUBMISSION DOCUMENT
        
        REGULATORY CONTEXT: {regulatory_context.upper()}
        THERAPEUTIC AREA: {therapeutic_area}
        
        EXECUTIVE SUMMARY:
        Product Overview: [Investigational medicinal product description]
        Indication: [Proposed therapeutic indication]
        Development Status: [Current development phase and status]
        Regulatory Pathway: [Proposed regulatory pathway and timeline]
        
        BENEFIT-RISK ASSESSMENT:
        Clinical Benefits: [Demonstrated clinical efficacy and benefits]
        Safety Profile: [Comprehensive safety evaluation]
        Risk Mitigation: [Risk management and mitigation strategies]
        Overall Assessment: [Favorable benefit-risk profile]
        
        REGULATORY COMPLIANCE:
        • {regulatory_context.upper()} guidelines adherence
        • ICH harmonized standards compliance
        • Good Clinical Practice (GCP) compliance
        • Quality by Design (QbD) principles
        • Risk-based approach to development
        
        SUPPORTING DOCUMENTATION:
        • Clinical study reports and data tabulations
        • Integrated summaries of efficacy and safety
        • Risk management plan and pharmacovigilance
        • Quality documentation and manufacturing information
        • Nonclinical studies and literature review
        
        REGULATORY STRATEGY:
        • Pre-submission meetings and scientific advice
        • Regulatory milestone planning and timeline
        • Post-marketing commitments and requirements
        • Global regulatory harmonization considerations
        """
        
        return {
            "content": regulatory_submission,
            "metadata": {
                "regulatory_context": regulatory_context,
                "therapeutic_area": therapeutic_area,
                "submission_type": "regulatory_filing",
                "compliance_standards": ["ICH", "GCP", "QbD"],
                "document_type": medical_analysis["document_type"]
            },
            "confidence_score": 0.85
        }
    
    async def _general_medical_assistance(self, task_request: TaskRequest, medical_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Provide general medical writing assistance"""
        # Create CrewAI task for general medical assistance
        medical_task = Task(
            description=f"""
            Provide expert medical writing assistance for the following request:
            
            Content: {task_request.content}
            Document Type: {medical_analysis['document_type']}
            Therapeutic Area: {medical_analysis['therapeutic_area']}
            Target Audience: {medical_analysis['target_audience']}
            Regulatory Context: {medical_analysis['regulatory_context']}
            
            Apply the medical writing framework:
            {MEDICAL_EXPERT_PROMPTS['medical_writing_framework']}
            
            Ensure:
            • Scientific accuracy and evidence-based content
            • Appropriate medical terminology and nomenclature
            • Regulatory compliance and ethical considerations
            • Clear communication appropriate for target audience
            • Professional medical writing standards
            
            Provide comprehensive medical writing guidance with practical
            recommendations and adherence to best practices.
            """,
            agent=self.crew_agent,
            expected_output="Expert medical writing assistance with professional guidance"
        )
        
        # Execute task
        result = await asyncio.to_thread(medical_task.execute)
        
        return {
            "content": result,
            "metadata": {
                "document_type": medical_analysis["document_type"],
                "therapeutic_area": medical_analysis["therapeutic_area"],
                "target_audience": medical_analysis["target_audience"],
                "assistance_type": "general_medical_writing"
            },
            "confidence_score": 0.85
        }
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get medical expert capabilities"""
        return {
            "agent_type": "medical_expert",
            "expertise_areas": self.expertise_areas,
            "therapeutic_areas": self.therapeutic_areas,
            "document_types": list(MEDICAL_EXPERT_PROMPTS["medical_document_types"].keys()),
            "regulatory_standards": list(MEDICAL_EXPERT_PROMPTS["regulatory_standards"].keys()),
            "tools": [tool.name for tool in self.medical_tools],
            "performance_metrics": await self.get_performance_metrics()
        }
    
    async def get_medical_templates(self) -> Dict[str, Any]:
        """Get available medical document templates"""
        return {
            "clinical_research_templates": [
                "Clinical Study Protocol", "Clinical Study Report", "Investigator Brochure",
                "Clinical Overview", "Clinical Summary", "Study Synopsis"
            ],
            "regulatory_templates": [
                "CTD Module 2 Summaries", "FDA IND/NDA Submissions", "EMA Marketing Authorization",
                "Risk Management Plan", "Periodic Safety Update Report"
            ],
            "publication_templates": [
                "Journal Article Manuscript", "Conference Abstract", "Poster Presentation",
                "Case Report", "Review Article", "Meta-Analysis"
            ],
            "safety_templates": [
                "Pharmacovigilance Report", "Safety Update Report", "Risk Assessment",
                "Signal Detection Report", "Benefit-Risk Evaluation"
            ],
            "educational_templates": [
                "Patient Information Leaflet", "Healthcare Provider Education", "Medical Training Material",
                "Clinical Guidelines", "Treatment Protocol"
            ]
        }

