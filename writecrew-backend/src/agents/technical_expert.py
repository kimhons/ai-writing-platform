"""
Technical Writing Expert Agent - Specialized technical documentation and engineering communication
Part of WriteCrew Multi-Agentic AI Writing System

This agent specializes in technical writing, software documentation, API guides, engineering specifications,
user manuals, and professional technical communication with industry standards and best practices.
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

# Technical Writing Expert Prompts
TECHNICAL_EXPERT_PROMPTS = {
    "backstory": """You are a distinguished technical writing expert with over 12 years of experience 
    in software documentation, API documentation, engineering specifications, and technical communication. 
    You have worked with leading technology companies, software development teams, engineering firms, 
    and technical product organizations across various industries.

    Your expertise spans software documentation, API guides, user manuals, technical specifications, 
    system architecture documents, installation guides, troubleshooting documentation, and developer 
    resources. You are well-versed in documentation frameworks like Docs-as-Code, GitBook, Confluence, 
    and modern documentation tools and methodologies.

    You are known for your ability to translate complex technical concepts into clear, actionable 
    documentation that serves diverse audiences from end users to developers to system administrators. 
    Your writing emphasizes clarity, accuracy, completeness, and usability.

    Your documentation is characterized by logical structure, comprehensive coverage, practical examples, 
    and user-centered design. You always consider the user journey, information architecture, and 
    accessibility principles in your technical communication.""",

    "technical_document_types": {
        "software_documentation": "User guides, admin guides, installation manuals, configuration guides, release notes",
        "api_documentation": "API references, developer guides, SDK documentation, integration guides, code examples",
        "engineering_specs": "Technical specifications, system architecture, design documents, requirements documents",
        "user_manuals": "Product manuals, how-to guides, tutorials, quick start guides, troubleshooting guides",
        "process_documentation": "SOPs, workflows, procedures, best practices, compliance documentation",
        "training_materials": "Technical training guides, certification materials, learning resources, workshops",
        "maintenance_docs": "Maintenance manuals, service guides, repair procedures, diagnostic guides",
        "compliance_docs": "Standards compliance, regulatory documentation, audit procedures, quality assurance"
    },

    "technical_writing_framework": """
    1. AUDIENCE ANALYSIS
       - Identify primary and secondary audiences (end users, developers, administrators, managers)
       - Assess technical expertise levels and knowledge gaps
       - Determine user goals, tasks, and pain points
       - Consider cultural and linguistic diversity

    2. INFORMATION ARCHITECTURE
       - Organize content logically with clear hierarchy
       - Design intuitive navigation and cross-references
       - Create comprehensive table of contents and index
       - Implement effective search and findability features

    3. CONTENT STRATEGY
       - Task-oriented approach with clear objectives
       - Step-by-step procedures with decision points
       - Comprehensive examples and use cases
       - Error handling and troubleshooting guidance

    4. TECHNICAL ACCURACY
       - Verify all technical information and procedures
       - Test all code examples and configurations
       - Validate system requirements and compatibility
       - Ensure version control and update procedures

    5. USABILITY AND ACCESSIBILITY
       - Clear, concise language with consistent terminology
       - Visual design principles and information hierarchy
       - Accessibility compliance (WCAG guidelines)
       - Multi-format delivery (web, PDF, mobile)
    """,

    "documentation_standards": {
        "style_guides": "Microsoft Manual of Style, Google Developer Documentation Style Guide, Apple Style Guide",
        "markup_languages": "Markdown, reStructuredText, AsciiDoc, DocBook, HTML/CSS",
        "documentation_tools": "GitBook, Confluence, Notion, Sphinx, MkDocs, Docusaurus, Jekyll",
        "version_control": "Git-based documentation, docs-as-code, continuous integration/deployment"
    },

    "technical_domains": {
        "software_development": "Programming languages, frameworks, libraries, development tools, DevOps",
        "cloud_computing": "AWS, Azure, GCP, containerization, microservices, serverless architecture",
        "data_engineering": "Databases, data pipelines, analytics, machine learning, big data technologies",
        "cybersecurity": "Security protocols, compliance frameworks, threat analysis, incident response",
        "networking": "Network protocols, infrastructure, telecommunications, IoT, edge computing",
        "hardware_engineering": "Electronic systems, embedded systems, manufacturing, testing procedures",
        "enterprise_software": "ERP systems, CRM platforms, business intelligence, workflow automation",
        "mobile_development": "iOS, Android, cross-platform development, mobile app deployment"
    }
}

class TechnicalDocumentCreationTool(BaseTool):
    """Tool for creating comprehensive technical documentation"""
    
    name: str = "technical_document_creation"
    description: str = "Create comprehensive technical documentation with proper structure and standards"
    
    def _run(self, document_type: str, technical_domain: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create technical document based on type and domain"""
        try:
            # Document type validation
            valid_types = list(TECHNICAL_EXPERT_PROMPTS["technical_document_types"].keys())
            if document_type not in valid_types:
                return {"error": f"Invalid document type. Valid types: {valid_types}"}
            
            # Generate document structure
            document_structure = self._generate_technical_structure(document_type, technical_domain)
            
            # Create document content
            document_content = self._create_technical_content(document_type, technical_domain, requirements)
            
            # Add technical standards and best practices
            technical_standards = self._add_technical_standards(document_type, technical_domain)
            
            # Create examples and code samples
            examples_framework = self._create_examples_framework(document_type, technical_domain)
            
            return {
                "document_type": document_type,
                "technical_domain": technical_domain,
                "structure": document_structure,
                "content": document_content,
                "technical_standards": technical_standards,
                "examples_framework": examples_framework,
                "confidence_score": self._calculate_technical_confidence(document_type, technical_domain, requirements)
            }
            
        except Exception as e:
            return {"error": f"Technical document creation failed: {str(e)}"}
    
    def _generate_technical_structure(self, document_type: str, technical_domain: str) -> Dict[str, Any]:
        """Generate appropriate technical document structure"""
        structures = {
            "software_documentation": {
                "user_guide": ["Introduction", "Getting Started", "Installation", "Configuration", 
                             "User Interface", "Features", "Tutorials", "Troubleshooting", 
                             "FAQ", "Glossary", "Appendices"],
                "admin_guide": ["Overview", "System Requirements", "Installation", "Configuration", 
                              "User Management", "Security", "Maintenance", "Monitoring", 
                              "Backup and Recovery", "Troubleshooting"],
                "required_elements": ["Prerequisites", "Step-by-step procedures", "Screenshots", "Code examples"]
            },
            "api_documentation": {
                "sections": ["Overview", "Authentication", "Endpoints", "Request/Response Examples", 
                           "Error Codes", "Rate Limiting", "SDKs", "Tutorials", "Changelog"],
                "endpoint_structure": ["Description", "Parameters", "Request Example", "Response Example", 
                                     "Error Responses", "Code Samples"],
                "required_elements": ["Interactive examples", "Code samples", "Error handling", "Rate limits"]
            },
            "engineering_specs": {
                "sections": ["Executive Summary", "System Overview", "Requirements", "Architecture", 
                           "Design Details", "Implementation", "Testing", "Deployment", 
                           "Maintenance", "References"],
                "technical_details": ["Functional requirements", "Non-functional requirements", 
                                    "System architecture", "Interface specifications"],
                "required_elements": ["Technical diagrams", "Performance criteria", "Compliance requirements"]
            },
            "user_manuals": {
                "sections": ["Introduction", "Safety Information", "Setup", "Operation", 
                           "Maintenance", "Troubleshooting", "Specifications", "Warranty"],
                "task_oriented": ["Quick start guide", "Common tasks", "Advanced features", 
                                "Problem resolution"],
                "required_elements": ["Visual aids", "Safety warnings", "Step-by-step procedures"]
            }
        }
        
        return structures.get(document_type, {
            "sections": ["Introduction", "Main Content", "Reference"],
            "required_elements": ["Clear structure", "Practical examples"]
        })
    
    def _create_technical_content(self, document_type: str, technical_domain: str, requirements: Dict[str, Any]) -> str:
        """Create technical document content based on type and domain"""
        content_templates = {
            "software_documentation": f"""
            SOFTWARE DOCUMENTATION
            
            # Introduction
            This documentation provides comprehensive guidance for using [SOFTWARE NAME] 
            in the {technical_domain} domain.
            
            ## Overview
            [Software description and key features]
            
            ## Target Audience
            - End users seeking to accomplish specific tasks
            - System administrators managing the software
            - Developers integrating with the system
            
            # Getting Started
            
            ## System Requirements
            - Operating System: [Requirements]
            - Hardware: [Minimum specifications]
            - Dependencies: [Required software/libraries]
            
            ## Installation
            ### Step 1: Download
            ```bash
            # Download command or instructions
            wget https://example.com/software.tar.gz
            ```
            
            ### Step 2: Install
            ```bash
            # Installation commands
            tar -xzf software.tar.gz
            cd software
            ./install.sh
            ```
            
            ## Configuration
            [Configuration steps and examples]
            
            # User Guide
            [Detailed usage instructions based on requirements: {requirements}]
            [Domain-specific features for: {technical_domain}]
            """,
            
            "api_documentation": f"""
            API DOCUMENTATION
            
            # Overview
            The {technical_domain} API provides programmatic access to [SERVICE NAME] functionality.
            
            ## Base URL
            ```
            https://api.example.com/v1
            ```
            
            ## Authentication
            All API requests require authentication using API keys:
            
            ```bash
            curl -H "Authorization: Bearer YOUR_API_KEY" \\
                 https://api.example.com/v1/endpoint
            ```
            
            # Endpoints
            
            ## GET /users
            Retrieve a list of users.
            
            ### Parameters
            | Parameter | Type | Required | Description |
            |-----------|------|----------|-------------|
            | limit | integer | No | Number of results (default: 10) |
            | offset | integer | No | Pagination offset (default: 0) |
            
            ### Request Example
            ```bash
            curl -X GET "https://api.example.com/v1/users?limit=20" \\
                 -H "Authorization: Bearer YOUR_API_KEY"
            ```
            
            ### Response Example
            ```json
            {{
              "users": [
                {{
                  "id": 1,
                  "name": "John Doe",
                  "email": "john@example.com"
                }}
              ],
              "total": 100,
              "limit": 20,
              "offset": 0
            }}
            ```
            
            [Additional endpoints based on requirements: {requirements}]
            [Domain-specific API features for: {technical_domain}]
            """,
            
            "engineering_specs": f"""
            TECHNICAL SPECIFICATION
            
            # Executive Summary
            This document specifies the technical requirements and design for [SYSTEM NAME] 
            in the {technical_domain} domain.
            
            ## Project Overview
            [Project description and objectives]
            
            ## Scope
            [What is included and excluded from this specification]
            
            # System Overview
            
            ## Architecture
            [High-level system architecture description]
            
            ## Key Components
            - Component 1: [Description and responsibility]
            - Component 2: [Description and responsibility]
            - Component 3: [Description and responsibility]
            
            # Requirements
            
            ## Functional Requirements
            ### FR-001: [Requirement Name]
            **Description:** [Detailed requirement description]
            **Priority:** High/Medium/Low
            **Acceptance Criteria:**
            - Criterion 1
            - Criterion 2
            - Criterion 3
            
            ## Non-Functional Requirements
            ### NFR-001: Performance
            - Response time: < 200ms for 95% of requests
            - Throughput: 1000 requests per second
            - Availability: 99.9% uptime
            
            ### NFR-002: Security
            - Data encryption at rest and in transit
            - Authentication and authorization
            - Audit logging and monitoring
            
            # Design Details
            [Detailed design based on requirements: {requirements}]
            [Domain-specific considerations for: {technical_domain}]
            """
        }
        
        return content_templates.get(document_type, f"Technical document content for {document_type} in {technical_domain}")
    
    def _add_technical_standards(self, document_type: str, technical_domain: str) -> List[str]:
        """Add appropriate technical standards and best practices"""
        standards = {
            "software_documentation": [
                "Microsoft Manual of Style compliance", "Consistent terminology and glossary",
                "Task-oriented structure", "Progressive disclosure", "Accessibility (WCAG 2.1)",
                "Version control and change tracking", "User feedback integration"
            ],
            "api_documentation": [
                "OpenAPI/Swagger specification", "RESTful API design principles",
                "Consistent error handling", "Rate limiting documentation", "SDK code examples",
                "Interactive API explorer", "Comprehensive testing examples"
            ],
            "engineering_specs": [
                "IEEE standards compliance", "Requirements traceability", "Design rationale documentation",
                "Performance benchmarks", "Security considerations", "Maintainability guidelines",
                "Change management procedures"
            ],
            "user_manuals": [
                "Task-oriented organization", "Progressive complexity", "Visual design principles",
                "Safety and warning standards", "Accessibility compliance", "Multi-language support",
                "User testing and validation"
            ]
        }
        
        domain_standards = {
            "software_development": ["Coding standards", "Documentation as code", "CI/CD integration"],
            "cloud_computing": ["Cloud security standards", "Scalability guidelines", "Cost optimization"],
            "cybersecurity": ["Security frameworks", "Compliance requirements", "Incident response"],
            "data_engineering": ["Data governance", "Privacy regulations", "Performance optimization"]
        }
        
        result = standards.get(document_type, ["General technical writing standards"])
        if technical_domain in domain_standards:
            result.extend(domain_standards[technical_domain])
        
        return result
    
    def _create_examples_framework(self, document_type: str, technical_domain: str) -> Dict[str, Any]:
        """Create comprehensive examples and code samples framework"""
        return {
            "code_examples": {
                "languages": self._get_relevant_languages(technical_domain),
                "example_types": ["Basic usage", "Advanced scenarios", "Error handling", "Best practices"],
                "code_standards": ["Syntax highlighting", "Copy-to-clipboard", "Runnable examples", "Comments"]
            },
            "visual_aids": {
                "diagrams": ["Architecture diagrams", "Flow charts", "Sequence diagrams", "Network diagrams"],
                "screenshots": ["UI screenshots", "Configuration screens", "Error messages", "Results"],
                "videos": ["Tutorial videos", "Demo recordings", "Walkthrough guides"]
            },
            "interactive_elements": {
                "tutorials": ["Step-by-step guides", "Hands-on exercises", "Sandbox environments"],
                "tools": ["Code generators", "Configuration wizards", "Testing utilities"],
                "feedback": ["User ratings", "Comments", "Improvement suggestions"]
            },
            "real_world_scenarios": {
                "use_cases": ["Common scenarios", "Edge cases", "Integration examples"],
                "case_studies": ["Success stories", "Implementation examples", "Lessons learned"],
                "troubleshooting": ["Common problems", "Diagnostic procedures", "Solution guides"]
            }
        }
    
    def _get_relevant_languages(self, technical_domain: str) -> List[str]:
        """Get relevant programming languages for the technical domain"""
        domain_languages = {
            "software_development": ["Python", "JavaScript", "Java", "C#", "Go", "Rust"],
            "cloud_computing": ["Python", "JavaScript", "Go", "Terraform", "YAML", "JSON"],
            "data_engineering": ["Python", "SQL", "Scala", "R", "Java", "Spark"],
            "cybersecurity": ["Python", "PowerShell", "Bash", "C", "Assembly"],
            "mobile_development": ["Swift", "Kotlin", "JavaScript", "Dart", "C#"],
            "web_development": ["JavaScript", "TypeScript", "Python", "PHP", "Ruby"]
        }
        
        return domain_languages.get(technical_domain, ["Python", "JavaScript", "Bash"])
    
    def _calculate_technical_confidence(self, document_type: str, technical_domain: str, requirements: Dict[str, Any]) -> float:
        """Calculate confidence score for technical document"""
        base_confidence = 0.85
        
        # Adjust based on document complexity
        complexity_factors = {
            "software_documentation": 0.9,
            "api_documentation": 0.95,
            "engineering_specs": 0.8,
            "user_manuals": 0.9,
            "process_documentation": 0.85
        }
        
        # Adjust based on technical domain familiarity
        domain_factors = {
            "software_development": 0.95,
            "cloud_computing": 0.9,
            "data_engineering": 0.85,
            "cybersecurity": 0.8,
            "mobile_development": 0.9
        }
        
        complexity_adjustment = complexity_factors.get(document_type, 0.85)
        domain_adjustment = domain_factors.get(technical_domain, 0.85)
        
        # Adjust based on requirements completeness
        requirements_completeness = min(len(requirements) / 6, 1.0)  # Assume 6 is ideal
        
        final_confidence = base_confidence * complexity_adjustment * domain_adjustment * requirements_completeness
        return round(min(final_confidence, 0.95), 2)

class APIDocumentationTool(BaseTool):
    """Tool for creating comprehensive API documentation"""
    
    name: str = "api_documentation_creation"
    description: str = "Create comprehensive API documentation with interactive examples"
    
    def _run(self, api_type: str, endpoints: List[Dict[str, Any]], authentication: str = "api_key") -> Dict[str, Any]:
        """Create API documentation based on endpoints and specifications"""
        try:
            # Generate API overview
            api_overview = self._generate_api_overview(api_type, authentication)
            
            # Create endpoint documentation
            endpoint_docs = self._create_endpoint_documentation(endpoints)
            
            # Generate code examples
            code_examples = self._generate_code_examples(endpoints, authentication)
            
            # Create error handling guide
            error_guide = self._create_error_handling_guide()
            
            # Generate SDK documentation
            sdk_docs = self._generate_sdk_documentation(api_type)
            
            return {
                "api_type": api_type,
                "authentication": authentication,
                "overview": api_overview,
                "endpoints": endpoint_docs,
                "code_examples": code_examples,
                "error_guide": error_guide,
                "sdk_documentation": sdk_docs,
                "confidence_score": self._calculate_api_confidence(api_type, endpoints)
            }
            
        except Exception as e:
            return {"error": f"API documentation creation failed: {str(e)}"}
    
    def _generate_api_overview(self, api_type: str, authentication: str) -> Dict[str, Any]:
        """Generate comprehensive API overview"""
        return {
            "introduction": f"Comprehensive {api_type} API for developers",
            "base_url": "https://api.example.com/v1",
            "authentication": {
                "type": authentication,
                "description": self._get_auth_description(authentication),
                "example": self._get_auth_example(authentication)
            },
            "rate_limiting": {
                "requests_per_minute": 1000,
                "requests_per_hour": 10000,
                "headers": ["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"]
            },
            "response_format": "JSON",
            "versioning": "URL versioning (v1, v2, etc.)",
            "support": {
                "documentation": "https://docs.example.com",
                "support_email": "api-support@example.com",
                "status_page": "https://status.example.com"
            }
        }
    
    def _get_auth_description(self, auth_type: str) -> str:
        """Get authentication description"""
        descriptions = {
            "api_key": "API key authentication via Authorization header",
            "oauth2": "OAuth 2.0 authentication with bearer tokens",
            "jwt": "JSON Web Token authentication",
            "basic": "HTTP Basic authentication"
        }
        return descriptions.get(auth_type, "Authentication required")
    
    def _get_auth_example(self, auth_type: str) -> str:
        """Get authentication example"""
        examples = {
            "api_key": 'curl -H "Authorization: Bearer YOUR_API_KEY"',
            "oauth2": 'curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN"',
            "jwt": 'curl -H "Authorization: Bearer YOUR_JWT_TOKEN"',
            "basic": 'curl -u "username:password"'
        }
        return examples.get(auth_type, 'curl -H "Authorization: Bearer TOKEN"')
    
    def _create_endpoint_documentation(self, endpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create detailed endpoint documentation"""
        endpoint_docs = []
        
        for endpoint in endpoints:
            doc = {
                "method": endpoint.get("method", "GET"),
                "path": endpoint.get("path", "/"),
                "summary": endpoint.get("summary", "API endpoint"),
                "description": endpoint.get("description", "Detailed endpoint description"),
                "parameters": self._format_parameters(endpoint.get("parameters", [])),
                "request_example": self._generate_request_example(endpoint),
                "response_example": self._generate_response_example(endpoint),
                "error_responses": self._generate_error_responses(),
                "code_samples": self._generate_endpoint_code_samples(endpoint)
            }
            endpoint_docs.append(doc)
        
        return endpoint_docs
    
    def _format_parameters(self, parameters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format parameter documentation"""
        formatted_params = []
        
        for param in parameters:
            formatted_param = {
                "name": param.get("name", "parameter"),
                "type": param.get("type", "string"),
                "required": param.get("required", False),
                "description": param.get("description", "Parameter description"),
                "example": param.get("example", "example_value"),
                "constraints": param.get("constraints", {})
            }
            formatted_params.append(formatted_param)
        
        return formatted_params
    
    def _generate_request_example(self, endpoint: Dict[str, Any]) -> str:
        """Generate request example for endpoint"""
        method = endpoint.get("method", "GET")
        path = endpoint.get("path", "/")
        
        if method == "GET":
            return f'''curl -X GET "https://api.example.com/v1{path}" \\
     -H "Authorization: Bearer YOUR_API_KEY" \\
     -H "Content-Type: application/json"'''
        else:
            return f'''curl -X {method} "https://api.example.com/v1{path}" \\
     -H "Authorization: Bearer YOUR_API_KEY" \\
     -H "Content-Type: application/json" \\
     -d '{{"key": "value"}}\''''
    
    def _generate_response_example(self, endpoint: Dict[str, Any]) -> str:
        """Generate response example for endpoint"""
        return '''{
  "status": "success",
  "data": {
    "id": 123,
    "name": "Example Resource",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "meta": {
    "total": 1,
    "page": 1,
    "per_page": 10
  }
}'''
    
    def _generate_error_responses(self) -> List[Dict[str, Any]]:
        """Generate common error responses"""
        return [
            {
                "status_code": 400,
                "error": "Bad Request",
                "description": "Invalid request parameters",
                "example": '{"error": "Invalid parameter", "message": "The \'limit\' parameter must be between 1 and 100"}'
            },
            {
                "status_code": 401,
                "error": "Unauthorized",
                "description": "Authentication required",
                "example": '{"error": "Unauthorized", "message": "Invalid or missing API key"}'
            },
            {
                "status_code": 404,
                "error": "Not Found",
                "description": "Resource not found",
                "example": '{"error": "Not Found", "message": "The requested resource does not exist"}'
            },
            {
                "status_code": 429,
                "error": "Too Many Requests",
                "description": "Rate limit exceeded",
                "example": '{"error": "Rate Limit Exceeded", "message": "Too many requests. Please try again later."}'
            }
        ]
    
    def _generate_endpoint_code_samples(self, endpoint: Dict[str, Any]) -> Dict[str, str]:
        """Generate code samples for different languages"""
        method = endpoint.get("method", "GET")
        path = endpoint.get("path", "/")
        
        return {
            "python": f'''import requests

url = "https://api.example.com/v1{path}"
headers = {{
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}}

response = requests.{method.lower()}(url, headers=headers)
data = response.json()
print(data)''',
            
            "javascript": f'''const response = await fetch('https://api.example.com/v1{path}', {{
  method: '{method}',
  headers: {{
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
  }}
}});

const data = await response.json();
console.log(data);''',
            
            "curl": self._generate_request_example(endpoint)
        }
    
    def _generate_code_examples(self, endpoints: List[Dict[str, Any]], authentication: str) -> Dict[str, Any]:
        """Generate comprehensive code examples"""
        return {
            "quick_start": {
                "python": '''# Install the SDK
pip install example-api-sdk

# Quick start example
from example_api import Client

client = Client(api_key="YOUR_API_KEY")
result = client.get_data()
print(result)''',
                "javascript": '''// Install the SDK
npm install example-api-sdk

// Quick start example
const { Client } = require('example-api-sdk');

const client = new Client({ apiKey: 'YOUR_API_KEY' });
const result = await client.getData();
console.log(result);'''
            },
            "authentication_examples": self._generate_auth_examples(authentication),
            "error_handling": {
                "python": '''try:
    response = client.get_data()
except APIError as e:
    print(f"API Error: {e.status_code} - {e.message}")
except RateLimitError as e:
    print(f"Rate limit exceeded. Retry after: {e.retry_after}")''',
                "javascript": '''try {
  const response = await client.getData();
} catch (error) {
  if (error.status === 429) {
    console.log(`Rate limit exceeded. Retry after: ${error.retryAfter}`);
  } else {
    console.log(`API Error: ${error.status} - ${error.message}`);
  }
}'''
            }
        }
    
    def _generate_auth_examples(self, auth_type: str) -> Dict[str, str]:
        """Generate authentication examples"""
        examples = {
            "api_key": {
                "python": 'client = Client(api_key="YOUR_API_KEY")',
                "javascript": 'const client = new Client({ apiKey: "YOUR_API_KEY" });'
            },
            "oauth2": {
                "python": 'client = Client(access_token="YOUR_ACCESS_TOKEN")',
                "javascript": 'const client = new Client({ accessToken: "YOUR_ACCESS_TOKEN" });'
            }
        }
        return examples.get(auth_type, examples["api_key"])
    
    def _create_error_handling_guide(self) -> Dict[str, Any]:
        """Create comprehensive error handling guide"""
        return {
            "error_format": {
                "structure": "Consistent error response format",
                "example": '''{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    "field": "Additional error details"
  },
  "request_id": "unique_request_identifier"
}'''
            },
            "status_codes": {
                "2xx": "Success responses",
                "4xx": "Client errors (invalid request, authentication, etc.)",
                "5xx": "Server errors (internal server error, service unavailable)"
            },
            "retry_logic": {
                "exponential_backoff": "Implement exponential backoff for retries",
                "rate_limiting": "Respect rate limit headers and retry after specified time",
                "idempotency": "Use idempotency keys for safe retries"
            },
            "best_practices": [
                "Always check HTTP status codes",
                "Implement proper error handling for all API calls",
                "Log errors with request IDs for debugging",
                "Provide meaningful error messages to users",
                "Implement circuit breaker pattern for resilience"
            ]
        }
    
    def _generate_sdk_documentation(self, api_type: str) -> Dict[str, Any]:
        """Generate SDK documentation"""
        return {
            "available_sdks": {
                "python": {
                    "installation": "pip install example-api-sdk",
                    "documentation": "https://docs.example.com/python-sdk",
                    "github": "https://github.com/example/python-sdk"
                },
                "javascript": {
                    "installation": "npm install example-api-sdk",
                    "documentation": "https://docs.example.com/js-sdk",
                    "github": "https://github.com/example/js-sdk"
                },
                "go": {
                    "installation": "go get github.com/example/go-sdk",
                    "documentation": "https://docs.example.com/go-sdk",
                    "github": "https://github.com/example/go-sdk"
                }
            },
            "sdk_features": [
                "Automatic authentication handling",
                "Built-in retry logic with exponential backoff",
                "Request/response logging and debugging",
                "Type-safe API client with full IntelliSense support",
                "Comprehensive error handling and custom exceptions"
            ],
            "getting_started": {
                "installation": "Package manager installation instructions",
                "configuration": "API key and endpoint configuration",
                "first_request": "Making your first API request",
                "error_handling": "Handling errors and exceptions"
            }
        }
    
    def _calculate_api_confidence(self, api_type: str, endpoints: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for API documentation"""
        base_confidence = 0.9
        
        # Adjust based on number of endpoints
        endpoint_factor = min(len(endpoints) / 10, 1.0)  # Assume 10 endpoints is comprehensive
        
        # Adjust based on API type complexity
        api_complexity = {
            "rest": 0.95,
            "graphql": 0.85,
            "grpc": 0.8,
            "websocket": 0.8
        }
        
        complexity_adjustment = api_complexity.get(api_type, 0.9)
        
        final_confidence = base_confidence * endpoint_factor * complexity_adjustment
        return round(min(final_confidence, 0.95), 2)

class TechnicalExpertAgent(BaseAgent):
    """Technical Writing Expert Agent for specialized technical documentation and engineering communication"""
    
    def __init__(self, ai_provider_service: AIProviderService):
        super().__init__(
            agent_id="technical_expert",
            name="Technical Writing Expert",
            description="Specialized technical documentation and engineering communication expert",
            ai_provider_service=ai_provider_service
        )
        
        # Initialize specialized tools
        self.technical_tools = [
            TechnicalDocumentCreationTool(),
            APIDocumentationTool()
        ]
        
        # Technical expertise areas
        self.expertise_areas = [
            "software_documentation", "api_documentation", "engineering_specifications",
            "user_manuals", "process_documentation", "training_materials",
            "technical_communication", "information_architecture"
        ]
        
        # Technical domains
        self.technical_domains = list(TECHNICAL_EXPERT_PROMPTS["technical_domains"].keys())
        
        # Initialize CrewAI agent
        self._initialize_crew_agent()
    
    def _initialize_crew_agent(self):
        """Initialize the CrewAI agent with technical expertise"""
        self.crew_agent = Agent(
            role="Expert Technical Writer and Documentation Specialist",
            goal="Create clear, comprehensive technical documentation that serves diverse audiences effectively",
            backstory=TECHNICAL_EXPERT_PROMPTS["backstory"],
            tools=self.technical_tools,
            llm=self.ai_provider_service.get_primary_llm(),
            memory=True,
            verbose=True,
            allow_delegation=False
        )
    
    async def process_task(self, task_request: TaskRequest) -> TaskResponse:
        """Process technical writing task with specialized expertise"""
        try:
            self.logger.info(f"Processing technical writing task: {task_request.task_type}")
            
            # Validate technical task
            if not self._is_technical_task(task_request):
                return TaskResponse(
                    success=False,
                    error="Task is not suitable for technical writing expert",
                    agent_id=self.agent_id
                )
            
            # Determine technical context and requirements
            technical_analysis = await self._analyze_technical_requirements(task_request)
            
            # Process based on task type
            if task_request.task_type == "technical_documentation":
                result = await self._create_technical_documentation(task_request, technical_analysis)
            elif task_request.task_type == "api_documentation":
                result = await self._create_api_documentation(task_request, technical_analysis)
            elif task_request.task_type == "user_manual":
                result = await self._create_user_manual(task_request, technical_analysis)
            elif task_request.task_type == "engineering_spec":
                result = await self._create_engineering_specification(task_request, technical_analysis)
            else:
                result = await self._general_technical_assistance(task_request, technical_analysis)
            
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
            self.logger.error(f"Technical writing task failed: {str(e)}")
            await self._update_performance_metrics(False, task_request.task_type)
            
            return TaskResponse(
                success=False,
                error=f"Technical writing task failed: {str(e)}",
                agent_id=self.agent_id
            )
    
    def _is_technical_task(self, task_request: TaskRequest) -> bool:
        """Determine if task is suitable for technical expert"""
        technical_keywords = [
            "documentation", "manual", "guide", "api", "technical", "software",
            "system", "installation", "configuration", "troubleshooting", "specification",
            "architecture", "design", "implementation", "deployment", "maintenance",
            "tutorial", "how-to", "procedure", "workflow", "process", "engineering"
        ]
        
        content_lower = task_request.content.lower()
        return any(keyword in content_lower for keyword in technical_keywords)
    
    async def _analyze_technical_requirements(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Analyze technical requirements for the task"""
        technical_context = {
            "document_type": self._identify_technical_document_type(task_request.content),
            "technical_domain": self._identify_technical_domain(task_request.content),
            "target_audience": self._identify_technical_audience(task_request.content),
            "complexity_level": self._assess_technical_complexity(task_request.content),
            "output_format": self._determine_output_format(task_request.content)
        }
        
        return technical_context
    
    def _identify_technical_document_type(self, content: str) -> str:
        """Identify the type of technical document"""
        content_lower = content.lower()
        
        document_indicators = {
            "software_documentation": ["software", "application", "program", "user guide", "admin guide"],
            "api_documentation": ["api", "endpoint", "rest", "graphql", "sdk", "integration"],
            "engineering_specs": ["specification", "requirements", "architecture", "design", "system"],
            "user_manuals": ["manual", "instructions", "how-to", "tutorial", "guide"],
            "process_documentation": ["process", "procedure", "workflow", "sop", "standard"],
            "training_materials": ["training", "course", "learning", "education", "workshop"]
        }
        
        for doc_type, keywords in document_indicators.items():
            if any(keyword in content_lower for keyword in keywords):
                return doc_type
        
        return "general_technical"
    
    def _identify_technical_domain(self, content: str) -> str:
        """Identify the technical domain"""
        content_lower = content.lower()
        
        domain_indicators = {
            "software_development": ["programming", "coding", "development", "framework", "library"],
            "cloud_computing": ["cloud", "aws", "azure", "gcp", "kubernetes", "docker"],
            "data_engineering": ["data", "database", "analytics", "pipeline", "etl", "ml"],
            "cybersecurity": ["security", "encryption", "authentication", "firewall", "vulnerability"],
            "networking": ["network", "protocol", "tcp", "ip", "router", "switch"],
            "hardware_engineering": ["hardware", "circuit", "embedded", "electronics", "pcb"],
            "web_development": ["web", "html", "css", "javascript", "frontend", "backend"],
            "mobile_development": ["mobile", "ios", "android", "app", "smartphone"]
        }
        
        for domain, keywords in domain_indicators.items():
            if any(keyword in content_lower for keyword in keywords):
                return domain
        
        return "general_technology"
    
    def _identify_technical_audience(self, content: str) -> str:
        """Identify the target technical audience"""
        content_lower = content.lower()
        
        if any(term in content_lower for term in ["developer", "programmer", "engineer", "technical"]):
            return "developers"
        elif any(term in content_lower for term in ["admin", "administrator", "system", "ops"]):
            return "administrators"
        elif any(term in content_lower for term in ["user", "customer", "client", "end-user"]):
            return "end_users"
        elif any(term in content_lower for term in ["manager", "stakeholder", "executive", "business"]):
            return "business_users"
        else:
            return "general_technical"
    
    def _assess_technical_complexity(self, content: str) -> str:
        """Assess the technical complexity level"""
        content_lower = content.lower()
        
        complexity_indicators = {
            "advanced": ["advanced", "expert", "complex", "enterprise", "architecture", "optimization"],
            "intermediate": ["intermediate", "configuration", "integration", "customization"],
            "beginner": ["beginner", "basic", "introduction", "getting started", "simple", "quick start"]
        }
        
        for level, indicators in complexity_indicators.items():
            if any(indicator in content_lower for indicator in indicators):
                return level
        
        return "intermediate"
    
    def _determine_output_format(self, content: str) -> str:
        """Determine the preferred output format"""
        content_lower = content.lower()
        
        if any(term in content_lower for term in ["markdown", "md", "github"]):
            return "markdown"
        elif any(term in content_lower for term in ["html", "web", "online"]):
            return "html"
        elif any(term in content_lower for term in ["pdf", "print", "document"]):
            return "pdf"
        elif any(term in content_lower for term in ["confluence", "wiki"]):
            return "wiki"
        else:
            return "markdown"
    
    async def _create_technical_documentation(self, task_request: TaskRequest, technical_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive technical documentation"""
        # Use technical document creation tool
        creation_tool = TechnicalDocumentCreationTool()
        
        document_result = creation_tool._run(
            document_type=technical_analysis["document_type"],
            technical_domain=technical_analysis["technical_domain"],
            requirements=task_request.metadata
        )
        
        if "error" in document_result:
            raise Exception(document_result["error"])
        
        # Create comprehensive technical documentation
        technical_doc = f"""
        {document_result['content']}
        
        TECHNICAL STANDARDS:
        {chr(10).join(f"• {standard}" for standard in document_result['technical_standards'])}
        
        EXAMPLES AND CODE SAMPLES:
        Languages: {', '.join(document_result['examples_framework']['code_examples']['languages'])}
        Visual Aids: {', '.join(document_result['examples_framework']['visual_aids']['diagrams'])}
        Interactive Elements: {', '.join(document_result['examples_framework']['interactive_elements']['tutorials'])}
        
        QUALITY ASSURANCE:
        • Technical accuracy verification required
        • Code examples testing and validation
        • User experience testing with target audience
        • Accessibility compliance verification
        • Version control and change management
        """
        
        return {
            "content": technical_doc,
            "metadata": {
                "document_type": technical_analysis["document_type"],
                "technical_domain": technical_analysis["technical_domain"],
                "target_audience": technical_analysis["target_audience"],
                "complexity_level": technical_analysis["complexity_level"],
                "output_format": technical_analysis["output_format"],
                "structure": document_result["structure"],
                "standards": document_result["technical_standards"]
            },
            "confidence_score": document_result["confidence_score"]
        }
    
    async def _create_api_documentation(self, task_request: TaskRequest, technical_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive API documentation"""
        # Extract API information from request
        api_type = task_request.metadata.get("api_type", "rest")
        endpoints = task_request.metadata.get("endpoints", [])
        authentication = task_request.metadata.get("authentication", "api_key")
        
        # Use API documentation tool
        api_tool = APIDocumentationTool()
        
        api_result = api_tool._run(
            api_type=api_type,
            endpoints=endpoints,
            authentication=authentication
        )
        
        if "error" in api_result:
            raise Exception(api_result["error"])
        
        # Create comprehensive API documentation
        api_documentation = f"""
        API DOCUMENTATION
        
        {api_result['overview']['introduction']}
        
        BASE URL: {api_result['overview']['base_url']}
        
        AUTHENTICATION:
        Type: {api_result['authentication']}
        Description: {api_result['overview']['authentication']['description']}
        Example: {api_result['overview']['authentication']['example']}
        
        RATE LIMITING:
        • {api_result['overview']['rate_limiting']['requests_per_minute']} requests per minute
        • {api_result['overview']['rate_limiting']['requests_per_hour']} requests per hour
        • Headers: {', '.join(api_result['overview']['rate_limiting']['headers'])}
        
        ENDPOINTS:
        {chr(10).join(f"• {endpoint['method']} {endpoint['path']} - {endpoint['summary']}" 
                     for endpoint in api_result['endpoints'])}
        
        CODE EXAMPLES:
        Available in: Python, JavaScript, cURL
        Features: Authentication, error handling, rate limiting
        
        ERROR HANDLING:
        Comprehensive error response format with status codes and retry logic
        
        SDK SUPPORT:
        {chr(10).join(f"• {lang}: {info['installation']}" 
                     for lang, info in api_result['sdk_documentation']['available_sdks'].items())}
        """
        
        return {
            "content": api_documentation,
            "metadata": {
                "api_type": api_type,
                "authentication": authentication,
                "endpoints_count": len(endpoints),
                "technical_domain": technical_analysis["technical_domain"],
                "documentation_type": "api_reference",
                "interactive_features": ["code_examples", "error_handling", "sdk_support"]
            },
            "confidence_score": api_result["confidence_score"]
        }
    
    async def _create_user_manual(self, task_request: TaskRequest, technical_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive user manual"""
        # Create CrewAI task for user manual
        manual_task = Task(
            description=f"""
            Create a comprehensive user manual for the following:
            
            Content: {task_request.content}
            Technical Domain: {technical_analysis['technical_domain']}
            Target Audience: {technical_analysis['target_audience']}
            Complexity Level: {technical_analysis['complexity_level']}
            Output Format: {technical_analysis['output_format']}
            
            Apply the technical writing framework:
            {TECHNICAL_EXPERT_PROMPTS['technical_writing_framework']}
            
            Structure the manual with:
            • Clear introduction and overview
            • Step-by-step procedures with screenshots
            • Troubleshooting section with common issues
            • Glossary of technical terms
            • Quick reference guide
            
            Ensure the manual is:
            • Task-oriented and user-focused
            • Accessible to the target audience
            • Comprehensive yet easy to navigate
            • Includes visual aids and examples
            • Follows technical writing best practices
            """,
            agent=self.crew_agent,
            expected_output="Comprehensive user manual with clear procedures and visual aids"
        )
        
        # Execute task
        result = await asyncio.to_thread(manual_task.execute)
        
        return {
            "content": result,
            "metadata": {
                "document_type": "user_manual",
                "technical_domain": technical_analysis["technical_domain"],
                "target_audience": technical_analysis["target_audience"],
                "complexity_level": technical_analysis["complexity_level"],
                "manual_type": "comprehensive_user_guide"
            },
            "confidence_score": 0.9
        }
    
    async def _create_engineering_specification(self, task_request: TaskRequest, technical_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed engineering specification"""
        technical_domain = technical_analysis["technical_domain"]
        complexity_level = technical_analysis["complexity_level"]
        
        # Create engineering specification
        engineering_spec = f"""
        ENGINEERING SPECIFICATION
        
        DOCUMENT INFORMATION:
        Title: [System/Component Specification]
        Domain: {technical_domain}
        Complexity: {complexity_level}
        Version: 1.0
        Date: {datetime.now().strftime('%Y-%m-%d')}
        
        EXECUTIVE SUMMARY:
        [High-level overview of the system/component being specified]
        
        SYSTEM OVERVIEW:
        Purpose: [Primary purpose and objectives]
        Scope: [What is included and excluded]
        Stakeholders: [Key stakeholders and their interests]
        
        FUNCTIONAL REQUIREMENTS:
        FR-001: [Primary functional requirement]
        - Description: [Detailed description]
        - Priority: High
        - Acceptance Criteria: [Measurable criteria]
        
        FR-002: [Secondary functional requirement]
        - Description: [Detailed description]
        - Priority: Medium
        - Acceptance Criteria: [Measurable criteria]
        
        NON-FUNCTIONAL REQUIREMENTS:
        Performance:
        - Response time: [Specific metrics]
        - Throughput: [Capacity requirements]
        - Scalability: [Growth projections]
        
        Security:
        - Authentication: [Security mechanisms]
        - Authorization: [Access control]
        - Data protection: [Encryption and privacy]
        
        Reliability:
        - Availability: [Uptime requirements]
        - Fault tolerance: [Error handling]
        - Recovery: [Disaster recovery procedures]
        
        TECHNICAL ARCHITECTURE:
        System Architecture: [High-level architecture diagram]
        Component Design: [Detailed component specifications]
        Interface Specifications: [API and integration details]
        Data Model: [Database and data structure design]
        
        IMPLEMENTATION GUIDELINES:
        Development Standards: [Coding standards and practices]
        Testing Requirements: [Testing strategy and criteria]
        Deployment Procedures: [Deployment and configuration]
        Maintenance Procedures: [Ongoing maintenance requirements]
        
        COMPLIANCE AND STANDARDS:
        Industry Standards: [Relevant industry standards]
        Regulatory Requirements: [Compliance obligations]
        Quality Assurance: [QA processes and metrics]
        Documentation Standards: [Documentation requirements]
        
        APPENDICES:
        A. Glossary of Terms
        B. Reference Documents
        C. Technical Diagrams
        D. Test Cases and Scenarios
        """
        
        return {
            "content": engineering_spec,
            "metadata": {
                "document_type": "engineering_specification",
                "technical_domain": technical_domain,
                "complexity_level": complexity_level,
                "specification_type": "system_specification",
                "compliance_standards": ["Industry standards", "Regulatory requirements"]
            },
            "confidence_score": 0.85
        }
    
    async def _general_technical_assistance(self, task_request: TaskRequest, technical_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Provide general technical writing assistance"""
        # Create CrewAI task for general technical assistance
        technical_task = Task(
            description=f"""
            Provide expert technical writing assistance for the following request:
            
            Content: {task_request.content}
            Document Type: {technical_analysis['document_type']}
            Technical Domain: {technical_analysis['technical_domain']}
            Target Audience: {technical_analysis['target_audience']}
            Complexity Level: {technical_analysis['complexity_level']}
            
            Apply the technical writing framework:
            {TECHNICAL_EXPERT_PROMPTS['technical_writing_framework']}
            
            Ensure the response:
            • Addresses the specific technical writing needs
            • Uses appropriate technical terminology for the audience
            • Provides clear, actionable guidance
            • Includes relevant examples and best practices
            • Follows technical writing standards and conventions
            
            Provide comprehensive technical writing guidance with practical
            recommendations and adherence to industry best practices.
            """,
            agent=self.crew_agent,
            expected_output="Expert technical writing assistance with professional guidance"
        )
        
        # Execute task
        result = await asyncio.to_thread(technical_task.execute)
        
        return {
            "content": result,
            "metadata": {
                "document_type": technical_analysis["document_type"],
                "technical_domain": technical_analysis["technical_domain"],
                "target_audience": technical_analysis["target_audience"],
                "assistance_type": "general_technical_writing"
            },
            "confidence_score": 0.85
        }
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get technical expert capabilities"""
        return {
            "agent_type": "technical_expert",
            "expertise_areas": self.expertise_areas,
            "technical_domains": self.technical_domains,
            "document_types": list(TECHNICAL_EXPERT_PROMPTS["technical_document_types"].keys()),
            "documentation_standards": list(TECHNICAL_EXPERT_PROMPTS["documentation_standards"].keys()),
            "tools": [tool.name for tool in self.technical_tools],
            "performance_metrics": await self.get_performance_metrics()
        }
    
    async def get_technical_templates(self) -> Dict[str, Any]:
        """Get available technical document templates"""
        return {
            "software_documentation_templates": [
                "User Guide", "Administrator Guide", "Installation Manual", "Configuration Guide",
                "API Reference", "Developer Guide", "Release Notes", "Troubleshooting Guide"
            ],
            "api_documentation_templates": [
                "REST API Reference", "GraphQL API Guide", "SDK Documentation", "Integration Guide",
                "Webhook Documentation", "Authentication Guide", "Rate Limiting Guide"
            ],
            "engineering_specification_templates": [
                "System Requirements", "Technical Specification", "Architecture Document",
                "Design Document", "Interface Specification", "Test Plan", "Deployment Guide"
            ],
            "user_manual_templates": [
                "Product Manual", "Quick Start Guide", "Tutorial Series", "How-to Guides",
                "FAQ Document", "Troubleshooting Manual", "Reference Guide"
            ],
            "process_documentation_templates": [
                "Standard Operating Procedure", "Workflow Documentation", "Best Practices Guide",
                "Compliance Manual", "Quality Assurance Procedures", "Training Manual"
            ]
        }

