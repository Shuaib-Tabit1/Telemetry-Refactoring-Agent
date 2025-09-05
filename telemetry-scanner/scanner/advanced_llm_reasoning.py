"""
Advanced LLM Reasoning System with Chain-of-Thought, validation, and self-correction.
"""
import json
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from openai import AzureOpenAI

def safe_json_dumps(obj, **kwargs):
    """Safely serialize objects to JSON, handling complex types."""
    def default_serializer(o):
        if hasattr(o, '__dict__'):
            return {k: str(v) for k, v in o.__dict__.items()}
        elif hasattr(o, 'value'):  # Handle enums
            return o.value
        else:
            return str(o)
    
    # Remove any existing 'default' parameter to avoid conflicts
    kwargs.pop('default', None)
    
    return json.dumps(obj, default=default_serializer, **kwargs)

class ReasoningStrategy(Enum):
    CHAIN_OF_THOUGHT = "chain_of_thought"
    TREE_OF_THOUGHTS = "tree_of_thoughts" 
    REFLECTION = "reflection"
    SELF_CORRECTION = "self_correction"

@dataclass
class ReasoningStep:
    step_number: int
    description: str
    reasoning: str
    conclusion: str
    confidence: float
    evidence: List[str]

@dataclass
class ReasoningChain:
    strategy: ReasoningStrategy
    steps: List[ReasoningStep]
    final_conclusion: str
    overall_confidence: float
    alternative_approaches: List[str]


class AdvancedLLMReasoner:
    """Advanced LLM reasoning system with chain-of-thought and validation."""
    
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
            api_version="2024-12-01-preview", 
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT")
        )
        
    def analyze_with_chain_of_thought(self, 
                                    task: str,
                                    context: Dict,
                                    strategy: ReasoningStrategy = ReasoningStrategy.CHAIN_OF_THOUGHT) -> ReasoningChain:
        """Perform advanced reasoning using chain-of-thought approach."""
        
        if strategy == ReasoningStrategy.CHAIN_OF_THOUGHT:
            return self._chain_of_thought_reasoning(task, context)
        elif strategy == ReasoningStrategy.TREE_OF_THOUGHTS:
            return self._tree_of_thoughts_reasoning(task, context)
        elif strategy == ReasoningStrategy.REFLECTION:
            return self._reflection_reasoning(task, context)
        else:
            return self._self_correction_reasoning(task, context)
    

    
    def _chain_of_thought_reasoning(self, task: str, context: Dict) -> ReasoningChain:
        """Implement chain-of-thought reasoning."""
        
        prompt = f"""You are an expert software engineer tasked with telemetry implementation.

TASK: {task}

CONTEXT:
{safe_json_dumps(context, indent=2)}

Think through this step by step:

1. **Analysis**: What are the key requirements and constraints?
2. **Planning**: What approach would work best? PREFER MINIMAL CHANGES.
3. **Implementation**: What specific changes are needed? SELECT ONLY THE MOST RELEVANT FILES.
4. **Validation**: How can we ensure this works correctly?

For each step, provide:
- Clear reasoning
- Specific evidence from the context
- Confidence level (0.0-1.0)
- Alternative approaches considered

CRITICAL: Focus on minimal, targeted changes. Avoid overengineering by selecting too many files.
Only select files that are directly relevant to the telemetry requirement.
Be thorough and systematic, but prefer simplicity over complexity."""

        try:
            response = self.client.chat.completions.create(
                model="o3",
                messages=[
                    {"role": "system", "content": "You are an expert software engineer specializing in telemetry implementation."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            reasoning_text = response.choices[0].message.content
            
            # Parse the response into structured reasoning steps
            steps = self._parse_reasoning_steps(reasoning_text)
            
            return ReasoningChain(
                strategy=ReasoningStrategy.CHAIN_OF_THOUGHT,
                steps=steps,
                final_conclusion=self._extract_final_conclusion(reasoning_text),
                overall_confidence=self._calculate_overall_confidence(steps),
                alternative_approaches=self._extract_alternatives(reasoning_text)
            )
            
        except Exception as e:
            # Fallback reasoning chain
            return ReasoningChain(
                strategy=ReasoningStrategy.CHAIN_OF_THOUGHT,
                steps=[ReasoningStep(
                    step_number=1,
                    description="Fallback analysis",
                    reasoning=f"Error in LLM reasoning: {str(e)}",
                    conclusion="Using fallback approach",
                    confidence=0.5,
                    evidence=["Error occurred"]
                )],
                final_conclusion="Fallback conclusion due to reasoning error",
                overall_confidence=0.5,
                alternative_approaches=["Manual implementation"]
            )
    
        
     
    
    def enhanced_patch_generation(self, intent: Dict, selected_files: List[Dict],reasoning_chain: ReasoningChain,strategy: str = "auto",) -> Tuple[str, str, ReasoningChain]:
        """Generate patches with enhanced reasoning, strict path scoping, and diff validation."""
        from pathlib import Path

        # 1) Repo-relative paths + allowed set
        repo_root = Path(intent.get("repo_root", ".")).resolve()

        def _rel(p):
            p = p if isinstance(p, Path) else Path(p)
            try:
                return str(p.resolve().relative_to(repo_root))
            except Exception:
                return str(p.resolve())

        rel_files = {_rel(f["path"]): f["content"] for f in selected_files}
        allowed_paths = list(rel_files.keys())

        # 2) Decide strategy
        if strategy == "auto":
            strategy_directive = self._get_ai_strategy_decision(intent, selected_files)
        else:
            strategy_directive = self._get_explicit_strategy_directive(strategy)

        # 3) Reasoning pass (context includes scoped files)
        # Handle both string and ReasoningChain object cases
        if hasattr(reasoning_chain, 'final_conclusion'):
            previous_reasoning = reasoning_chain.final_conclusion
        else:
            # reasoning_chain is a string
            previous_reasoning = str(reasoning_chain)
            
        context = {
            "intent": intent,
            "files": rel_files,              # repo-relative path -> content
            "allowed_paths": allowed_paths,  # ONLY these may be edited
            "previous_reasoning": previous_reasoning,
        }
        patch_reasoning = self.analyze_with_chain_of_thought(
            task=f"Generate a comprehensive code patch that implements the telemetry requirements using the {strategy} strategy",
            context=context,
            strategy=ReasoningStrategy.CHAIN_OF_THOUGHT,
        )

        # Generate the actual patch
        patch_prompt = f"""
You are to generate a precise, *applicable* unified diff that implements the telemetry changes.

STRATEGY DIRECTIVE:
{strategy_directive}

REASONING PLAN (high level):
{patch_reasoning.final_conclusion}

FILES (repo-relative path → content):
{safe_json_dumps(rel_files, indent=2)}

ALLOWED_PATHS (you may edit ONLY these):
{safe_json_dumps(allowed_paths, indent=2)}

REQUIREMENTS (intent):
{safe_json_dumps(intent, indent=2)}

OUTPUT FORMAT (STRICT):
## Explanation
- Briefly justify what you changed and where (mention file paths from ALLOWED_PATHS).
- Note any assumptions.

## Patch
```diff
[Unified diff with git-style headers ONLY for files in ALLOWED_PATHS]
Notes

Any caveats, follow-ups, or TODOs relevant to reviewers.

CRITICAL GUIDELINES:

FIRST: Prefer extending existing telemetry (e.g., add SetTag/attributes near StartActivity or enrichment callbacks).

DO NOT: Create new classes/middleware/helpers unless explicitly required by REQUIREMENTS.

EXACT: Use attribute names exactly as specified (e.g., "HTTP_REFERER", "HTTP_RESPONSE_REDIRECT_LOCATION").

LEAST CHANGE: Modify the smallest necessary region that achieves the requirement.

CONSISTENT: Preserve existing formatting/usings unless required for compilation.

STRICT DIFF RULES (MANDATORY):

Edit ONLY files in ALLOWED_PATHS.

Use git-style unified diff headers with the same repo-relative path on both sides:
--- a/<repo-relative-path>
+++ b/<repo-relative-path>

DO NOT create new files (no '--- /dev/null', no 'new file mode').

DO NOT modify or reference any path outside ALLOWED_PATHS.

Ensure the diff applies cleanly with standard tools (e.g., git apply --index).

If no edit is necessary in the provided files, return an EMPTY diff and explain why in ## Explanation.

REMINDERS:

Prefer inline attribute additions over architectural changes.

If an enrichment hook already exists, add attributes there instead of duplicating logic.
"""

        # Estimate token count for debugging (rough estimate: 1 token = 4 chars)
        total_chars = len(patch_prompt)
        estimated_tokens = total_chars // 4
        print(f"Debug: Patch prompt is ~{estimated_tokens:,} tokens ({total_chars:,} chars)")
            
        if estimated_tokens > 180000:  # Conservative limit below 200K
            print(f"Warning: Prompt may exceed token limit. Consider reducing file selection.")

        try:
            response = self.client.chat.completions.create(
                model="o3",
                messages=[
                    {"role": "system", "content": "You are an expert software engineer specializing in telemetry and observability implementation."},
                    {"role": "user", "content": patch_prompt}
                ]
            )
            
            patch_content = response.choices[0].message.content
            
            # Parse explanation and diff
            explanation = self._extract_explanation(patch_content)
            diff = self._extract_diff(patch_content)
            
            return explanation, diff, patch_reasoning
            
        except Exception as e:
            # Fallback patch generation
            explanation = f"Error generating patch: {str(e)}\n\nFallback explanation based on reasoning."
            diff = "# Patch generation failed - manual implementation required"
            
            return explanation, diff, patch_reasoning
    
    # Helper methods for parsing LLM responses
    
    def _parse_reasoning_steps(self, text: str) -> List[ReasoningStep]:
        """Parse reasoning text into structured steps."""
        # Simple parsing - in production would use more sophisticated NLP
        steps = []
        lines = text.split('\n')
        current_step = 1
        
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in ['analysis', 'planning', 'implementation', 'validation']):
                description = line.strip()
                reasoning = '\n'.join(lines[i:i+3]) if i+3 < len(lines) else line
                
                steps.append(ReasoningStep(
                    step_number=current_step,
                    description=description,
                    reasoning=reasoning,
                    conclusion=reasoning.split('\n')[-1] if '\n' in reasoning else reasoning,
                    confidence=0.8,  # Default confidence
                    evidence=["LLM analysis"]
                ))
                current_step += 1
        
        if not steps:
            # Fallback single step
            steps.append(ReasoningStep(
                step_number=1,
                description="Analysis",
                reasoning=text,
                conclusion="Reasoning completed",
                confidence=0.7,
                evidence=["LLM response"]
            ))
        
        return steps
    

    def _extract_final_conclusion(self, text: str) -> str:
        """Extract the final conclusion from reasoning text."""
        lines = text.split('\n')
        # Look for conclusion keywords
        for line in reversed(lines):
            if any(keyword in line.lower() for keyword in ['conclusion', 'final', 'result', 'recommendation']):
                return line.strip()
        
        # Fallback to last non-empty line
        for line in reversed(lines):
            if line.strip():
                return line.strip()
        
        return "No clear conclusion found"

    def _calculate_overall_confidence(self, steps: List[ReasoningStep]) -> float:
        """Calculate overall confidence from individual steps."""
        if not steps:
            return 0.5
        
        return sum(step.confidence for step in steps) / len(steps)

    def _extract_alternatives(self, text: str) -> List[str]:
        """Extract alternative approaches from reasoning text."""
        alternatives = []
        lines = text.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['alternative', 'option', 'approach', 'method']):
                alternatives.append(line.strip())
        
        return alternatives[:3]  # Limit to 3 alternatives

    def _fallback_reasoning_chain(self, error: str) -> ReasoningChain:
        """Create a fallback reasoning chain when LLM calls fail."""
        return ReasoningChain(
            strategy=ReasoningStrategy.CHAIN_OF_THOUGHT,
            steps=[ReasoningStep(
                step_number=1,
                description="Fallback reasoning",
                reasoning=f"LLM reasoning failed: {error}",
                conclusion="Using fallback approach",
                confidence=0.5,
                evidence=["Error handling"]
            )],
            final_conclusion="Fallback reasoning due to LLM error",
            overall_confidence=0.5,
            alternative_approaches=["Manual analysis", "Simplified approach"]
        )


    def _extract_explanation(self, content: str) -> str:
        """Extract explanation section from patch content."""
        lines = content.split('\n')
        explanation_lines = []
        in_explanation = False
        
        for line in lines:
            if '## Explanation' in line:
                in_explanation = True
                continue
            elif line.startswith('##') and in_explanation:
                break
            elif in_explanation:
                explanation_lines.append(line)
        
        return '\n'.join(explanation_lines).strip()

    def _extract_diff(self, content: str) -> str:
        """Extract diff section from patch content."""
        lines = content.split('\n')
        diff_lines = []
        in_diff = False
        
        for line in lines:
            if '```diff' in line:
                in_diff = True
                continue
            elif '```' in line and in_diff:
                break
            elif in_diff:
                diff_lines.append(line)
        
        return '\n'.join(diff_lines).strip()

    def _get_ai_strategy_decision(self, intent: Dict, selected_files: List[Dict]) -> str:
        """Let AI decide the best modification strategy based on context."""
        
        analysis_prompt = f"""
Analyze this telemetry change request and determine the best implementation approach.

CHANGE REQUEST:
{safe_json_dumps(intent, indent=2)}

FILES TO MODIFY: {len(selected_files)} files
FILE NAMES: {[f["path"].name for f in selected_files]}

Consider these factors:
1. **Scale**: How many files need the same change?
2. **Pattern**: Is this a cross-cutting concern or localized fix?
3. **Maintenance**: Will this change be repeated in future development?
4. **Codebase**: What patterns already exist in the code?
5. **Complexity**: How complex is the required change?

Choose the best approach:
- **DIRECT_MODIFICATION**: Modify each file individually at every relevant location. Good for: simple changes, comprehensive coverage, immediate requirements.
- **HELPER_METHODS**: Create reusable helper methods and infrastructure. Good for: complex logic, future maintainability, DRY principles.

Respond with your choice and 2-3 sentences explaining why:

DECISION: [DIRECT_MODIFICATION or HELPER_METHODS]
REASONING: [Your explanation]
"""
        
        try:
            response = self.client.chat.completions.create(
                model="o3",
                messages=[
                    {"role": "system", "content": "You are an expert software architect making strategic decisions about code modification approaches."},
                    {"role": "user", "content": analysis_prompt}
                ]
            )
            
            decision_text = response.choices[0].message.content
            
            if "DIRECT_MODIFICATION" in decision_text:
                return self._get_explicit_strategy_directive("direct")
            else:
                return self._get_explicit_strategy_directive("helpers")
                
        except Exception as e:
            # Fallback to helpers approach
            return self._get_explicit_strategy_directive("helpers")
    
    def _get_explicit_strategy_directive(self, strategy: str) -> str:
        """Get explicit strategy directive based on chosen approach."""
        
        if strategy == "direct":
            return """
**STRATEGIC DIRECT MODIFICATION:**
- PREFER SINGLE STRATEGIC FILES: Choose the most strategic file that can solve the entire requirement (e.g., Global.asax, ScmHttpApplication.cs, central middleware)
- AVOID MULTIPLE FILES: When one file can handle the requirement, don't modify multiple files
- TARGET KEY INSERTION POINTS: Find the single most effective location for the change
- IMPLEMENT COMPLETE SOLUTION: Ensure the chosen location captures all required telemetry
- FOCUS ON MAINTAINABILITY: Single-point modifications are easier to maintain than scattered changes

**PRIORITIZATION ORDER:**
1. Application entry points (Global.asax.cs, ScmHttpApplication.cs)  
2. Central request/response handlers (Startup.cs middleware configuration)
3. Base classes that handle all requests
4. LAST RESORT: Multiple middleware files

Example approach - PREFER THIS:
```csharp
// In ScmHttpApplication.cs - ONE STRATEGIC LOCATION
protected void Application_BeginRequest()
{
    var activity = Activity.Current;
    activity?.SetTag("HTTP_REFERER", Request.Headers["Referer"]);
}

protected void Application_EndRequest()  
{
    var activity = Activity.Current;
    activity?.SetTag("HTTP_RESPONSE_REDIRECT_LOCATION", Response.Headers["Location"]);
}
```

AVOID THIS (multiple file changes):
```csharp
// Don't modify 8 different middleware files when 1 strategic file can solve it
```
"""
        else:  # helpers
            return """
**HELPER METHOD STRATEGY:**
- Create reusable helper methods and extension classes
- Update DI registration and central configuration
- Provide infrastructure for consistent usage
- Focus on maintainable, DRY solutions
- Create examples showing how to use the new helpers
- Ensure the solution can be easily adopted by the development team

Example approach:
```csharp
// Create extension method:
public static Activity StartActivityWithContext(this ActivitySource source, string name) { ... }

// Show usage:
var activity = source.StartActivityWithContext("operation");
```
"""



    def filter_batch_for_telemetry_enhancement(self, batch_context):
        """
        Filter a batch of files for telemetry enhancement potential using LLM reasoning.
        
        This method evaluates each file in a batch to determine if it could benefit from
        telemetry enhancement based on the ticket requirements. It's designed to be generic
        for all telemetry types (spans, metrics, logs, custom) and aligns with the coding
        instruction for direct instrumentation.
        
        Args:
            batch_context: Dict containing telemetry_intent and files list
            
        Returns:
            Object with selected_files list containing paths of promising files
        """
        prompt = f"""
    You are analyzing files for telemetry enhancement opportunities. Given this telemetry requirement:

    OPERATION: {batch_context['telemetry_intent']['operation']}
    CATEGORY: {batch_context['telemetry_intent']['category']}
    DESCRIPTION: {batch_context['telemetry_intent']['description']}
    OPERATION_TYPE: {batch_context['telemetry_intent']['operation_type']}

    For each file in this batch, determine if it could benefit from this telemetry enhancement.

    Files to analyze:
    {chr(10).join(f"- {file_info['path']} (search score: {file_info['relevance_score']}, strategy: {file_info['search_strategy']})" for file_info in batch_context['files'])}

    Consider these factors:
    1. **Business Logic Relevance**: Does this file handle the business logic mentioned in the requirement?
    2. **Telemetry Potential**: Could telemetry (spans, metrics, logs, traces) be added to improve observability?
    3. **System Interactions**: Does this file interact with the systems/data mentioned in the requirement?
    4. **Direct Instrumentation**: Can we add telemetry attributes directly after span creation sites?
    5. **Pattern Matching**: Does this file contain patterns like StartActivity, ActivitySource, HTTP handling, database operations?

    Focus on files where you can add telemetry instrumentation directly following the preferred approach of:
    - Search for span creation sites (StartActivity, ActivitySource)
    - Inject attribute-setting code directly after each span creation
    - Avoid processor-based enrichment unless explicitly requested

    Return ONLY the file paths (one per line) that have genuine telemetry enhancement potential.
    Do not include configuration files, test files, or files without actual instrumentation opportunities.

    Example response format:
    /path/to/CustomerService.cs
    /path/to/PaymentProcessor.cs
    """

        try:
            response = self.client.chat.completions.create(
                model="o3",
                messages=[
                    {"role": "system", "content": "You are an expert in telemetry and observability. You understand different telemetry types (spans, metrics, logs) and can identify files where direct instrumentation can be added."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse file paths from response
            selected_files = []
            for line in response_text.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('//'):
                    # Extract just the path part (in case LLM adds explanations)
                    if ' ' in line:
                        line = line.split(' ')[0]
                    selected_files.append(line)
            
            return type('BatchFilterResult', (), {
                'selected_files': selected_files,
                'reasoning': response_text,
                'total_evaluated': len(batch_context['files']),
                'selected_count': len(selected_files)
            })()
            
        except Exception as e:
            print(f"Error in batch filtering: {e}")
            # Fallback: return all files if LLM fails
            return type('BatchFilterResult', (), {
                'selected_files': [file_info['path'] for file_info in batch_context['files']],
                'reasoning': f"Error occurred: {e}. Returned all files as fallback.",
                'total_evaluated': len(batch_context['files']),
                'selected_count': len(batch_context['files'])
            })()

    def final_telemetry_file_selection(self, batch_context):
        """
        Analyze a single file and its relationships to determine if the telemetry gap can be solved.
        
        This method performs focused analysis on one main file and its related files to determine
        if this specific group can implement the required telemetry enhancement. This enables
        relationship-aware file selection with manageable context size.
        
        Args:
            batch_context: Dict containing main_file name, files with content, and telemetry_intent
            
        Returns:
            Object with can_solve_telemetry_gap boolean and selected_files list
        """
        # Prepare files summary for this batch
        main_file_name = batch_context['main_file']
        files_summary = []
        
        for i, file_data in enumerate(batch_context['files']):
            is_main = file_data['path'].name == main_file_name
            relationship_indicator = "🎯 MAIN FILE" if is_main else "🔗 Related"
            
            file_summary = f"""
    {relationship_indicator}: {file_data['path'].name}
    - Search Score: {file_data.get('search_score', 'N/A')}
    - Content Preview: {file_data['content'][:800]}...
    - Relationship: {'Primary candidate' if is_main else 'Called by or calls main file'}"""
            files_summary.append(file_summary)
        
        prompt = f"""
    You are analyzing whether a specific group of related files can solve this telemetry requirement:

    **TELEMETRY REQUIREMENT:**
    Operation: {batch_context['telemetry_intent'].telemetry_operation}
    Category: {batch_context['telemetry_intent'].issue_category}
    Description: {batch_context['telemetry_intent'].semantic_description}
    Type: {batch_context['telemetry_intent'].operation_type.value}

    **FILE GROUP ANALYSIS:**
    Main File: {main_file_name}
    Total Files in Group: {len(batch_context['files'])}

    {chr(10).join(files_summary)}

    **YOUR TASK:**
    Analyze this specific group of related files and determine:

    1. **CAN_SOLVE_TELEMETRY_GAP**: Can this group of files implement the telemetry requirement?
       - Does the main file or its related files handle the functionality mentioned in the requirement?
       - Is there existing telemetry infrastructure (Activities, Spans, SetTag) that can be extended?
       - Can the required telemetry attributes be captured in this execution context?

    2. **STRATEGIC_VALUE**: How strategic is this solution?
       - MOST_STRATEGIC: Central utilities, Global.asax, entry points that affect ALL requests
       - STRATEGIC: Middleware/base classes that affect many requests  
       - TACTICAL: Individual controllers/handlers that affect some requests
       - SKIP: Files that cannot solve the gap or are not strategic

    3. **FINAL_DECISION**: Should this group be selected for the patch?
       - SELECT_AS_PRIMARY: This is the best strategic solution (central utility, global entry point)
       - SELECT_AS_FALLBACK: Good solution but not as strategic as primary options
       - SKIP: Either cannot solve gap or is not strategic enough

    **ANALYSIS CRITERIA:**
    ✅ **Good Candidates**: Files with StartActivity, ActivitySource, HTTP handling, business logic related to requirement
    ✅ **Strategic Single Files**: Global.asax, application entry points, central request handlers that can solve the requirement alone
    ❌ **Skip**: Configuration files, test files, files without instrumentation opportunities
    ❌ **Skip Group**: If none of the files can implement the telemetry requirement

    **PRIORITIZATION RULES:**
    1. **PREFER SINGLE STRATEGIC FILES**: If one file (e.g., Global.asax, ScmHttpApplication.cs, Startup.cs) can solve the entire requirement, select ONLY that file
    2. **AVOID MULTIPLE MIDDLEWARE**: Don't select multiple middleware files when one strategic file can handle the requirement
    3. **MINIMIZE FILE COUNT**: Prefer solutions that modify fewer files for maintainability

    **RESPONSE FORMAT:**
    CAN_SOLVE_GAP: [YES/NO]
    STRATEGIC_VALUE: [MOST_STRATEGIC/STRATEGIC/TACTICAL/SKIP]
    FINAL_DECISION: [SELECT_AS_PRIMARY/SELECT_AS_FALLBACK/SKIP]
    
    SELECTED_FILES: (only if FINAL_DECISION is SELECT_AS_PRIMARY or SELECT_AS_FALLBACK)
    /path/to/file1.cs
    
    REASONING:
    [Explain your analysis: can this solve the gap, how strategic it is, and your final decision. If you identify a central utility that other files call, mark it as MOST_STRATEGIC.]
    """

        try:
            response = self.client.chat.completions.create(
                model="o3",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a senior telemetry engineer specialized in relationship-aware code analysis. You excel at understanding how files work together and determining whether a group of related files can implement specific telemetry requirements. You focus on direct instrumentation opportunities and avoid unnecessary modifications."
                    },
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse response
            can_solve_gap = False
            strategic_value = "SKIP"
            final_decision = "SKIP"
            selected_files = []
            reasoning = ""
            
            if "CAN_SOLVE_GAP:" in response_text:
                lines = response_text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if line.startswith("CAN_SOLVE_GAP:"):
                        can_solve_gap = "YES" in line.upper()
                    elif line.startswith("STRATEGIC_VALUE:"):
                        strategic_value = line.split(":", 1)[1].strip()
                    elif line.startswith("FINAL_DECISION:"):
                        final_decision = line.split(":", 1)[1].strip()
                    elif line.startswith("REASONING:"):
                        # Find reasoning section
                        reasoning_start = response_text.find("REASONING:")
                        if reasoning_start != -1:
                            reasoning = response_text[reasoning_start + 10:].strip()
                
                # Extract selected files if decision is to select
                if final_decision in ["SELECT_AS_PRIMARY", "SELECT_AS_FALLBACK"] and "SELECTED_FILES:" in response_text:
                    files_start = response_text.find("SELECTED_FILES:")
                    reasoning_start = response_text.find("REASONING:")
                    
                    if files_start != -1:
                        files_end = reasoning_start if reasoning_start != -1 else len(response_text)
                        files_section = response_text[files_start + 15:files_end].strip()
                        
                        for line in files_section.split('\n'):
                            line = line.strip()
                            if line and not line.startswith('#') and '/' in line:
                                selected_files.append(line)
            
            return type('RelationshipBatchResult', (), {
                'can_solve_telemetry_gap': can_solve_gap,
                'strategic_value': strategic_value,
                'final_decision': final_decision,
                'selected_files': selected_files,
                'reasoning': reasoning,
                'main_file': main_file_name,
                'total_files_analyzed': len(batch_context['files']),
                'raw_response': response_text
            })()
            
        except Exception as e:
            print(f"Error in relationship batch analysis: {e}")
            # Fallback: assume this batch cannot solve the gap
            return type('RelationshipBatchResult', (), {
                'can_solve_telemetry_gap': False,
                'selected_files': [],
                'reasoning': f"Error occurred during analysis: {e}",
                'main_file': main_file_name,
                'total_files_analyzed': len(batch_context.get('files', [])),
                'raw_response': str(e)
            })()


# def final_telemetry_file_selection(self, final_context):
#         """
#         Make final file selection using code graph relationships for comprehensive telemetry coverage.
        
#         This method performs the final selection considering both file content and code graph relationships
#         to ensure comprehensive telemetry coverage across related components. It aligns with the coding
#         instruction to find all span creation sites and ensure consistent instrumentation.
        
#         Args:
#             final_context: Dict containing telemetry_intent, files with content and relationships
            
#         Returns:
#             Object with selected_files list and reasoning_chain
#         """
#         # Prepare files summary for LLM
#         files_summary = []
#         for i, file_data in enumerate(final_context['files']):
#             file_summary = f"""
#     File {i+1}: {file_data['path'].name}
#     - Search Score: {file_data['search_score']}
#     - Search Strategy: {file_data['search_strategy']}
#     - Content Preview: {file_data['content'][:500]}...
#     - Relationships: {len(file_data.get('relationships', []))} related files
#     - Related Files: {', '.join([str(rel) for rel in file_data.get('relationships', [])[:3]])}"""
#             files_summary.append(file_summary)
        
#         prompt = f"""
#     You are an expert telemetry engineer selecting files for instrumentation enhancement. Your goal is to implement this requirement:

#     **TELEMETRY REQUIREMENT:**
#     Operation: {final_context['telemetry_intent']['operation']}
#     Category: {final_context['telemetry_intent']['category']} 
#     Description: {final_context['telemetry_intent']['description']}
#     Type: {final_context['telemetry_intent']['operation_type']}

#     **IMPLEMENTATION APPROACH:** {f"Direct Instrumentation - Modify files directly" if final_context.get('direct_instrumentation_focus', True) else "Helper Methods - Create reusable components"}

#     **CANDIDATE FILES ANALYSIS:**
#     {chr(10).join(files_summary)}

#     **SELECTION STRATEGY:**
    
#     Analyze each file's potential for implementing the telemetry requirement. Consider:

#     🎯 **Primary Selection Criteria:**
#     - **Relevance to Requirement**: How directly does this file relate to the telemetry operation described?
#     - **Implementation Feasibility**: Can the required telemetry enhancement be implemented in this file?
#     - **Existing Telemetry Patterns**: Does the file already have telemetry infrastructure (Activities, Spans, Tags)?
#     - **Business Logic Alignment**: Does the file handle the core functionality mentioned in the requirement?

#     🔍 **Code Analysis Indicators:**
#     - Telemetry infrastructure: StartActivity, ActivitySource, SetTag, Activity.Current
#     - HTTP handling: Middleware, Controllers, Handlers, Request processing
#     - Business operations: Service methods, API endpoints, Core logic
#     - Data flow: Components that process the data mentioned in the requirement

#     📊 **Context Considerations:**
#     - **Search Score**: Higher scores indicate better keyword/pattern matches
#     - **File Relationships**: Related files may need consistent instrumentation
#     - **Content Preview**: Actual code snippets showing telemetry opportunities
#     - **File Type**: Focus on implementation files rather than configuration

#     **YOUR TASK:**
#     Select the most appropriate files (up to {final_context.get('target_selection', 10)}) where the telemetry requirement can be effectively implemented. Prioritize files that:
#     1. Have clear connection to the telemetry operation
#     2. Already contain telemetry infrastructure or can easily accommodate it
#     3. Handle the business logic or data flow mentioned in the requirement
#     4. Provide the best ROI for telemetry enhancement

#     **RESPONSE FORMAT:**
#     SELECTED_FILES:
#     /path/to/file1.cs
#     /path/to/file2.cs
#     ...

#     REASONING:
#     Explain your selection logic, focusing on how these files enable the telemetry requirement implementation.
#     """

#         try:
#             response = self.client.chat.completions.create(
#                 model="o3",
#                 messages=[
#                     {
#                         "role": "system", 
#                         "content": "You are a senior telemetry engineer and code analyst specializing in OpenTelemetry instrumentation. You excel at understanding business requirements, analyzing codebases, and selecting the optimal files for telemetry enhancement. You consider both technical feasibility and business value when making selection decisions. Your expertise includes recognizing telemetry patterns, understanding code relationships, and ensuring comprehensive observability coverage."
#                     },
#                     {"role": "user", "content": prompt}
#                 ]
#             )
            
#             response_text = response.choices[0].message.content.strip()
            
#             # Parse response
#             selected_files = []
#             reasoning = ""
            
#             if "SELECTED_FILES:" in response_text and "REASONING:" in response_text:
#                 parts = response_text.split("REASONING:")
#                 files_section = parts[0].replace("SELECTED_FILES:", "").strip()
#                 reasoning = parts[1].strip()
                
#                 # Extract file paths
#                 for line in files_section.split('\n'):
#                     line = line.strip()
#                     if line and not line.startswith('#'):
#                         selected_files.append(line)
#             else:
#                 # Fallback parsing
#                 lines = response_text.split('\n')
#                 in_files_section = False
#                 for line in lines:
#                     line = line.strip()
#                     if "SELECTED_FILES:" in line:
#                         in_files_section = True
#                         continue
#                     elif "REASONING:" in line:
#                         in_files_section = False
#                         continue
#                     elif in_files_section and line and not line.startswith('#'):
#                         selected_files.append(line)
#                     elif not in_files_section and not line.startswith('#'):
#                         reasoning += line + " "
            
#             # Create reasoning chain
#             reasoning_chain = type('ReasoningChain', (), {
#                 'final_conclusion': reasoning or "Files selected based on telemetry enhancement potential and code relationships.",
#                 'selection_count': len(selected_files),
#                 'total_candidates': len(final_context['files']),
#                 'raw_response': response_text
#             })()
            
#             return type('FinalSelectionResult', (), {
#                 'selected_files': selected_files,
#                 'reasoning_chain': reasoning_chain,
#                 'selection_strategy': 'relationship_aware_direct_instrumentation'
#             })()
            
#         except Exception as e:
#             print(f"Error in final selection: {e}")
#             # Fallback: select files with highest search scores
#             fallback_files = sorted(final_context['files'], 
#                                 key=lambda f: f['search_score'], 
#                                 reverse=True)[:final_context.get('target_selection', 5)]
            
#             fallback_reasoning = type('ReasoningChain', (), {
#                 'final_conclusion': f"Error occurred: {e}. Selected top files by search score as fallback.",
#                 'selection_count': len(fallback_files),
#                 'total_candidates': len(final_context['files']),
#                 'raw_response': f"Fallback selection due to error: {e}"
#             })()
            
#             return type('FinalSelectionResult', (), {
#                 'selected_files': [str(f['path']) for f in fallback_files],
#                 'reasoning_chain': fallback_reasoning,
#                 'selection_strategy': 'fallback_score_based'
#             })()