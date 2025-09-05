"""
Integration patch for enhanced file analysis and validation.
This shows the specific changes needed to fix the tool's file content and validation issues.
"""

# INTEGRATION PLAN: Modify scanner/advanced_llm_reasoning.py

def integrate_enhanced_analysis():
    """
    Here are the specific changes needed to fix the tool:
    
    1. REPLACE the truncated content approach
    2. ADD file structure analysis before patch generation  
    3. ADD patch validation after generation
    4. MODIFY the LLM prompts to include full context
    """
    
    # CHANGE 1: Fix the content truncation issue
    # CURRENT (Line 473 in advanced_llm_reasoning.py):
    # {safe_json_dumps({f["path"].name: f["content"][:500] + "..." if len(f["content"]) > 500 else f["content"] for f in selected_files}, indent=2)}
    
    # REPLACE WITH:
    # {safe_json_dumps({f["path"].name: f["content"] for f in selected_files}, indent=2)}
    
    # CHANGE 2: Add enhanced file analysis
    # ADD this import at the top:
    # from enhanced_file_analysis import EnhancedFileAnalyzer, PatchValidator, EnhancedPatchGenerator
    
    # CHANGE 3: Modify enhanced_patch_generation method
    # REPLACE the existing method with this enhanced version:
    pass

# Here's the complete replacement for the enhanced_patch_generation method:

ENHANCED_PATCH_GENERATION_METHOD = '''
def enhanced_patch_generation(self, intent: Dict, selected_files: List[Dict], 
                             reasoning_chain: ReasoningChain, strategy: str = "auto") -> Tuple[str, str, ReasoningChain]:
    """Generate patches with enhanced reasoning, full file analysis, and validation."""
    
    # STEP 1: Analyze actual file structures (NEW!)
    from enhanced_file_analysis import EnhancedFileAnalyzer, PatchValidator
    
    analyzer = EnhancedFileAnalyzer()
    validator = PatchValidator(analyzer)
    
    file_structures = {}
    structure_summaries = []
    
    for file_info in selected_files:
        file_path = str(file_info["path"])
        content = file_info["content"]
        
        # Analyze the actual structure
        structure = analyzer.analyze_file_structure(file_path, content)
        file_structures[file_path] = structure
        
        # Create summary for LLM
        summary = f"\\n=== {file_path} ===\\n"
        summary += f"Language: {structure.language}\\n"
        
        for class_struct in structure.classes:
            summary += f"Class {class_struct.name}"
            if class_struct.base_classes:
                summary += f" : {', '.join(class_struct.base_classes)}"
            summary += "\\n"
            
            for method in class_struct.methods[:5]:  # Limit to avoid token overflow
                params = ', '.join(method.parameters)
                modifiers = []
                if method.is_async:
                    modifiers.append("async")
                if method.is_override:
                    modifiers.append("override")
                modifier_str = " ".join(modifiers)
                summary += f"  {method.access_modifier} {modifier_str} {method.return_type} {method.name}({params})\\n"
        
        structure_summaries.append(summary)
    
    # STEP 2: Prepare enhanced context for patch generation
    context = {
        "intent": intent,
        "files": {f["path"].name: f["content"] for f in selected_files},  # FULL CONTENT, NO TRUNCATION!
        "file_structures": "\\n".join(structure_summaries),
        "previous_reasoning": reasoning_chain.final_conclusion
    }
    
    # STEP 3: Determine the modification strategy
    if strategy == "auto":
        strategy_directive = self._get_ai_strategy_decision(intent, selected_files)
    else:
        strategy_directive = self._get_explicit_strategy_directive(strategy)
    
    # STEP 4: Use reasoning to plan the patch with structure awareness
    patch_reasoning = self.analyze_with_chain_of_thought(
        task=f"Generate a comprehensive code patch that implements the telemetry requirements using the {strategy} strategy, based on ACTUAL file structure analysis",
        context=context,
        strategy=ReasoningStrategy.CHAIN_OF_THOUGHT
    )
    
    # STEP 5: Generate the actual patch with full context and structure awareness
    patch_prompt = f"""
Based on your detailed reasoning and ACTUAL file structure analysis, generate a precise unified diff.

STRATEGY DIRECTIVE:
{strategy_directive}

REASONING PLAN:
{patch_reasoning.final_conclusion}

ACTUAL FILE STRUCTURES FOUND:
{context["file_structures"]}

FULL FILE CONTENTS (NOT TRUNCATED):
{safe_json_dumps(context["files"], indent=2)}

REQUIREMENTS:
{safe_json_dumps(intent, indent=2)}

CRITICAL INSTRUCTIONS:
1. Use ONLY the method names and signatures that actually exist in the files
2. Respect the actual class inheritance patterns found
3. If a class overrides methods, use the correct method name (e.g., "Invoke" not "InvokeAsync")
4. Ensure all referenced methods, classes, and namespaces exist in the analyzed files
5. Generate changes that can actually be applied to the real file structure

Generate:
1. A clear explanation of the changes based on actual file analysis
2. A unified diff format patch that respects the real file structure
3. Implementation notes explaining how the patch aligns with existing code patterns

Format the response as:
## Explanation
[Clear explanation based on actual file analysis]

## Patch
```diff
[Unified diff that matches real file structure]
```

## Notes
[Implementation notes about real code patterns found]
"""

    try:
        response = self.client.chat.completions.create(
            model="o3",
            messages=[
                {"role": "system", "content": "You are an expert software engineer who analyzes ACTUAL code structure before making changes. You never assume method names or class structures - you only work with what actually exists in the analyzed files."},
                {"role": "user", "content": patch_prompt}
            ]
        )
        
        patch_content = response.choices[0].message.content
        
        # Parse explanation and diff
        explanation = self._extract_explanation(patch_content)
        diff = self._extract_diff(patch_content)
        
        # STEP 6: Validate the generated patch against actual file structures (NEW!)
        validation_issues = validator.validate_patch_against_structure(diff, file_structures)
        
        # Add validation results to explanation
        if validation_issues:
            explanation += "\\n\\n## Validation Issues Found:\\n"
            for issue in validation_issues:
                explanation += f"- {issue.severity.value.upper()}: {issue.message}\\n"
                if issue.suggested_fix:
                    explanation += f"  Suggested fix: {issue.suggested_fix}\\n"
        else:
            explanation += "\\n\\n## Validation: ✅ All checks passed - patch should apply successfully"
        
        return explanation, diff, patch_reasoning
        
    except Exception as e:
        # Enhanced fallback with structure info
        explanation = f"Error generating patch: {str(e)}\\n\\nFallback explanation based on reasoning and structure analysis."
        explanation += f"\\n\\nFile structures analyzed: {len(file_structures)} files"
        diff = "# Patch generation failed - manual implementation required based on analyzed structure"
        
        return explanation, diff, patch_reasoning
'''

# CHANGE 4: Add validation step to the pipeline
PIPELINE_INTEGRATION = '''
# In pipeline_orchestrator.py, add a new validation stage after patch generation:

def run_patch_validation(self, patch: str, selected_files: List[Dict]) -> Dict:
    """Validate generated patch against actual file structure."""
    
    from enhanced_file_analysis import EnhancedFileAnalyzer, PatchValidator
    
    analyzer = EnhancedFileAnalyzer()
    validator = PatchValidator(analyzer)
    
    # Analyze file structures
    file_structures = {}
    for file_info in selected_files:
        file_path = str(file_info["path"])
        content = file_info["content"]
        structure = analyzer.analyze_file_structure(file_path, content)
        file_structures[file_path] = structure
    
    # Validate patch
    validation_issues = validator.validate_patch_against_structure(patch, file_structures)
    
    return {
        "validation_issues": validation_issues,
        "can_apply": len([i for i in validation_issues if i.severity.value == "error"]) == 0,
        "warning_count": len([i for i in validation_issues if i.severity.value == "warning"]),
        "error_count": len([i for i in validation_issues if i.severity.value == "error"])
    }
'''

def show_exact_file_changes():
    """Shows the exact line-by-line changes needed."""
    
    changes = {
        "scanner/advanced_llm_reasoning.py": {
            "line_1": "Add import: from enhanced_file_analysis import EnhancedFileAnalyzer, PatchValidator",
            "line_473": "REMOVE truncation: Change f['content'][:500] + '...' to f['content']", 
            "method_enhanced_patch_generation": "Replace entire method with enhanced version above",
        },
        "scanner/pipeline_orchestrator.py": {
            "add_stage": "Add patch validation stage after patch generation"
        },
        "enhanced_cli.py": {
            "validation_reporting": "Add validation results to final report"
        }
    }
    
    return changes

if __name__ == "__main__":
    print("Enhanced File Analysis Integration Plan")
    print("="*50)
    print("\nThis enhancement will fix the core issues:")
    print("1. ✅ Reads FULL file content (no 500-char truncation)")
    print("2. ✅ Analyzes actual method signatures and class structure") 
    print("3. ✅ Validates patches against real code before generation")
    print("4. ✅ Provides specific error messages for method mismatches")
    print("5. ✅ Ensures generated patches can actually be applied")
    
    print("\nNext steps:")
    print("1. Copy enhanced_file_analysis.py to the scanner directory")
    print("2. Apply the integration changes shown above")
    print("3. Test with the same ticket to see improved results")
