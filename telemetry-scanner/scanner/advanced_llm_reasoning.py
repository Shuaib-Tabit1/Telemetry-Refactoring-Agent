"""
Advanced LLM Reasoning System with Chain-of-Thought, validation, and self-correction.
"""
import json
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
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

class ConfidenceLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

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

@dataclass
class ValidationResult:
    is_valid: bool
    confidence_score: float
    issues_found: List[str]
    suggested_improvements: List[str]

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
2. **Planning**: What approach would work best?
3. **Implementation**: What specific changes are needed?
4. **Validation**: How can we ensure this works correctly?

For each step, provide:
- Clear reasoning
- Specific evidence from the context
- Confidence level (0.0-1.0)
- Alternative approaches considered

Be thorough and systematic."""

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
    
    def _tree_of_thoughts_reasoning(self, task: str, context: Dict) -> ReasoningChain:
        """Implement tree-of-thoughts reasoning with multiple branches."""
        
        prompt = f"""Explore multiple solution paths for this telemetry implementation task.

TASK: {task}
CONTEXT: {safe_json_dumps(context, indent=2)}

Generate 3 different solution approaches:

1. **Conservative Approach**: Minimal changes, maximum safety
2. **Optimal Approach**: Best practices, moderate complexity  
3. **Innovative Approach**: Advanced techniques, higher complexity

For each approach, evaluate:
- Implementation effort
- Risk level
- Performance impact
- Maintainability
- Telemetry coverage

Recommend the best approach with detailed justification."""

        try:
            response = self.client.chat.completions.create(
                model="o3",
                messages=[
                    {"role": "system", "content": "You are an expert software architect specializing in observability systems."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            reasoning_text = response.choices[0].message.content
            steps = self._parse_tree_reasoning(reasoning_text)
            
            return ReasoningChain(
                strategy=ReasoningStrategy.TREE_OF_THOUGHTS,
                steps=steps,
                final_conclusion=self._extract_final_conclusion(reasoning_text),
                overall_confidence=self._calculate_overall_confidence(steps),
                alternative_approaches=self._extract_alternatives(reasoning_text)
            )
            
        except Exception as e:
            return self._fallback_reasoning_chain(str(e))
    
    def _reflection_reasoning(self, task: str, context: Dict) -> ReasoningChain:
        """Implement reflection-based reasoning with self-critique."""
        
        # First pass: Initial reasoning
        initial_prompt = f"""Analyze this telemetry implementation task:

TASK: {task}
CONTEXT: {safe_json_dumps(context, indent=2)}

Provide your initial analysis and solution approach."""

        # Second pass: Self-reflection
        reflection_prompt = """Now, critically examine your initial analysis:

1. What assumptions did you make?
2. What could go wrong with this approach?
3. What did you miss or overlook?
4. How could the solution be improved?
5. What additional considerations are needed?

Provide a refined solution based on this reflection."""

        try:
            # Initial reasoning
            initial_response = self.client.chat.completions.create(
                model="o3",
                messages=[
                    {"role": "system", "content": "You are an expert telemetry engineer."},
                    {"role": "user", "content": initial_prompt}
                ]
            )
            
            initial_reasoning = initial_response.choices[0].message.content
            
            # Reflection
            reflection_response = self.client.chat.completions.create(
                model="o3", 
                messages=[
                    {"role": "system", "content": "You are an expert telemetry engineer."},
                    {"role": "user", "content": initial_prompt},
                    {"role": "assistant", "content": initial_reasoning},
                    {"role": "user", "content": reflection_prompt}
                ]
            )
            
            reflection_reasoning = reflection_response.choices[0].message.content
            
            # Combine into reasoning steps
            steps = [
                ReasoningStep(
                    step_number=1,
                    description="Initial Analysis",
                    reasoning=initial_reasoning,
                    conclusion="Initial solution approach",
                    confidence=0.7,
                    evidence=["Context analysis"]
                ),
                ReasoningStep(
                    step_number=2,
                    description="Self-Reflection",
                    reasoning=reflection_reasoning,
                    conclusion="Refined solution approach",
                    confidence=0.9,
                    evidence=["Critical analysis", "Assumption validation"]
                )
            ]
            
            return ReasoningChain(
                strategy=ReasoningStrategy.REFLECTION,
                steps=steps,
                final_conclusion=self._extract_final_conclusion(reflection_reasoning),
                overall_confidence=0.85,
                alternative_approaches=self._extract_alternatives(reflection_reasoning)
            )
            
        except Exception as e:
            return self._fallback_reasoning_chain(str(e))
    
    def _self_correction_reasoning(self, task: str, context: Dict) -> ReasoningChain:
        """Implement self-correction reasoning with iterative improvement."""
        
        prompt = f"""Solve this telemetry implementation task using self-correction:

TASK: {task}
CONTEXT: {safe_json_dumps(context, indent=2)}

Process:
1. Provide initial solution
2. Identify potential issues
3. Correct and improve
4. Validate the final solution

Be explicit about what you're correcting and why."""

        try:
            response = self.client.chat.completions.create(
                model="o3",
                messages=[
                    {"role": "system", "content": "You are an expert software engineer who excels at self-correction and iterative improvement."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            reasoning_text = response.choices[0].message.content
            steps = self._parse_correction_steps(reasoning_text)
            
            return ReasoningChain(
                strategy=ReasoningStrategy.SELF_CORRECTION,
                steps=steps,
                final_conclusion=self._extract_final_conclusion(reasoning_text),
                overall_confidence=self._calculate_overall_confidence(steps),
                alternative_approaches=self._extract_alternatives(reasoning_text)
            )
            
        except Exception as e:
            return self._fallback_reasoning_chain(str(e))
    
    def validate_reasoning(self, reasoning_chain: ReasoningChain, original_context: Dict) -> ValidationResult:
        """Validate the quality and correctness of reasoning."""
        
        validation_prompt = f"""Evaluate this reasoning chain for quality and correctness:

REASONING STRATEGY: {reasoning_chain.strategy.value}
STEPS: {len(reasoning_chain.steps)}
FINAL CONCLUSION: {reasoning_chain.final_conclusion}
CONFIDENCE: {reasoning_chain.overall_confidence}

ORIGINAL CONTEXT: {safe_json_dumps(original_context, indent=2)}

Assess:
1. Logical consistency
2. Evidence quality
3. Conclusion validity
4. Completeness
5. Potential issues

Provide validation score (0.0-1.0) and specific feedback."""

        try:
            response = self.client.chat.completions.create(
                model="o3",
                messages=[
                    {"role": "system", "content": "You are an expert reasoning validator with deep knowledge of logic and software engineering."},
                    {"role": "user", "content": validation_prompt}
                ]
            )
            
            validation_text = response.choices[0].message.content
            
            return ValidationResult(
                is_valid=self._extract_validity(validation_text),
                confidence_score=self._extract_confidence_score(validation_text),
                issues_found=self._extract_issues(validation_text),
                suggested_improvements=self._extract_improvements(validation_text)
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=True,
                confidence_score=0.5,
                issues_found=[f"Validation error: {str(e)}"],
                suggested_improvements=["Manual validation recommended"]
            )
    
    def self_correct_reasoning(self, reasoning_chain: ReasoningChain, 
                             validation_result: ValidationResult) -> ReasoningChain:
        """Self-correct reasoning based on validation feedback."""
        
        if validation_result.is_valid and validation_result.confidence_score > 0.8:
            return reasoning_chain
        
        correction_prompt = f"""Improve this reasoning chain based on validation feedback:

ORIGINAL REASONING: {reasoning_chain.final_conclusion}
ISSUES FOUND: {', '.join(validation_result.issues_found)}
SUGGESTIONS: {', '.join(validation_result.suggested_improvements)}

Provide corrected reasoning that addresses these issues."""

        try:
            response = self.client.chat.completions.create(
                model="o3",
                messages=[
                    {"role": "system", "content": "You are an expert at reasoning improvement and self-correction."},
                    {"role": "user", "content": correction_prompt}
                ]
            )
            
            corrected_text = response.choices[0].message.content
            
            # Add a correction step
            correction_step = ReasoningStep(
                step_number=len(reasoning_chain.steps) + 1,
                description="Self-Correction",
                reasoning=corrected_text,
                conclusion="Improved reasoning based on validation",
                confidence=0.9,
                evidence=["Validation feedback", "Error correction"]
            )
            
            corrected_steps = reasoning_chain.steps + [correction_step]
            
            return ReasoningChain(
                strategy=reasoning_chain.strategy,
                steps=corrected_steps,
                final_conclusion=self._extract_final_conclusion(corrected_text),
                overall_confidence=min(reasoning_chain.overall_confidence + 0.2, 1.0),
                alternative_approaches=reasoning_chain.alternative_approaches
            )
            
        except Exception as e:
            return reasoning_chain  # Return original if correction fails
    
    def enhanced_file_selection(self, intent: Dict, candidate_files: List[Dict]) -> Tuple[List[str], ReasoningChain]:
        """Enhanced file selection using chain-of-thought reasoning."""
        
        context = {
            "intent": intent,
            "candidate_count": len(candidate_files),
            "files": [{"path": f["path"], "relevance": f.get("relevance_score", 0)} for f in candidate_files[:20]]
        }
        
        reasoning = self.analyze_with_chain_of_thought(
            task="Select the most relevant files for telemetry implementation",
            context=context,
            strategy=ReasoningStrategy.CHAIN_OF_THOUGHT
        )
        
        # Extract file selections from reasoning
        selected_files = []
        for file_info in candidate_files[:10]:  # Top 10 candidates
            if self._should_include_file(file_info, reasoning):
                selected_files.append(file_info["path"])
        
        return selected_files, reasoning
    
    def enhanced_patch_generation(self, intent: Dict, selected_files: List[Dict], 
                                 reasoning_chain: ReasoningChain) -> Tuple[str, str, ReasoningChain]:
        """Generate patches with enhanced reasoning and validation."""
        
        # Prepare context for patch generation
        context = {
            "intent": intent,
            "files": {f["path"].name: f["content"] for f in selected_files},
            "previous_reasoning": reasoning_chain.final_conclusion
        }
        
        # Use reasoning to plan the patch
        patch_reasoning = self.analyze_with_chain_of_thought(
            task="Generate a comprehensive code patch that implements the telemetry requirements",
            context=context,
            strategy=ReasoningStrategy.CHAIN_OF_THOUGHT
        )
        
        # Generate the actual patch
        patch_prompt = f"""
Based on your detailed reasoning, generate a precise unified diff to implement the telemetry changes.

REASONING PLAN:
{patch_reasoning.final_conclusion}

FILES AVAILABLE:
{safe_json_dumps({f["path"].name: f["content"][:500] + "..." if len(f["content"]) > 500 else f["content"] for f in selected_files}, indent=2)}

REQUIREMENTS:
{safe_json_dumps(intent, indent=2)}

Generate:
1. A clear explanation of the changes
2. A unified diff format patch
3. Implementation notes and considerations

Format the response as:
## Explanation
[Clear explanation]

## Patch
```diff
[Unified diff]
```

## Notes
[Implementation notes]
"""

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
    
    def _parse_tree_reasoning(self, text: str) -> List[ReasoningStep]:
        """Parse tree-of-thoughts reasoning."""
        return self._parse_reasoning_steps(text)  # Simplified for now
    
    def _parse_correction_steps(self, text: str) -> List[ReasoningStep]:
        """Parse self-correction reasoning."""
        return self._parse_reasoning_steps(text)  # Simplified for now
    
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
    
    def _extract_validity(self, text: str) -> bool:
        """Extract validity assessment from validation text."""
        return not any(word in text.lower() for word in ['invalid', 'incorrect', 'wrong', 'false'])
    
    def _extract_confidence_score(self, text: str) -> float:
        """Extract confidence score from validation text."""
        # Look for numerical scores
        import re
        scores = re.findall(r'(\d+\.?\d*)', text)
        if scores:
            try:
                score = float(scores[0])
                return score if score <= 1.0 else score / 10.0
            except:
                pass
        return 0.7  # Default confidence
    
    def _extract_issues(self, text: str) -> List[str]:
        """Extract issues from validation text."""
        issues = []
        lines = text.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['issue', 'problem', 'error', 'concern']):
                issues.append(line.strip())
        
        return issues
    
    def _extract_improvements(self, text: str) -> List[str]:
        """Extract improvement suggestions from validation text."""
        improvements = []
        lines = text.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['improve', 'suggest', 'recommend', 'enhance']):
                improvements.append(line.strip())
        
        return improvements
    
    def _should_include_file(self, file_info: Dict, reasoning: ReasoningChain) -> bool:
        """Determine if a file should be included based on reasoning."""
        # Simplified decision logic
        return file_info.get("relevance_score", 0) > 0.6
    
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
