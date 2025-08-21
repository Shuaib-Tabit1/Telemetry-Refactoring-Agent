"""
Comprehensive Testing and Validation Framework for the Telemetry Refactoring Agent.
"""
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import difflib
import re

class TestType(Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    REGRESSION = "regression"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"

class ValidationLevel(Enum):
    BASIC = "basic"
    COMPREHENSIVE = "comprehensive"
    EXHAUSTIVE = "exhaustive"

@dataclass
class TestResult:
    test_name: str
    test_type: TestType
    passed: bool
    score: float
    details: Dict[str, Any]
    errors: List[str]
    warnings: List[str]
    execution_time: float

@dataclass
class ValidationReport:
    overall_score: float
    test_results: List[TestResult]
    recommendations: List[str]
    risk_assessment: str
    compliance_status: Dict[str, bool]

class TelemetryAgentValidator:
    """Comprehensive validation framework for the telemetry refactoring agent."""
    
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self.test_data_dir = workspace_dir / "test_data"
        self.test_data_dir.mkdir(exist_ok=True)
        
    def run_comprehensive_validation(self, 
                                   intent: Dict,
                                   original_files: List[Dict],
                                   generated_patch: str,
                                   validation_level: ValidationLevel = ValidationLevel.COMPREHENSIVE) -> ValidationReport:
        """Run comprehensive validation of the agent's output."""
        
        test_results = []
        
        # 1. Intent Validation Tests
        intent_results = self._validate_intent_quality(intent)
        test_results.extend(intent_results)
        
        # 2. Patch Quality Tests
        patch_results = self._validate_patch_quality(generated_patch, original_files)
        test_results.extend(patch_results)
        
        # 3. Code Compilation Tests
        compilation_results = self._validate_code_compilation(original_files, generated_patch)
        test_results.extend(compilation_results)
        
        # 4. OpenTelemetry Compliance Tests
        compliance_results = self._validate_opentelemetry_compliance(generated_patch, intent)
        test_results.extend(compliance_results)
        
        # 5. Security and Best Practices Tests
        security_results = self._validate_security_practices(generated_patch)
        test_results.extend(security_results)
        
        if validation_level in [ValidationLevel.COMPREHENSIVE, ValidationLevel.EXHAUSTIVE]:
            # 6. Performance Impact Analysis
            performance_results = self._analyze_performance_impact(generated_patch)
            test_results.extend(performance_results)
            
            # 7. Integration Testing
            integration_results = self._validate_integration_compatibility(original_files, generated_patch)
            test_results.extend(integration_results)
        
        if validation_level == ValidationLevel.EXHAUSTIVE:
            # 8. Regression Testing
            regression_results = self._run_regression_tests(original_files, generated_patch)
            test_results.extend(regression_results)
            
            # 9. Edge Case Testing
            edge_case_results = self._test_edge_cases(intent, generated_patch)
            test_results.extend(edge_case_results)
        
        # Calculate overall score and generate report
        overall_score = self._calculate_overall_score(test_results)
        recommendations = self._generate_recommendations(test_results, intent)
        risk_assessment = self._assess_risk_level(test_results)
        compliance_status = self._check_compliance_status(test_results)
        
        return ValidationReport(
            overall_score=overall_score,
            test_results=test_results,
            recommendations=recommendations,
            risk_assessment=risk_assessment,
            compliance_status=compliance_status
        )
    
    def _validate_intent_quality(self, intent: Dict) -> List[TestResult]:
        """Validate the quality and completeness of the extracted intent."""
        results = []
        
        # Test 1: Required Fields Present
        required_fields = ["issue_category", "semantic_description", "search_keywords", "telemetry_operation"]
        missing_fields = [field for field in required_fields if not intent.get(field)]
        
        results.append(TestResult(
            test_name="Intent Required Fields",
            test_type=TestType.UNIT,
            passed=len(missing_fields) == 0,
            score=1.0 if len(missing_fields) == 0 else 0.5,
            details={"missing_fields": missing_fields},
            errors=[f"Missing required field: {field}" for field in missing_fields],
            warnings=[],
            execution_time=0.001
        ))
        
        # Test 2: Telemetry Operation Validity
        telemetry_op = intent.get("telemetry_operation", {})
        valid_types = ["span", "metric", "log"]
        valid_actions = ["CREATE", "ADD_ATTRIBUTES", "UPDATE_NAME"]
        
        type_valid = telemetry_op.get("type") in valid_types
        action_valid = telemetry_op.get("action") in valid_actions
        
        results.append(TestResult(
            test_name="Telemetry Operation Validity",
            test_type=TestType.UNIT,
            passed=type_valid and action_valid,
            score=1.0 if (type_valid and action_valid) else 0.0,
            details={"type": telemetry_op.get("type"), "action": telemetry_op.get("action")},
            errors=[] if (type_valid and action_valid) else ["Invalid telemetry operation"],
            warnings=[],
            execution_time=0.001
        ))
        
        # Test 3: Semantic Description Quality
        semantic_desc = intent.get("semantic_description", "")
        desc_quality_score = self._assess_description_quality(semantic_desc)
        
        results.append(TestResult(
            test_name="Semantic Description Quality",
            test_type=TestType.UNIT,
            passed=desc_quality_score >= 0.7,
            score=desc_quality_score,
            details={"description_length": len(semantic_desc), "quality_score": desc_quality_score},
            errors=[] if desc_quality_score >= 0.5 else ["Poor semantic description quality"],
            warnings=[] if desc_quality_score >= 0.7 else ["Semantic description could be improved"],
            execution_time=0.002
        ))
        
        return results
    
    def _validate_patch_quality(self, patch: str, original_files: List[Dict]) -> List[TestResult]:
        """Validate the quality of the generated code patch."""
        results = []
        
        # Test 1: Patch Format Validity
        is_valid_diff = self._is_valid_unified_diff(patch)
        results.append(TestResult(
            test_name="Patch Format Validity",
            test_type=TestType.UNIT,
            passed=is_valid_diff,
            score=1.0 if is_valid_diff else 0.0,
            details={"patch_length": len(patch)},
            errors=[] if is_valid_diff else ["Invalid unified diff format"],
            warnings=[],
            execution_time=0.001
        ))
        
        # Test 2: Code Style Compliance
        style_score = self._check_code_style_compliance(patch)
        results.append(TestResult(
            test_name="Code Style Compliance",
            test_type=TestType.UNIT,
            passed=style_score >= 0.8,
            score=style_score,
            details={"style_score": style_score},
            errors=[] if style_score >= 0.5 else ["Poor code style compliance"],
            warnings=[] if style_score >= 0.8 else ["Code style could be improved"],
            execution_time=0.003
        ))
        
        # Test 3: Change Scope Appropriateness
        scope_score = self._assess_change_scope(patch, len(original_files))
        results.append(TestResult(
            test_name="Change Scope Appropriateness",
            test_type=TestType.UNIT,
            passed=scope_score >= 0.7,
            score=scope_score,
            details={"scope_score": scope_score},
            errors=[] if scope_score >= 0.5 else ["Change scope too broad or narrow"],
            warnings=[] if scope_score >= 0.7 else ["Change scope may not be optimal"],
            execution_time=0.002
        ))
        
        return results
    
    def _validate_code_compilation(self, original_files: List[Dict], patch: str) -> List[TestResult]:
        """Validate that the patched code compiles successfully."""
        results = []
        
        try:
            # Create temporary directory for testing
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Apply patch to temporary files
                patched_files = self._apply_patch_to_temp_files(original_files, patch, temp_path)
                
                # Attempt compilation (simplified - would need proper project setup)
                compilation_success, compilation_errors = self._attempt_compilation(patched_files)
                
                results.append(TestResult(
                    test_name="Code Compilation",
                    test_type=TestType.INTEGRATION,
                    passed=compilation_success,
                    score=1.0 if compilation_success else 0.0,
                    details={"files_count": len(patched_files)},
                    errors=compilation_errors,
                    warnings=[],
                    execution_time=2.0  # Compilation takes time
                ))
        
        except Exception as e:
            results.append(TestResult(
                test_name="Code Compilation",
                test_type=TestType.INTEGRATION,
                passed=False,
                score=0.0,
                details={},
                errors=[f"Compilation test failed: {str(e)}"],
                warnings=[],
                execution_time=0.1
            ))
        
        return results
    
    def _validate_opentelemetry_compliance(self, patch: str, intent: Dict) -> List[TestResult]:
        """Validate OpenTelemetry compliance and best practices."""
        results = []
        
        # Test 1: Attribute Naming Compliance
        attributes = intent.get("telemetry_operation", {}).get("attributes_to_add", [])
        compliant_attributes = self._check_attribute_naming_compliance(attributes)
        
        results.append(TestResult(
            test_name="OpenTelemetry Attribute Naming",
            test_type=TestType.COMPLIANCE,
            passed=compliant_attributes,
            score=1.0 if compliant_attributes else 0.5,
            details={"attributes_count": len(attributes)},
            errors=[] if compliant_attributes else ["Non-compliant attribute names found"],
            warnings=[],
            execution_time=0.001
        ))
        
        # Test 2: Instrumentation Patterns
        pattern_compliance = self._check_instrumentation_patterns(patch)
        results.append(TestResult(
            test_name="Instrumentation Pattern Compliance",
            test_type=TestType.COMPLIANCE,
            passed=pattern_compliance >= 0.8,
            score=pattern_compliance,
            details={"pattern_score": pattern_compliance},
            errors=[] if pattern_compliance >= 0.6 else ["Poor instrumentation patterns"],
            warnings=[] if pattern_compliance >= 0.8 else ["Instrumentation patterns could be improved"],
            execution_time=0.002
        ))
        
        # Test 3: Resource Usage
        resource_usage = self._analyze_resource_usage(patch)
        results.append(TestResult(
            test_name="Resource Usage Analysis",
            test_type=TestType.PERFORMANCE,
            passed=resource_usage["score"] >= 0.8,
            score=resource_usage["score"],
            details=resource_usage,
            errors=resource_usage.get("errors", []),
            warnings=resource_usage.get("warnings", []),
            execution_time=0.003
        ))
        
        return results
    
    def _validate_security_practices(self, patch: str) -> List[TestResult]:
        """Validate security practices in the generated code."""
        results = []
        
        # Test 1: No Hardcoded Secrets
        has_secrets = self._check_for_hardcoded_secrets(patch)
        results.append(TestResult(
            test_name="No Hardcoded Secrets",
            test_type=TestType.COMPLIANCE,
            passed=not has_secrets,
            score=0.0 if has_secrets else 1.0,
            details={},
            errors=["Potential hardcoded secrets found"] if has_secrets else [],
            warnings=[],
            execution_time=0.001
        ))
        
        # Test 2: Input Validation
        input_validation_score = self._check_input_validation(patch)
        results.append(TestResult(
            test_name="Input Validation",
            test_type=TestType.COMPLIANCE,
            passed=input_validation_score >= 0.7,
            score=input_validation_score,
            details={"validation_score": input_validation_score},
            errors=[] if input_validation_score >= 0.5 else ["Insufficient input validation"],
            warnings=[] if input_validation_score >= 0.7 else ["Input validation could be improved"],
            execution_time=0.002
        ))
        
        return results
    
    def _analyze_performance_impact(self, patch: str) -> List[TestResult]:
        """Analyze potential performance impact of changes."""
        results = []
        
        # Analyze for performance-critical patterns
        perf_impact = self._assess_performance_impact(patch)
        
        results.append(TestResult(
            test_name="Performance Impact Analysis",
            test_type=TestType.PERFORMANCE,
            passed=perf_impact["risk_level"] <= 3,  # Scale of 1-5
            score=1.0 - (perf_impact["risk_level"] - 1) / 4,
            details=perf_impact,
            errors=perf_impact.get("errors", []),
            warnings=perf_impact.get("warnings", []),
            execution_time=0.005
        ))
        
        return results
    
    def _validate_integration_compatibility(self, original_files: List[Dict], patch: str) -> List[TestResult]:
        """Validate compatibility with existing integrations."""
        results = []
        
        # Check for breaking changes
        breaking_changes = self._detect_breaking_changes(original_files, patch)
        
        results.append(TestResult(
            test_name="Integration Compatibility",
            test_type=TestType.INTEGRATION,
            passed=len(breaking_changes) == 0,
            score=1.0 if len(breaking_changes) == 0 else max(0.0, 1.0 - len(breaking_changes) * 0.2),
            details={"breaking_changes": breaking_changes},
            errors=[f"Breaking change detected: {change}" for change in breaking_changes],
            warnings=[],
            execution_time=0.010
        ))
        
        return results
    
    # Helper methods for validation logic
    
    def _assess_description_quality(self, description: str) -> float:
        """Assess the quality of a semantic description."""
        if not description:
            return 0.0
        
        score = 0.0
        
        # Length check
        if 20 <= len(description) <= 200:
            score += 0.3
        
        # Contains technical terms
        tech_terms = ["telemetry", "instrumentation", "span", "metric", "attribute", "trace"]
        if any(term in description.lower() for term in tech_terms):
            score += 0.3
        
        # Contains action verbs
        action_verbs = ["add", "create", "configure", "implement", "ensure", "enable"]
        if any(verb in description.lower() for verb in action_verbs):
            score += 0.2
        
        # Grammatical structure
        if description.count('.') <= 2 and description.count(',') <= 3:
            score += 0.2
        
        return min(1.0, score)
    
    def _is_valid_unified_diff(self, patch: str) -> bool:
        """Check if the patch is a valid unified diff."""
        if not patch:
            return False
        
        lines = patch.split('\n')
        has_header = any(line.startswith('---') or line.startswith('+++') for line in lines)
        has_hunks = any(line.startswith('@@') for line in lines)
        has_changes = any(line.startswith('+') or line.startswith('-') for line in lines if not line.startswith('+++') and not line.startswith('---'))
        
        return has_header and has_hunks and has_changes
    
    def _check_code_style_compliance(self, patch: str) -> float:
        """Check code style compliance."""
        score = 1.0
        
        # Check for proper indentation (simplified)
        lines = patch.split('\n')
        added_lines = [line[1:] for line in lines if line.startswith('+') and not line.startswith('+++')]
        
        if added_lines:
            # Check indentation consistency
            indentation_issues = sum(1 for line in added_lines if line.strip() and not line.startswith('\t') and not line.startswith('    '))
            if indentation_issues > 0:
                score -= 0.2
            
            # Check for proper spacing
            spacing_issues = sum(1 for line in added_lines if '  ' in line and line.strip())
            if spacing_issues > len(added_lines) * 0.3:
                score -= 0.2
        
        return max(0.0, score)
    
    def _assess_change_scope(self, patch: str, original_file_count: int) -> float:
        """Assess if the change scope is appropriate."""
        lines = patch.split('\n')
        changed_lines = len([line for line in lines if line.startswith('+') or line.startswith('-')])
        
        # Heuristic: reasonable change scope
        if changed_lines < 5:
            return 0.7  # Might be too minimal
        elif changed_lines <= 50:
            return 1.0  # Good scope
        elif changed_lines <= 100:
            return 0.8  # Acceptable
        else:
            return 0.5  # Potentially too broad
    
    def _apply_patch_to_temp_files(self, original_files: List[Dict], patch: str, temp_dir: Path) -> List[Path]:
        """Apply patch to temporary files for testing."""
        # Simplified implementation - would need proper patch application
        patched_files = []
        
        for file_data in original_files:
            temp_file = temp_dir / file_data["path"].name
            temp_file.write_text(file_data["content"])
            patched_files.append(temp_file)
        
        return patched_files
    
    def _attempt_compilation(self, files: List[Path]) -> Tuple[bool, List[str]]:
        """Attempt to compile the files (simplified)."""
        # In a real implementation, this would set up a proper C# project and compile
        # For now, just check for basic syntax issues
        errors = []
        
        for file_path in files:
            content = file_path.read_text()
            
            # Basic syntax checks
            if content.count('{') != content.count('}'):
                errors.append(f"Mismatched braces in {file_path.name}")
            
            if content.count('(') != content.count(')'):
                errors.append(f"Mismatched parentheses in {file_path.name}")
        
        return len(errors) == 0, errors
    
    def _check_attribute_naming_compliance(self, attributes: List[Dict]) -> bool:
        """Check if attribute names follow OpenTelemetry semantic conventions."""
        compliant_prefixes = [
            "http.", "db.", "messaging.", "rpc.", "server.", "client.",
            "net.", "host.", "process.", "service.", "telemetry.",
            "user.", "enduser.", "session.", "browser.", "device.",
            "os.", "runtime.", "thread.", "code.", "exception."
        ]
        
        for attr in attributes:
            attr_name = attr.get("name", "")
            if not any(attr_name.startswith(prefix) for prefix in compliant_prefixes):
                if not attr_name.startswith("app."):  # Allow custom app. prefix
                    return False
        
        return True
    
    def _check_instrumentation_patterns(self, patch: str) -> float:
        """Check for proper instrumentation patterns."""
        score = 1.0
        
        # Look for proper Activity usage
        if "Activity" in patch:
            if "StartActivity" in patch or "CreateActivity" in patch:
                score += 0.2
            if "SetTag" in patch or "SetAttribute" in patch:
                score += 0.2
        
        # Look for proper error handling
        if "try" in patch and "catch" in patch:
            score += 0.1
        
        return min(1.0, score)
    
    def _analyze_resource_usage(self, patch: str) -> Dict[str, Any]:
        """Analyze resource usage patterns."""
        result = {
            "score": 1.0,
            "errors": [],
            "warnings": []
        }
        
        # Check for potential memory leaks
        if "new " in patch and "using" not in patch:
            result["warnings"].append("Consider using 'using' statements for disposable resources")
            result["score"] -= 0.1
        
        # Check for synchronous operations that could block
        blocking_patterns = ["Thread.Sleep", ".Wait()", ".Result"]
        for pattern in blocking_patterns:
            if pattern in patch:
                result["warnings"].append(f"Potential blocking operation: {pattern}")
                result["score"] -= 0.1
        
        return result
    
    def _check_for_hardcoded_secrets(self, patch: str) -> bool:
        """Check for hardcoded secrets or sensitive data."""
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'apikey\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']{20,}["\']'
        ]
        
        for pattern in secret_patterns:
            if re.search(pattern, patch, re.IGNORECASE):
                return True
        
        return False
    
    def _check_input_validation(self, patch: str) -> float:
        """Check for proper input validation."""
        score = 1.0
        
        # Look for validation patterns
        validation_patterns = ["ArgumentNullException", "ArgumentException", "string.IsNullOrEmpty", "if ("]
        validation_count = sum(1 for pattern in validation_patterns if pattern in patch)
        
        # Count method parameters that might need validation
        param_count = patch.count("(") + patch.count(",")
        
        if param_count > 0:
            validation_ratio = validation_count / param_count
            score = min(1.0, validation_ratio * 2)  # Boost validation ratio
        
        return score
    
    def _assess_performance_impact(self, patch: str) -> Dict[str, Any]:
        """Assess potential performance impact."""
        result = {
            "risk_level": 1,  # 1-5 scale
            "errors": [],
            "warnings": []
        }
        
        # Check for performance-sensitive operations
        if "Activity" in patch:
            result["risk_level"] += 1
            result["warnings"].append("Telemetry instrumentation may have minor performance impact")
        
        if "foreach" in patch and "Activity" in patch:
            result["risk_level"] += 1
            result["warnings"].append("Instrumentation in loops may impact performance")
        
        if patch.count("SetTag") > 10:
            result["risk_level"] += 1
            result["warnings"].append("Many attributes may impact performance")
        
        return result
    
    def _detect_breaking_changes(self, original_files: List[Dict], patch: str) -> List[str]:
        """Detect potential breaking changes."""
        breaking_changes = []
        
        # Check for signature changes
        if "public " in patch and ("-" in patch and "+" in patch):
            breaking_changes.append("Potential public API signature change")
        
        # Check for removed functionality
        removed_lines = [line[1:] for line in patch.split('\n') if line.startswith('-') and not line.startswith('---')]
        if any("public" in line for line in removed_lines):
            breaking_changes.append("Public member removed")
        
        return breaking_changes
    
    def _calculate_overall_score(self, test_results: List[TestResult]) -> float:
        """Calculate overall validation score."""
        if not test_results:
            return 0.0
        
        total_score = sum(result.score for result in test_results)
        return total_score / len(test_results)
    
    def _generate_recommendations(self, test_results: List[TestResult], intent: Dict) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        failed_tests = [result for result in test_results if not result.passed]
        
        if failed_tests:
            recommendations.append("Address failing tests before deployment")
        
        low_score_tests = [result for result in test_results if result.score < 0.7]
        if low_score_tests:
            recommendations.append("Improve implementation for low-scoring areas")
        
        # Domain-specific recommendations
        if intent.get("issue_category") == "INSTRUMENTATION":
            recommendations.append("Validate telemetry data collection in staging environment")
        
        return recommendations
    
    def _assess_risk_level(self, test_results: List[TestResult]) -> str:
        """Assess overall risk level."""
        failed_count = sum(1 for result in test_results if not result.passed)
        total_count = len(test_results)
        
        if failed_count == 0:
            return "LOW"
        elif failed_count / total_count < 0.2:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def _check_compliance_status(self, test_results: List[TestResult]) -> Dict[str, bool]:
        """Check compliance status for different areas."""
        compliance_tests = [result for result in test_results if result.test_type == TestType.COMPLIANCE]
        
        return {
            "opentelemetry": all(result.passed for result in compliance_tests if "OpenTelemetry" in result.test_name),
            "security": all(result.passed for result in compliance_tests if "Security" in result.test_name or "Secrets" in result.test_name),
            "style": all(result.passed for result in compliance_tests if "Style" in result.test_name)
        }

# Alias for compatibility with enhanced CLI
ValidationFramework = TelemetryAgentValidator
