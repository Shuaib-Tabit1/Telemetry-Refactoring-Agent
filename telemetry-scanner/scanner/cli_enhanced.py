#!/usr/bin/env python3
"""
Enhanced CLI for the Telemetry Refactoring Agent
Supports both original and enhanced workflows
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

# Original modules
from scanner.jira_client import get_formatted_ticket_text, clean_jira_text
from scanner.intent_builder import extract_intent
from scanner.project_utils import parse_dirs_proj
from scanner.context_finder import find_candidate_files
from scanner.config_finder import find_config_files
from scanner.static_analyzer import build_monorepo_graph, expand_with_code_graph
from scanner.patch_composer import select_files_for_edit, compose_patch
from scanner.writer import write_markdown

# Enhanced modules
try:
    from scanner.enhanced_intent_builder import EnhancedIntentBuilder
    from scanner.intelligent_search import IntelligentSearchEngine
    from scanner.advanced_code_graph import AdvancedCodeGraphAnalyzer
    from scanner.advanced_llm_reasoning import AdvancedLLMReasoner
    from scanner.pipeline_orchestrator import EnhancedOrchestrator
    from scanner.validation_framework import ValidationFramework
    ENHANCED_AVAILABLE = True
except ImportError as e:
    print(f"Enhanced modules not available: {e}")
    ENHANCED_AVAILABLE = False

async def run_enhanced_workflow(args):
    """Run the enhanced workflow with all new capabilities."""
    if not ENHANCED_AVAILABLE:
        print("ERROR: Enhanced modules are not available. Please check imports.")
        return False
    
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize enhanced components
    orchestrator = EnhancedOrchestrator(
        output_dir=out_dir,
        max_retries=args.max_retries,
        enable_cache=False,  # Force disable cache to avoid serialization issues
        parallel_workers=args.parallel_workers
    )
    
    intent_builder = EnhancedIntentBuilder()
    
    # Import constants from static_analyzer
    from .static_analyzer import ROSLYN_TOOL_PATH, CODE_GRAPH_PATH
    
    search_engine = IntelligentSearchEngine(args.repo_root, CODE_GRAPH_PATH)
    search_engine.signal_boost_log = True  # one run only; set back to False later
    code_analyzer = AdvancedCodeGraphAnalyzer(CODE_GRAPH_PATH, ROSLYN_TOOL_PATH)
    llm_reasoner = AdvancedLLMReasoner()
    validator = ValidationFramework(Path(args.repo_root))
    
    try:
        # Stage 1: Enhanced Ticket Processing
        print("🎯 Stage 1: Enhanced Ticket Analysis...")
        
        def fetch_ticket(ticket_key):
            if args.local_ticket:
                ticket_path = Path(ticket_key)
                if not ticket_path.exists():
                    raise FileNotFoundError(f"Local ticket file not found: {ticket_key}")
                return ticket_path.read_text(encoding="utf-8")
            else:
                raw_text = get_formatted_ticket_text(ticket_key)
                if not raw_text:
                    raise ValueError("Could not retrieve ticket text")
                return clean_jira_text(raw_text)
        
        ticket_result = await orchestrator.execute_stage(
            "fetch_ticket", fetch_ticket, args.ticket_key
        )
        
        if ticket_result.status.value != "completed":
            print(f"❌ Failed to fetch ticket: {ticket_result.error}")
            return False
        
        (out_dir / "cleaned_ticket.txt").write_text(ticket_result.result, encoding="utf-8")
        
        # Stage 2: Enhanced Intent Extraction
        print("🧠 Stage 2: Multi-Step Intent Extraction...")
        
        def extract_enhanced_intent(ticket_text):
            return intent_builder.extract_enhanced_intent(ticket_text)
        
        intent_result = await orchestrator.execute_stage(
            "extract_intent", extract_enhanced_intent, ticket_result.result
        )
        
        if intent_result.status.value != "completed":
            print(f"❌ Failed to extract intent: {intent_result.error}")
            return False
        
        enhanced_intent = intent_result.result
        (out_dir / "enhanced_intent.json").write_text(
            json.dumps(enhanced_intent.__dict__, indent=2, default=str), encoding="utf-8"
        )
        
        print(f"   Confidence: {enhanced_intent.confidence.value}")
        print(f"   Complexity: {enhanced_intent.complexity_score}/10")
        print(f"   Estimated Files: {enhanced_intent.estimated_files}")
        
        # Stage 3: Build Code Graph
        print("📊 Stage 3: Building Enhanced Code Graph...")
        
        def build_graph(dirs_proj_path):
            project_paths = parse_dirs_proj(Path(dirs_proj_path))
            if not project_paths:
                raise ValueError("No projects found in dirs.proj")
            build_monorepo_graph(project_paths)
            return project_paths
        
        graph_result = await orchestrator.execute_stage(
            "build_graph", build_graph, args.dirs_proj_path
        )
        
        if graph_result.status.value != "completed":
            print(f"❌ Failed to build code graph: {graph_result.error}")
            return False
        
        if args.build_graph_only:
            print("✅ Code graph built successfully. Exiting as requested.")
            orchestrator.save_stage_report()
            return True
        
        # Stage 4: Intelligent Search
        print("🔍 Stage 4: Intelligent Multi-Modal Search...")
        
        def intelligent_search(inputs):
            intent, repo_root = inputs
            # Convert EnhancedIntent object to dictionary for search engine
            intent_dict = intent.__dict__ if hasattr(intent, '__dict__') else intent
            return search_engine.multi_modal_search(
                intent=intent_dict,
                top_k=args.max_candidates
            )
        
        search_result = await orchestrator.execute_stage(
            "intelligent_search", 
            intelligent_search, 
            (enhanced_intent, args.repo_root)
        )
        
        if search_result.status.value != "completed":
            print(f"❌ Search failed: {search_result.error}")
            return False
        
        candidates = search_result.result
        print(f"   Found {len(candidates)} candidate files")
        
        # Stage 5: Advanced Code Analysis
        print("🏗️  Stage 5: Architectural Analysis...")
        
        def analyze_architecture(inputs):
            candidates, intent = inputs
            # Load the code graph first
            code_analyzer.load_and_analyze_graph()
            # Convert intent object to dict if needed
            intent_dict = intent.__dict__ if hasattr(intent, '__dict__') else intent
            return code_analyzer.analyze_impact(
                seed_files=[c.file_path for c in candidates],
                intent=intent_dict
            )
        
        analysis_result = await orchestrator.execute_stage(
            "analyze_architecture",
            analyze_architecture,
            (candidates, enhanced_intent)
        )
        
        if analysis_result.status.value != "completed":
            print(f"❌ Architecture analysis failed: {analysis_result.error}")
            return False
        
        architecture_analysis = analysis_result.result
        
        # Stage 6: Advanced LLM Reasoning
        print("🤖 Stage 6: Advanced Solution Generation...")
        
        def generate_solution(dummy_inputs):
            # Use closure to access the actual objects without serialization issues
            intent = enhanced_intent
            candidate_list = candidates
            analysis = architecture_analysis

            # Convert intent to dict if needed and handle enum serialization
            if hasattr(intent, '__dict__'):
                intent_dict = {}
                for key, value in intent.__dict__.items():
                    if hasattr(value, 'value'):  # Handle enum types
                        intent_dict[key] = value.value
                    else:
                        intent_dict[key] = value
            else:
                intent_dict = intent

            # Ensure repo_root is present for downstream repo-relative scoping
            from pathlib import Path
            intent_dict.setdefault("repo_root", str(Path(args.repo_root).resolve()))

            # Hard cap only — no extra prioritization heuristics
            LLM_FILE_CAP = 30

            selected_files = []
            for c in candidate_list[:LLM_FILE_CAP]:
                try:
                    file_content = c.file_path.read_text(encoding='utf-8', errors='ignore')
                    selected_files.append({
                        "path": c.file_path,
                        "content": file_content,
                        "relevance_score": c.relevance_score,
                        "reasoning": c.reasoning
                    })
                except Exception as e:
                    print(f"Could not read file {c.file_path}: {e}")
                    continue

            # Minimal reasoning chain stub
            from .advanced_llm_reasoning import ReasoningChain, ReasoningStep, ReasoningStrategy
            reasoning_chain = ReasoningChain(
                strategy=ReasoningStrategy.CHAIN_OF_THOUGHT,
                steps=[ReasoningStep(
                    step_number=1,
                    description="File selection",
                    reasoning=f"Selected the top {len(selected_files)} candidates by relevance (no central-file bias).",
                    conclusion="Proceed to patch generation with selected files.",
                    confidence=0.75,
                    evidence=["Ranking"]
                )],
                final_conclusion="Ready to generate patches",
                overall_confidence=0.75,
                alternative_approaches=["Manual implementation", "Configuration-based approach"]
            )

            patch_result = llm_reasoner.enhanced_patch_generation(
                intent=intent_dict,
                selected_files=selected_files,
                reasoning_chain=reasoning_chain
            )

            explanation, diff, updated_reasoning = patch_result
            return {
                "explanation": explanation,
                "diff": diff,
                "reasoning_chain": updated_reasoning,
                "selected_files": selected_files
            }

        
        solution_result = await orchestrator.execute_stage(
            "generate_solution",
            generate_solution,
            "simple_string"  # Use simple string to avoid serialization issues
        )
        
        if solution_result.status.value != "completed":
            print(f"❌ Solution generation failed: {solution_result.error}")
            return False
        
        solution = solution_result.result
        
        # Stage 7: Validation
        print("✅ Stage 7: Comprehensive Validation...")
        
        def validate_solution(solution):
            # Convert intent to dict if needed
            intent_dict = enhanced_intent.__dict__ if hasattr(enhanced_intent, '__dict__') else enhanced_intent
            
            return validator.run_comprehensive_validation(
                intent=intent_dict,
                original_files=solution['selected_files'],
                generated_patch=solution['diff']
            )
        
        validation_result = await orchestrator.execute_stage(
            "validate_solution", validate_solution, solution
        )
        
        if validation_result.status.value == "completed":
            validation = validation_result.result
            print(f"   Overall Score: {validation.overall_score}/10")
            print(f"   Risk Assessment: {validation.risk_assessment}")
            print(f"   Recommendations: {len(validation.recommendations)} items")
        else:
            print(f" Validation encountered issues: {validation_result.error}")
            # Continue anyway since validation is not critical for patch generation
        
        # Write final outputs
        write_markdown(out_dir, "enhanced_remediation.md", solution.get('explanation', ''))
        
        if 'diff' in solution:
            (out_dir / "solution.diff").write_text(solution['diff'], encoding="utf-8")
        
        # Save execution report
        orchestrator.save_stage_report()
        
        print("🎉 Enhanced pipeline completed successfully!")
        print(f"📁 Results saved to: {out_dir}")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced workflow failed: {e}")
        orchestrator.save_stage_report()
        return False

def run_original_workflow(args):
    """Run the original workflow (your existing code)."""
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print("Running original workflow...")
    
    # Original workflow code (unchanged)
    ticket_text = None
    if args.local_ticket:
        try:
            print(f"Reading local ticket file '{args.ticket_key}'...")
            ticket_path = Path(args.ticket_key)
            if ticket_path.exists():
                ticket_text = ticket_path.read_text(encoding="utf-8")
            else:
                print(f"Local ticket file not found: {args.ticket_key}")
                return
        except Exception as e:
            print(f"Error reading local ticket file: {e}")
            return
    else:
        print(f"Fetching and formatting Jira ticket '{args.ticket_key}'...")
        raw_ticket_text = get_formatted_ticket_text(args.ticket_key)
        if not raw_ticket_text:
            print("Could not retrieve ticket text. Exiting.")
            return
        ticket_text = clean_jira_text(raw_ticket_text)
    
    (out_dir / "cleaned_ticket.txt").write_text(ticket_text, encoding="utf-8")

    print("\nStep 1: Planning - Extracting intent from Jira ticket...")
    intent = extract_intent(ticket_text)
    (out_dir / "intent.json").write_text(json.dumps(intent, indent=2))

    print("\nStep 2: Indexing - Building full monorepo Code Graph...")
    project_paths = parse_dirs_proj(Path(args.dirs_proj_path))
    if not project_paths:
        print("Could not find any projects in dirs.proj. Exiting.")
        return
    
    print(f"Found {len(project_paths)} projects in dirs.proj.")
    build_monorepo_graph(project_paths)
    
    if args.build_graph_only:
        print("\nMonorepo graph built successfully. Exiting as requested.")
        return
    
    print("\nStep 3: Investigating - Running parallel searches...")
    semantic_candidates = find_candidate_files(args.repo_root, intent, top_k=30)
    config_candidates = find_config_files(args.repo_root)
    static_candidates = []

    seed_files = {}
    for f in static_candidates + config_candidates + semantic_candidates:
        if f not in seed_files:
            seed_files[f] = True
    
    print("\nStep 4: Expanding context with Code Graph...")
    candidate_list = expand_with_code_graph(list(seed_files.keys()))
    print(f"Found a total of {len(candidate_list)} unique candidate files to analyze.")
    (out_dir / "candidate_list.txt").write_text("\n".join(str(p) for p in candidate_list))

    print("\nStep 5: Deciding - Analyzing candidates in batches...")
    selected_files = []
    for i in range(0, len(candidate_list), args.batch_size):
        batch = candidate_list[i : i + args.batch_size]
        print(f"--> Analyzing batch {i//args.batch_size + 1} of {len(batch)} files...")
        
        candidate_contexts = []
        for path in batch:
            try:
                content = path.read_text(encoding='utf-8')
                candidate_contexts.append({'path': path, 'content': content})
            except Exception as e:
                print(f"Warning: Could not read file {path.name}: {e}")
        
        if not candidate_contexts: continue

        files_to_edit = select_files_for_edit(intent, candidate_contexts)
        if files_to_edit:
            selected_files = files_to_edit
            break

    if selected_files:
        print(f"\nStep 6: Coding - Final selection made. Generating patch for {len(selected_files)} file(s)...")
        final_contexts = []
        for path in selected_files:
            try:
                content = path.read_text(encoding='utf-8')
                final_contexts.append({'path': path, 'content': content})
            except Exception as e:
                 print(f"Error reading final file {path.name}: {e}")

        if final_contexts:
            diff, md = compose_patch(intent, final_contexts)
            write_markdown(out_dir, "remediation.md", f"```diff\n{diff}\n```\n\n{md}")
            print(f"Unified diff and explanation written to {out_dir / 'remediation.md'}")
    else:
        print("\nCould not find a suitable file to modify after checking all candidates.")

    print("\nScan complete.")

def main():
    parser = argparse.ArgumentParser("Enhanced Telemetry Refactoring Agent")
    
    # Original arguments
    parser.add_argument("--ticket-key", required=True, help="The Jira ticket key or local file path")
    parser.add_argument("--repo-root", required=True, help="Path to the root of the monorepo")
    parser.add_argument("--dirs-proj-path", required=True, help="Path to the dirs.proj file")
    parser.add_argument("--output", default="runs/demo", help="Output folder")
    parser.add_argument("--batch-size", type=int, default=10, help="Number of files to check per iteration")
    parser.add_argument("--local-ticket", action='store_true', help="Use local file for ticket text")
    parser.add_argument("--build-graph-only", action='store_true', help="Only build the code graph and exit")
    
    # Enhanced workflow options
    parser.add_argument("--enhanced", action='store_true', help="Use the enhanced workflow (recommended)")
    parser.add_argument("--max-retries", type=int, default=3, help="Maximum retries for failed stages")
    parser.add_argument("--enable-cache", action='store_true', default=False, help="Enable result caching")
    parser.add_argument("--parallel-workers", type=int, default=4, help="Number of parallel workers")
    parser.add_argument("--max-candidates", type=int, default=50, help="Maximum candidate files to analyze")
    
    args = parser.parse_args()
    
    # Show workflow selection
    if args.enhanced:
        if not ENHANCED_AVAILABLE:
            print("❌ Enhanced workflow requested but modules are not available.")
            print("   Falling back to original workflow...")
            run_original_workflow(args)
        else:
            print("🚀 Running Enhanced Telemetry Refactoring Agent")
            print("="*60)
            success = asyncio.run(run_enhanced_workflow(args))
            sys.exit(0 if success else 1)
    else:
        print("📝 Running Original Telemetry Refactoring Agent")
        print("="*50)
        run_original_workflow(args)

if __name__ == "__main__":
    main()
