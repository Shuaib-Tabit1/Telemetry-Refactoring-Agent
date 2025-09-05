"""
Enhanced File Content Analysis and Patch Validation System
Addresses the critical issues found in the telemetry refactoring tool.
"""
import ast
import re
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

@dataclass
class MethodSignature:
    """Represents a method signature found in code."""
    name: str
    parameters: List[str] 
    return_type: Optional[str]
    is_async: bool
    is_override: bool
    access_modifier: str
    line_number: int
    class_name: Optional[str] = None

@dataclass
class ClassStructure:
    """Represents a class structure found in code."""
    name: str
    base_classes: List[str]
    methods: List[MethodSignature]
    is_abstract: bool
    namespace: str
    line_number: int

@dataclass
class FileStructure:
    """Complete structure analysis of a code file."""
    file_path: str
    classes: List[ClassStructure]
    methods: List[MethodSignature]  # Top-level methods
    imports: List[str]
    namespace: str
    language: str

class ValidationSeverity(Enum):
    ERROR = "error"
    WARNING = "warning" 
    INFO = "info"

@dataclass
class ValidationIssue:
    severity: ValidationSeverity
    message: str
    line_number: Optional[int] = None
    suggested_fix: Optional[str] = None

class EnhancedFileAnalyzer:
    """Analyzes actual file content and structure before patch generation."""
    
    def analyze_file_structure(self, file_path: str, content: str) -> FileStructure:
        """Analyze the actual structure of a code file."""
        
        if file_path.endswith('.cs'):
            return self._analyze_csharp_structure(file_path, content)
        elif file_path.endswith('.py'):
            return self._analyze_python_structure(file_path, content)
        else:
            # Generic analysis
            return self._analyze_generic_structure(file_path, content)
    
    def _analyze_csharp_structure(self, file_path: str, content: str) -> FileStructure:
        """Analyze C# file structure including classes, methods, inheritance."""
        
        lines = content.split('\n')
        classes = []
        methods = []
        imports = []
        namespace = ""
        
        # Extract namespace
        namespace_match = re.search(r'namespace\s+([^\s;{]+)', content)
        if namespace_match:
            namespace = namespace_match.group(1)
        
        # Extract using statements
        using_matches = re.findall(r'using\s+([^;]+);', content)
        imports = [u.strip() for u in using_matches]
        
        # Find classes
        class_pattern = r'(public|internal|private|protected)?\s*(abstract|sealed|static)?\s*class\s+(\w+)(?:\s*:\s*([^{]+))?'
        class_matches = re.finditer(class_pattern, content)
        
        for class_match in class_matches:
            access_modifier = class_match.group(1) or 'internal'
            modifiers = class_match.group(2) or ''
            class_name = class_match.group(3)
            inheritance = class_match.group(4) or ''
            
            # Find line number
            line_num = content[:class_match.start()].count('\n') + 1
            
            # Parse base classes
            base_classes = []
            if inheritance:
                base_classes = [b.strip() for b in inheritance.split(',')]
            
            # Find methods in this class
            class_methods = self._find_csharp_methods_in_class(content, class_match.start(), class_name)
            
            classes.append(ClassStructure(
                name=class_name,
                base_classes=base_classes,
                methods=class_methods,
                is_abstract='abstract' in modifiers,
                namespace=namespace,
                line_number=line_num
            ))
        
        return FileStructure(
            file_path=file_path,
            classes=classes,
            methods=methods,
            imports=imports,
            namespace=namespace,
            language='csharp'
        )
    
    def _find_csharp_methods_in_class(self, content: str, class_start: int, class_name: str) -> List[MethodSignature]:
        """Find all methods within a specific class."""
        methods = []
        
        # Extract the class content (simplified - would need proper brace matching)
        class_section = content[class_start:]
        
        # Method pattern for C#
        method_pattern = r'(public|private|protected|internal)?\s*(static|virtual|override|abstract|async)?\s*(async)?\s*(\w+)\s+(\w+)\s*\(([^)]*)\)'
        method_matches = re.finditer(method_pattern, class_section)
        
        for method_match in method_matches:
            access_modifier = method_match.group(1) or 'private'
            modifiers = (method_match.group(2) or '') + ' ' + (method_match.group(3) or '')
            return_type = method_match.group(4)
            method_name = method_match.group(5)
            parameters_str = method_match.group(6)
            
            # Parse parameters
            parameters = []
            if parameters_str.strip():
                param_parts = parameters_str.split(',')
                parameters = [p.strip() for p in param_parts]
            
            line_num = content[:class_start + method_match.start()].count('\n') + 1
            
            methods.append(MethodSignature(
                name=method_name,
                parameters=parameters,
                return_type=return_type,
                is_async='async' in modifiers,
                is_override='override' in modifiers,
                access_modifier=access_modifier,
                line_number=line_num,
                class_name=class_name
            ))
        
        return methods
    
    def _analyze_python_structure(self, file_path: str, content: str) -> FileStructure:
        """Analyze Python file structure using AST."""
        try:
            tree = ast.parse(content)
            classes = []
            methods = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}")
                elif isinstance(node, ast.ClassDef):
                    base_classes = [ast.unparse(base) for base in node.bases]
                    class_methods = [self._ast_method_to_signature(m, node.name) 
                                   for m in node.body if isinstance(m, ast.FunctionDef)]
                    
                    classes.append(ClassStructure(
                        name=node.name,
                        base_classes=base_classes,
                        methods=class_methods,
                        is_abstract=any(isinstance(d, ast.Name) and d.id == 'abstractmethod' 
                                      for d in getattr(node, 'decorator_list', [])),
                        namespace='',
                        line_number=node.lineno
                    ))
                elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                    # Top-level function
                    methods.append(self._ast_method_to_signature(node))
            
            return FileStructure(
                file_path=file_path,
                classes=classes,
                methods=methods,
                imports=imports,
                namespace='',
                language='python'
            )
        except SyntaxError:
            # Fallback to regex-based analysis
            return self._analyze_generic_structure(file_path, content)
    
    def _ast_method_to_signature(self, node: ast.FunctionDef, class_name: Optional[str] = None) -> MethodSignature:
        """Convert AST FunctionDef to MethodSignature."""
        parameters = []
        for arg in node.args.args:
            param_str = arg.arg
            if arg.annotation:
                param_str += f": {ast.unparse(arg.annotation)}"
            parameters.append(param_str)
        
        return_type = None
        if node.returns:
            return_type = ast.unparse(node.returns)
        
        is_async = isinstance(node, ast.AsyncFunctionDef)
        
        return MethodSignature(
            name=node.name,
            parameters=parameters,
            return_type=return_type,
            is_async=is_async,
            is_override=False,  # Would need deeper analysis
            access_modifier='public',  # Python default
            line_number=node.lineno,
            class_name=class_name
        )
    
    def _analyze_generic_structure(self, file_path: str, content: str) -> FileStructure:
        """Generic structure analysis for unknown file types."""
        lines = content.split('\n')
        imports = []
        
        # Look for import-like statements
        for line in lines:
            if any(keyword in line for keyword in ['import ', 'using ', '#include ', 'require ']):
                imports.append(line.strip())
        
        return FileStructure(
            file_path=file_path,
            classes=[],
            methods=[],
            imports=imports,
            namespace='',
            language='unknown'
        )

class PatchValidator:
    """Validates generated patches against actual file structure."""
    
    def __init__(self, file_analyzer: EnhancedFileAnalyzer):
        self.file_analyzer = file_analyzer
    
    def validate_patch_against_structure(self, 
                                       patch: str, 
                                       file_structures: Dict[str, FileStructure]) -> List[ValidationIssue]:
        """Validate that a patch can actually be applied to the given file structures."""
        issues = []
        
        # Parse the patch to extract file modifications
        patch_modifications = self._parse_patch_modifications(patch)
        
        for file_path, modifications in patch_modifications.items():
            if file_path not in file_structures:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Patch references file {file_path} that was not analyzed"
                ))
                continue
            
            file_structure = file_structures[file_path]
            file_issues = self._validate_file_modifications(modifications, file_structure)
            issues.extend(file_issues)
        
        return issues
    
    def _parse_patch_modifications(self, patch: str) -> Dict[str, List[str]]:
        """Parse a unified diff patch to extract file modifications."""
        modifications = {}
        current_file = None
        
        lines = patch.split('\n')
        for line in lines:
            if line.startswith('+++') or line.startswith('---'):
                # Extract file path
                file_match = re.search(r'[ab]/(.+)', line)
                if file_match:
                    current_file = file_match.group(1)
                    if current_file not in modifications:
                        modifications[current_file] = []
            elif line.startswith('+') and current_file:
                # Added line
                modifications[current_file].append(line[1:])  # Remove the + prefix
        
        return modifications
    
    def _validate_file_modifications(self, 
                                   modifications: List[str], 
                                   file_structure: FileStructure) -> List[ValidationIssue]:
        """Validate modifications against a specific file structure."""
        issues = []
        
        for modification in modifications:
            # Check for method calls that might not exist
            method_calls = re.findall(r'(\w+)\.(\w+)\s*\(', modification)
            for obj, method in method_calls:
                # Check if method exists in known classes
                method_found = False
                for class_struct in file_structure.classes:
                    if any(m.name == method for m in class_struct.methods):
                        method_found = True
                        break
                
                if not method_found and method not in ['ToString', 'GetType', 'Equals']:  # Common .NET methods
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Method '{method}' not found in analyzed file structure",
                        suggested_fix=f"Verify that {obj}.{method}() is the correct method call"
                    ))
            
            # Check for references to methods that should be overridden
            if 'InvokeAsync' in modification:
                # Check if the class actually has InvokeAsync method
                has_invoke_async = any(
                    any(m.name == 'InvokeAsync' for m in class_struct.methods)
                    for class_struct in file_structure.classes
                )
                
                if not has_invoke_async:
                    # Check for Invoke method instead
                    has_invoke = any(
                        any(m.name == 'Invoke' for m in class_struct.methods)
                        for class_struct in file_structure.classes
                    )
                    
                    if has_invoke:
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            message="Patch references 'InvokeAsync' but file contains 'Invoke' method",
                            suggested_fix="Change 'InvokeAsync' to 'Invoke' in the patch"
                        ))
        
        return issues

class EnhancedPatchGenerator:
    """Enhanced patch generator that uses actual file structure."""
    
    def __init__(self, file_analyzer: EnhancedFileAnalyzer, validator: PatchValidator):
        self.file_analyzer = file_analyzer
        self.validator = validator
    
    def generate_validated_patch(self, 
                                intent: Dict,
                                selected_files: List[Dict]) -> Tuple[str, List[ValidationIssue]]:
        """Generate patch with full file structure analysis and validation."""
        
        # Step 1: Analyze actual file structures
        file_structures = {}
        for file_info in selected_files:
            file_path = file_info["path"]
            content = file_info["content"]
            
            structure = self.file_analyzer.analyze_file_structure(str(file_path), content)
            file_structures[str(file_path)] = structure
        
        # Step 2: Generate structure-aware prompt
        structure_context = self._build_structure_context(file_structures)
        
        # Step 3: Generate patch with full context (not truncated!)
        patch_prompt = f"""
Generate a telemetry enhancement patch based on ACTUAL file structure analysis.

INTENT: {intent}

ACTUAL FILE STRUCTURES:
{structure_context}

FULL FILE CONTENTS:
{self._build_full_content_context(selected_files)}

CRITICAL REQUIREMENTS:
1. Use ACTUAL method names and signatures found in the files
2. Respect class inheritance and override requirements
3. Use correct parameter types and method calls
4. Ensure all referenced methods and classes exist

Generate a precise unified diff that can be applied successfully.
"""
        
        # Step 4: Generate patch (would call LLM here)
        generated_patch = self._call_llm_for_patch(patch_prompt)
        
        # Step 5: Validate patch against structures
        validation_issues = self.validator.validate_patch_against_structure(
            generated_patch, file_structures
        )
        
        return generated_patch, validation_issues
    
    def _build_structure_context(self, file_structures: Dict[str, FileStructure]) -> str:
        """Build a context string describing the actual file structures."""
        context_parts = []
        
        for file_path, structure in file_structures.items():
            context_parts.append(f"\n=== {file_path} ===")
            context_parts.append(f"Language: {structure.language}")
            context_parts.append(f"Namespace: {structure.namespace}")
            
            for class_struct in structure.classes:
                context_parts.append(f"\nClass: {class_struct.name}")
                if class_struct.base_classes:
                    context_parts.append(f"  Inherits: {', '.join(class_struct.base_classes)}")
                if class_struct.is_abstract:
                    context_parts.append("  Abstract: Yes")
                
                context_parts.append("  Methods:")
                for method in class_struct.methods:
                    params = ', '.join(method.parameters)
                    async_str = "async " if method.is_async else ""
                    override_str = "override " if method.is_override else ""
                    context_parts.append(f"    {method.access_modifier} {async_str}{override_str}{method.return_type} {method.name}({params})")
        
        return '\n'.join(context_parts)
    
    def _build_full_content_context(self, selected_files: List[Dict]) -> str:
        """Build full file content context (NOT TRUNCATED)."""
        context_parts = []
        
        for file_info in selected_files:
            file_path = file_info["path"]
            content = file_info["content"]
            
            context_parts.append(f"\n=== {file_path} ===")
            context_parts.append(content)  # FULL CONTENT, NOT TRUNCATED!
        
        return '\n'.join(context_parts)
    
    def _call_llm_for_patch(self, prompt: str) -> str:
        """Call LLM with the enhanced prompt."""
        # This would call the actual LLM
        # For now, return a placeholder
        return "# Enhanced patch would be generated here with full context"

# Example usage
def enhance_telemetry_tool():
    """Example of how to integrate these enhancements."""
    
    analyzer = EnhancedFileAnalyzer()
    validator = PatchValidator(analyzer)
    generator = EnhancedPatchGenerator(analyzer, validator)
    
    # This would replace the current patch generation logic
    return generator
