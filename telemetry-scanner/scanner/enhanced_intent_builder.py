"""
Enhanced Intent Understanding System with multi-step planning and validation.
"""
import json
import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
from openai import AzureOpenAI

class IntentConfidence(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class OperationType(Enum):
    SINGLE_FILE = "single_file"
    MULTI_FILE = "multi_file"
    CONFIGURATION = "configuration"
    CROSS_CUTTING = "cross_cutting"

@dataclass
class ValidationResult:
    is_valid: bool
    confidence: IntentConfidence
    issues: List[str]
    suggestions: List[str]

@dataclass
class EnhancedIntent:
    # Original fields
    issue_category: str
    static_analysis_query: Optional[Dict]
    semantic_description: str
    search_keywords: List[str]
    telemetry_operation: Dict
    
    # Enhanced fields
    confidence: IntentConfidence
    operation_type: OperationType
    complexity_score: int  # 1-10
    estimated_files: int
    validation_result: ValidationResult
    sub_tasks: List[Dict] = None
    contextual_hints: List[str] = None
    similar_patterns: List[str] = None

class EnhancedIntentBuilder:
    """Advanced intent builder with multi-step reasoning and validation."""
    
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
            api_version="2024-12-01-preview"
        )
    
    def extract_enhanced_intent(self, ticket_text: str, context: Dict = None) -> EnhancedIntent:
        """Extract intent with enhanced understanding and planning."""
        
        # Step 1: Initial intent extraction
        basic_intent = self._extract_basic_intent(ticket_text)
        
        # Step 2: Complexity analysis
        complexity_analysis = self._analyze_complexity(ticket_text, basic_intent)
        
        # Step 3: Multi-step planning
        planning_result = self._create_multi_step_plan(ticket_text, basic_intent, complexity_analysis)
        
        # Step 4: Validation and confidence scoring
        validation = self._validate_intent(basic_intent, complexity_analysis, planning_result)
        
        # Step 5: Enhance with contextual information
        enhanced_intent = self._enhance_with_context(
            basic_intent, complexity_analysis, planning_result, validation, context
        )
        
        return enhanced_intent
    
    def _extract_basic_intent(self, ticket_text: str) -> Dict:
        """Extract basic intent using improved prompting."""
        
        system_prompt = """
You are an expert software architect analyzing software tickets. Your task is to extract structured intent from natural language descriptions.

Follow this enhanced analysis process:

1. **Entity Extraction**: Identify all technical entities (services, attributes, protocols, frameworks)
2. **Goal Synthesis**: Determine the primary and secondary objectives
3. **Pattern Recognition**: Identify if this matches common telemetry patterns
4. **Scope Analysis**: Determine if this is a single-file, multi-file, or cross-cutting change
5. **Complexity Assessment**: Rate complexity from 1-10 based on technical scope

Output valid JSON following this schema:

{
  "issue_category": "INSTRUMENTATION|CONFIGURATION",
  "static_analysis_query": {"find_method_call": "MethodName"} | null,
  "semantic_description": "One-sentence goal summary",
  "search_keywords": ["keyword1", "keyword2"],
  "telemetry_operation": {
    "type": "span|metric|log",
    "target_name": "string|null",
    "action": "CREATE|ADD_ATTRIBUTES|UPDATE_NAME",
    "attributes_to_add": [{"name": "attr.name", "value_source": "description"}],
    "new_span_name": "string|null",
    "new_metric_details": {}
  },
  "technical_entities": ["entity1", "entity2"],
  "primary_goal": "main objective",
  "secondary_goals": ["goal1", "goal2"],
  "recognized_patterns": ["pattern1", "pattern2"],
  "scope_indicators": ["single_method", "multiple_files", "configuration_change"]
}
"""
        
        response = self.client.chat.completions.create(
            model="o3",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this ticket:\n\n{ticket_text}"}
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    def _analyze_complexity(self, ticket_text: str, basic_intent: Dict) -> Dict:
        """Analyze the complexity and scope of the required changes."""
        
        complexity_prompt = f"""
Analyze the complexity of this telemetry change request:

Ticket: {ticket_text}
Basic Intent: {json.dumps(basic_intent, indent=2)}

Provide complexity analysis in JSON format:

{{
  "complexity_score": 1-10,
  "operation_type": "single_file|multi_file|configuration|cross_cutting",
  "estimated_files": 1-50,
  "risk_factors": ["factor1", "factor2"],
  "technical_challenges": ["challenge1", "challenge2"],
  "prerequisites": ["prereq1", "prereq2"]
}}
"""
        
        response = self.client.chat.completions.create(
            model="o3",
            messages=[{"role": "user", "content": complexity_prompt}],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    def _create_multi_step_plan(self, ticket_text: str, basic_intent: Dict, complexity: Dict) -> Dict:
        """Create a multi-step execution plan for complex changes."""
        
        if complexity.get("complexity_score", 1) <= 3:
            return {"steps": [{"order": 1, "action": "direct_implementation", "description": "Simple single-step implementation"}]}
        
        planning_prompt = f"""
Create a multi-step implementation plan for this telemetry change:

Ticket: {ticket_text}
Intent: {json.dumps(basic_intent, indent=2)}
Complexity: {json.dumps(complexity, indent=2)}

Provide a step-by-step plan in JSON format:

{{
  "steps": [
    {{
      "order": 1,
      "action": "locate_configuration",
      "description": "Find OpenTelemetry configuration files",
      "expected_files": ["Startup.cs", "*Extensions.cs"],
      "validation_criteria": "Configuration files found and analyzed"
    }},
    {{
      "order": 2,
      "action": "implement_changes",
      "description": "Add required instrumentation",
      "dependencies": [1],
      "validation_criteria": "Code changes implemented correctly"
    }}
  ],
  "alternative_approaches": ["approach1", "approach2"],
  "rollback_strategy": "description"
}}
"""
        
        response = self.client.chat.completions.create(
            model="o3",
            messages=[{"role": "user", "content": planning_prompt}],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    def _validate_intent(self, basic_intent: Dict, complexity: Dict, planning: Dict) -> ValidationResult:
        """Validate the extracted intent and assess confidence."""
        
        issues = []
        suggestions = []
        
        # Validate basic intent structure
        required_fields = ["issue_category", "semantic_description", "search_keywords", "telemetry_operation"]
        for field in required_fields:
            if not basic_intent.get(field):
                issues.append(f"Missing or empty required field: {field}")
        
        # Validate telemetry operation
        telemetry_op = basic_intent.get("telemetry_operation", {})
        if not telemetry_op.get("type") in ["span", "metric", "log"]:
            issues.append("Invalid telemetry operation type")
        
        if not telemetry_op.get("action") in ["CREATE", "ADD_ATTRIBUTES", "UPDATE_NAME"]:
            issues.append("Invalid telemetry action")
        
        # Assess confidence based on completeness and consistency
        confidence_score = 100
        if issues:
            confidence_score -= len(issues) * 20
        
        if not basic_intent.get("static_analysis_query"):
            confidence_score -= 10
            suggestions.append("Consider adding a static analysis query for more precise targeting")
        
        if len(basic_intent.get("search_keywords", [])) < 3:
            confidence_score -= 10
            suggestions.append("Add more search keywords for better coverage")
        
        # Determine confidence level
        if confidence_score >= 80:
            confidence = IntentConfidence.HIGH
        elif confidence_score >= 60:
            confidence = IntentConfidence.MEDIUM
        else:
            confidence = IntentConfidence.LOW
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            confidence=confidence,
            issues=issues,
            suggestions=suggestions
        )
    
    def _enhance_with_context(self, basic_intent: Dict, complexity: Dict, 
                             planning: Dict, validation: ValidationResult, 
                             context: Dict = None) -> EnhancedIntent:
        """Create enhanced intent with all analysis results."""
        
        # Map complexity score to operation type
        complexity_score = complexity.get("complexity_score", 5)
        if complexity_score <= 2:
            operation_type = OperationType.SINGLE_FILE
        elif complexity_score <= 5:
            operation_type = OperationType.MULTI_FILE
        elif basic_intent.get("issue_category") == "CONFIGURATION":
            operation_type = OperationType.CONFIGURATION
        else:
            operation_type = OperationType.CROSS_CUTTING
        
        return EnhancedIntent(
            issue_category=basic_intent["issue_category"],
            static_analysis_query=basic_intent.get("static_analysis_query"),
            semantic_description=basic_intent["semantic_description"],
            search_keywords=basic_intent["search_keywords"],
            telemetry_operation=basic_intent["telemetry_operation"],
            confidence=validation.confidence,
            operation_type=operation_type,
            complexity_score=complexity_score,
            estimated_files=complexity.get("estimated_files", 1),
            validation_result=validation,
            sub_tasks=planning.get("steps", []),
            contextual_hints=complexity.get("technical_challenges", []),
            similar_patterns=basic_intent.get("recognized_patterns", [])
        )
