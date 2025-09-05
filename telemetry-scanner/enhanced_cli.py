"""
Enhanced CLI with advanced orchestration and all new features integrated.
"""
import argparse
import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Optional

# Import enhanced modules
from scanner.pipeline_orchestrator import EnhancedOrchestrator, StageStatus
from scanner.enhanced_intent_builder import EnhancedIntentBuilder, IntentConfidence
from scanner.intelligent_search import IntelligentSearchEngine
from scanner.advanced_code_graph import AdvancedCodeGraphAnalyzer
from scanner.advanced_llm_reasoning import AdvancedLLMReasoner, ReasoningStrategy

# Import existing modules
from scanner.jira_client import get_formatted_ticket_text, clean_jira_text
from scanner.project_utils import parse_dirs_proj
from scanner.static_analyzer import build_monorepo_graph
from scanner.writer import write_markdown

class EnhancedTelemetryAgent:
    """Enhanced Telemetry Refactoring Agent with advanced capabilities."""
    
    def __init__(self, args):
        self.args = args
        self.output_dir = Path(args.output)
        self.orchestrator = EnhancedOrchestrator(
            self.output_dir,
            max_retries=args.max_retries,
            enable_cache=args.enable_cache,
            parallel_workers=args.parallel_workers
        )
        
        # Initialize enhanced components
        self.intent_builder = EnhancedIntentBuilder()
        self.search_engine = None  # Will be initialized after repo setup
        self.graph_analyzer = None  # Will be initialized after graph building
        self.llm_reasoner = AdvancedLLMReasoner()
    
    async def run_enhanced_pipeline(self) -> None:
        """Run the enhanced telemetry refactoring pipeline."""
        
        print("🚀 Starting Enhanced Telemetry Refactoring Agent")
        print(f"Output directory: {self.output_dir}")
        
        try:
            # Stage 1: Ticket Processing and Intent Extraction
            await self._stage_ticket_processing()
            
            # Stage 2: Repository Analysis and Graph Building
            await self._stage_repository_analysis()
            
            # Stage 3: Enhanced Multi-Modal Search
            await self._stage_intelligent_search()
            
            # Stage 4: Batch-Based LLM Selection and Patch Generation
            await self._stage_reasoning_and_generation()
                    
            # Stage 5 : Report Generation
            await self._stage_report_generation()
            
        except Exception as e:
            print(f"Pipeline failed: {e}")
            raise
        finally:
            # Save execution report
            self.orchestrator.save_stage_report()
            print(f"Execution report saved to {self.output_dir / 'pipeline_report.json'}")
    
    # ...existing code for stages 1-3...
    async def _stage_ticket_processing(self) -> None:
        """Stage 1: Enhanced ticket processing and intent extraction."""
        
        def process_ticket(args):
            if args.local_ticket:
                ticket_path = Path(args.ticket_key)
                if not ticket_path.exists():
                    raise FileNotFoundError(f"Local ticket file not found: {args.ticket_key}")
                raw_text = ticket_path.read_text(encoding="utf-8")
            else:
                raw_text = get_formatted_ticket_text(args.ticket_key)
                if not raw_text:
                    raise ValueError("Could not retrieve ticket text")
                raw_text = clean_jira_text(raw_text)
            
            return raw_text
        
        def extract_enhanced_intent(ticket_text):
            # Build contextual information for better intent extraction
            context = {
                "timestamp": time.time(),
                "ticket_source": "local" if self.args.local_ticket else "jira",
                "agent_version": "enhanced_v1.0"
            }
            
            enhanced_intent = self.intent_builder.extract_enhanced_intent(ticket_text, context)
            return enhanced_intent
        
        # Execute ticket processing with orchestration
        ticket_result = await self.orchestrator.execute_stage(
            "ticket_processing",
            process_ticket,
            self.args
        )
        
        if ticket_result.status != StageStatus.COMPLETED:
            raise RuntimeError(f"Ticket processing failed: {ticket_result.error}")
        
        ticket_text = ticket_result.result
        (self.output_dir / "cleaned_ticket.txt").write_text(ticket_text, encoding="utf-8")
        
        # Extract enhanced intent
        intent_result = await self.orchestrator.execute_stage(
            "intent_extraction",
            extract_enhanced_intent,
            ticket_text,
            dependencies=["ticket_processing"]
        )
        
        if intent_result.status != StageStatus.COMPLETED:
            raise RuntimeError(f"Intent extraction failed: {intent_result.error}")
        
        self.enhanced_intent = intent_result.result
        
        # Save enhanced intent
        intent_data = {
            "basic_intent": {
                "issue_category": self.enhanced_intent.issue_category,
                "static_analysis_query": self.enhanced_intent.static_analysis_query,
                "semantic_description": self.enhanced_intent.semantic_description,
                "search_keywords": self.enhanced_intent.search_keywords,
                "telemetry_operation": self.enhanced_intent.telemetry_operation
            },
            "enhanced_analysis": {
                "confidence": self.enhanced_intent.confidence.value,
                "operation_type": self.enhanced_intent.operation_type.value,
                "complexity_score": self.enhanced_intent.complexity_score,
                "estimated_files": self.enhanced_intent.estimated_files,
                "validation_issues": self.enhanced_intent.validation_result.issues,
                "suggestions": self.enhanced_intent.validation_result.suggestions,
                "sub_tasks": self.enhanced_intent.sub_tasks,
                "contextual_hints": self.enhanced_intent.contextual_hints
            }
        }
        
        (self.output_dir / "enhanced_intent.json").write_text(
            json.dumps(intent_data, indent=2), encoding="utf-8"
        )
        
        print(f"✅ Intent extracted with {self.enhanced_intent.confidence.value} confidence")
        print(f"📊 Complexity Score: {self.enhanced_intent.complexity_score}/10")
        print(f"📁 Estimated Files: {self.enhanced_intent.estimated_files}")
    
    async def _stage_repository_analysis(self) -> None:
        """Stage 2: Repository analysis and advanced graph building."""
        
        def parse_projects(dirs_proj_path):
            project_paths = parse_dirs_proj(Path(dirs_proj_path))
            if not project_paths:
                raise ValueError("Could not find any projects in dirs.proj")
            return project_paths
        
        def build_enhanced_graph(project_paths):
            print(f"Building code graph for {len(project_paths)} projects...")
            build_monorepo_graph(project_paths)
            
            from scanner.static_analyzer import CODE_GRAPH_PATH
            
            # Initialize advanced graph analyzer
            self.graph_analyzer = AdvancedCodeGraphAnalyzer(
                CODE_GRAPH_PATH,
                "~/Documents/TRA/CodeGraphBuilder/bin/Release/net9.0/CodeGraphBuilder.dll"
            )
            self.graph_analyzer.load_and_analyze_graph()
            
            return {"projects_count": len(project_paths), "graph_loaded": True}
        
        # Parse projects
        projects_result = await self.orchestrator.execute_stage(
            "project_parsing",
            parse_projects,
            self.args.dirs_proj_path
        )
        
        if projects_result.status != StageStatus.COMPLETED:
            raise RuntimeError(f"Project parsing failed: {projects_result.error}")
        
        project_paths = projects_result.result
        print(f"📁 Found {len(project_paths)} projects")
        
        # Build enhanced graph (always needed for analysis)
        graph_result = await self.orchestrator.execute_stage(
            "graph_building",
            build_enhanced_graph,
            project_paths,
            dependencies=["project_parsing"]
        )
        
        if graph_result.status != StageStatus.COMPLETED:
            raise RuntimeError(f"Graph building failed: {graph_result.error}")
        
        # If only building graph, exit here
        if self.args.build_graph_only:
            print("✅ Enhanced code graph built successfully")
            return
        
        # Initialize search engine with proper code graph path
        from scanner.static_analyzer import CODE_GRAPH_PATH
        self.search_engine = IntelligentSearchEngine(
            self.args.repo_root,
            CODE_GRAPH_PATH
        )
        
        print("✅ Repository analysis completed")

    async def _stage_intelligent_search(self) -> None:
        """Stage 3: Enhanced multi-modal search."""
        
        def perform_intelligent_search(intent_data):
            # Convert enhanced intent back to basic format for search
            basic_intent = {
                "issue_category": intent_data.issue_category,
                "static_analysis_query": intent_data.static_analysis_query,
                "semantic_description": intent_data.semantic_description,
                "search_keywords": intent_data.search_keywords,
                "telemetry_operation": intent_data.telemetry_operation
            }
            
            # Perform multi-modal search
            search_results = self.search_engine.multi_modal_search(
                basic_intent, 
                top_k=self.args.max_candidates
            )
            
            return search_results
        
        search_result = await self.orchestrator.execute_stage(
            "intelligent_search",
            perform_intelligent_search,
            self.enhanced_intent,
            dependencies=["intent_extraction"]
        )
        
        if search_result.status != StageStatus.COMPLETED:
            raise RuntimeError(f"Intelligent search failed: {search_result.error}")
        
        self.search_results = search_result.result
        
        # Save search results
        search_data = [
            {
                "file_path": str(result.file_path),
                "strategy": result.strategy.value,
                "relevance_score": result.relevance_score,
                "reasoning": result.reasoning,
                "matching_patterns": result.matching_patterns,
                "confidence": result.confidence
            }
            for result in self.search_results
        ]
        
        (self.output_dir / "search_results.json").write_text(
            json.dumps(search_data, indent=2), encoding="utf-8"
        )
        
        print(f"🔍 Found {len(self.search_results)} candidate files")
        print(f"🎯 Top result: {self.search_results[0].file_path.name} (score: {self.search_results[0].relevance_score})")
    
    async def _stage_reasoning_and_generation(self) -> None:
        """Stage 4: Batch-based LLM file selection and patch generation with direct instrumentation focus."""
        
        # Execute batch filtering
        batch_result = await self.orchestrator.execute_stage(
            "batch_filtering",
            self.batch_filter_candidates,
            self.search_results  # Use ALL search results, not filtered subset
        )
        
        if batch_result.status != StageStatus.COMPLETED:
            raise RuntimeError(f"Batch filtering failed: {batch_result.error}")
        
        promising_files = batch_result.result
        
        # Execute final selection
        selection_result = await self.orchestrator.execute_stage(
            "final_selection",
            self.final_selection_with_relationships,
            promising_files
        )
        
        if selection_result.status != StageStatus.COMPLETED:
            raise RuntimeError(f"Final selection failed: {selection_result.error}")
        
        self.selected_files, self.reasoning_chain = selection_result.result
        
        # Execute patch generation
        generation_result = await self.orchestrator.execute_stage(
            "patch_generation",
            self.generate_enhanced_patch,
            (self.selected_files, self.reasoning_chain)
        )
        
        if generation_result.status != StageStatus.COMPLETED:
            raise RuntimeError(f"Patch generation failed: {generation_result.error}")

        self.generation_result = generation_result.result
        
        # Save results
        batch_summary = {
            "total_search_results": len(self.search_results),
            "promising_files_found": len(promising_files),
            "final_files_selected": len(self.selected_files),
            "strategy_used": self.generation_result.get("strategy_used", "direct"),
            "selection_efficiency": f"{len(self.selected_files)/len(self.search_results)*100:.1f}%",
            "files_selected": [str(f) for f in self.generation_result.get("selected_files", [])],
            "diff_length": len(self.generation_result.get("diff", "")),
            "explanation_length": len(self.generation_result.get("explanation", ""))
        }
        
        (self.output_dir / "batch_selection_summary.json").write_text(
            json.dumps(batch_summary, indent=2), encoding="utf-8"
        )
        
        if self.generation_result.get("selected_files"):
            print(f" Selected {len(self.generation_result['selected_files'])} files for direct instrumentation")
            print(f" Generated patch with {len(self.generation_result.get('diff', '').splitlines())} lines")
        else:
            print(" No files selected for modification")

    def batch_filter_candidates(self, search_results):
        """
        Filter search results in batches using LLM reasoning.
        
        This function processes ALL search results (not just top scoring ones) in manageable batches,
        allowing the LLM to evaluate each file's potential for telemetry enhancement based on the
        specific ticket requirements. This aligns with the coding instructions for comprehensive
        direct instrumentation coverage.
        
        Args:
            search_results: ALL search results from Stage 3 intelligent search
            
        Returns:
            List of promising files that could benefit from telemetry enhancement
        """
        # Process ALL search results in batches (not just top scoring ones)
        batch_size = 15 # Use the argument instead of hardcoding
        batches = [search_results[i:i+batch_size] for i in range(0, len(search_results), batch_size)]
        
        print(f"🔍 Processing {len(search_results)} search results in {len(batches)} batches of {batch_size}")
        print(f"📊 Using ALL search results (not just high-scoring ones)")
        
        promising_files = []
        
        # Process each batch with LLM reasoning
        for i, batch in enumerate(batches):
            print(f"   Processing batch {i+1}/{len(batches)}...")
            
            # Prepare batch context with telemetry intent
            batch_context = {
                "telemetry_intent": {
                    "operation": self.enhanced_intent.telemetry_operation,
                    "category": self.enhanced_intent.issue_category,
                    "description": self.enhanced_intent.semantic_description,
                    "operation_type": self.enhanced_intent.operation_type.value
                },
                "files": [
                    {
                        "path": str(result.file_path),
                        "relevance_score": result.relevance_score,
                        "search_strategy": result.strategy.value,
                        "search_reasoning": result.reasoning,
                        "matching_patterns": result.matching_patterns
                    }
                    for result in batch
                ]
            }
            
            # LLM call: Filter this batch for telemetry enhancement potential
            # This is generic for all telemetry types (spans, metrics, logs, custom)
            batch_promising = self.llm_reasoner.filter_batch_for_telemetry_enhancement(
                batch_context
            )
            
            # Add promising files from this batch
            for file_path in batch_promising.selected_files:
                # Find the original search result to preserve metadata
                for result in batch:
                    if str(result.file_path) == file_path:
                        promising_files.append(result)
                        print(f"     ✅ Selected: {result.file_path.name} (score: {result.relevance_score})")
                        break
        
        print(f" Total promising files from all batches: {len(promising_files)}")
        print(f"Processed {len(search_results)} files, selected {len(promising_files)} ({len(promising_files)/len(search_results)*100:.1f}%)")
        
        # Limit to reasonable number for final selection (but don't use arbitrary score cutoffs)
        if len(promising_files) > 30:
            # Sort by combination of LLM selection + search relevance
            promising_files.sort(key=lambda f: f.relevance_score, reverse=True)
            promising_files = promising_files[:30]
            print(f" Limited to top 30 by search relevance for final selection")
        
        return promising_files

    def _apply_strategic_llm_filter(self, candidate_files):
        """
        Use LLM to strategically filter candidate files to select the most optimal ones.
        
        This method asks the LLM to choose 1-3 files from the candidates that can
        solve the telemetry requirement with minimal changes and maximum coverage.
        """
        print(f"Asking LLM to strategically filter {len(candidate_files)} candidate files...")
        
        # Prepare file summaries for LLM analysis
        file_summaries = []
        for i, file_data in enumerate(candidate_files, 1):
            file_summary = f"""
File {i}: {file_data['path'].name}
- Full Path: {file_data['path']}
- Full Content: {file_data['content']}
- Selection Reasoning: {file_data.get('search_reasoning', 'N/A')}
- Is Main File: {file_data.get('is_main_file', False)}"""
            file_summaries.append(file_summary)
        
        prompt = f"""
You are a senior software architect analyzing telemetry implementation options.

**TELEMETRY REQUIREMENT:**
{self.enhanced_intent.semantic_description}
Operation: {self.enhanced_intent.telemetry_operation}
Type: {self.enhanced_intent.operation_type.value}

**SITUATION:**
You have {len(candidate_files)} files that can each solve this telemetry requirement. However, modifying too many files is not maintainable. You need to choose the 1-3 MOST STRATEGIC files that can solve the requirement with:

1. **Minimal code changes** 
2. **Maximum coverage** (affects all requests, not just some endpoints)
3. **Easiest maintenance** (central utilities > multiple middleware files)

**CANDIDATE FILES:**
{chr(10).join(file_summaries)}

**STRATEGIC SELECTION CRITERIA:**
✅ **PRIORITIZE FILES THAT ALREADY HAVE TELEMETRY INSTRUMENTATION:**
1. Files with existing Activity.SetTag, span.SetAttribute, or similar telemetry calls
2. Files that already create or manage Activity/Span objects (ActivitySource, StartActivity)
3. Files with OpenTelemetry imports and active instrumentation code
4. Central enrichers/utilities that already handle telemetry (ActivityEnricher, TelemetryHelper)
5. Application entry points that configure OpenTelemetry (Global.asax, Startup.cs with AddOpenTelemetry)

❌ **AVOID FILES THAT DON'T HAVE INSTRUMENTATION:**
- Plain middleware that only does logging without telemetry
- Controllers with no existing Activity/Span usage
- Files that would require adding new OpenTelemetry infrastructure
- Multiple similar files when one strategic file can solve it

**YOUR GOAL:**
Find files where you can EXTEND existing telemetry instrumentation to add the required attributes. Look for files that already have Activity.Current, span.SetTag, ActivitySource.StartActivity, or similar telemetry patterns. The ideal file already has the telemetry infrastructure in place and just needs additional SetTag calls.

**RESPONSE FORMAT:**
SELECTED_FILES:
/path/to/file/with/existing/instrumentation.cs

REASONING:
[Explain which files you chose and WHY they already have the telemetry infrastructure needed to fulfill this ticket. Focus on existing instrumentation patterns, not just file types.]
"""

        try:
            response = self.llm_reasoner.client.chat.completions.create(
                model="o3",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a senior software architect specializing in telemetry implementation and code maintainability. You excel at choosing the most strategic files for modifications that minimize code changes while maximizing coverage."
                    },
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = response.choices[0].message.content.strip()
            print(f"LLM strategic filtering response received")
            
            # Parse the response to extract selected files
            selected_file_paths = []
            reasoning = ""
            
            if "SELECTED_FILES:" in response_text:
                files_start = response_text.find("SELECTED_FILES:")
                reasoning_start = response_text.find("REASONING:")
                
                if files_start != -1:
                    files_end = reasoning_start if reasoning_start != -1 else len(response_text)
                    files_section = response_text[files_start + 15:files_end].strip()
                    
                    for line in files_section.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('#') and '/' in line:
                            selected_file_paths.append(line)
                
                if reasoning_start != -1:
                    reasoning = response_text[reasoning_start + 10:].strip()
            
            # Match selected paths back to file data objects
            filtered_files = []
            for selected_path in selected_file_paths:
                for file_data in candidate_files:
                    if str(file_data['path']) == selected_path or file_data['path'].name in selected_path:
                        filtered_files.append(file_data)
                        print(f"   ⭐ STRATEGIC: {file_data['path'].name}")
                        break
            
            if filtered_files:
                print(f"✅ LLM selected {len(filtered_files)} strategic files")
                print(f"Strategic reasoning: {reasoning[:200]}...")
                return filtered_files
            else:
                print("⚠️  LLM didn't select any files, falling back to top 3 candidates")
                return candidate_files[:3]
                
        except Exception as e:
            print(f"❌ Error in strategic LLM filtering: {e}")
            print("Falling back to top 3 candidate files")
            return candidate_files[:3]

    def final_selection_with_relationships(self, promising_files):
            """
            Make final file selection using relationship-aware batch processing.
            
            This function processes each promising file with its code graph relationships
            as separate batches, allowing focused analysis of related file groups.
            Each batch is analyzed to determine if it can solve the telemetry gap.
            
            Args:
                promising_files: Files identified as having telemetry enhancement potential
                
            Returns:
                Tuple of (selected_files_with_content, reasoning_chain)
            """
            print(f"Analyzing {len(promising_files)} promising files using relationship-aware batch processing")
            
            all_selected_files = []
            batch_reasoning = []
            
            # Process each promising file with its relationships as a separate batch
            for i, main_file_result in enumerate(promising_files):
                print(f"Processing relationship batch {i+1}/{len(promising_files)}: {main_file_result.file_path.name}")
                
                try:
                    # Read main file content
                    main_file_content = main_file_result.file_path.read_text(encoding='utf-8')
                    
                    # Get relationships for this main file
                    relationships = self.graph_analyzer.get_file_relationships(
                        main_file_result.file_path,
                        relationship_types=['calls', 'called_by', 'inheritance', 'implements'],
                        max_depth=1  
                    )
                    
                    # Build batch with main file + related files
                    batch_files = [{
                        'path': main_file_result.file_path,
                        'content': main_file_content,
                        'search_score': main_file_result.relevance_score,
                        'search_reasoning': main_file_result.reasoning,
                        'search_strategy': main_file_result.strategy.value,
                        'matching_patterns': main_file_result.matching_patterns,
                        'is_main_file': True
                    }]
                    
                    # Add related files to batch (limit to avoid overwhelming LLM)
                    related_count = 0
                    max_related = 4  # Keep batch manageable
                    
                    for rel_type, rel_paths in relationships.items():
                        if related_count >= max_related:
                            break
                            
                        for rel_path_str in rel_paths:
                            if related_count >= max_related:
                                break
                                
                            try:
                                rel_path = Path(rel_path_str)
                                if rel_path.exists():
                                    rel_content = rel_path.read_text(encoding='utf-8')
                                    batch_files.append({
                                        'path': rel_path,
                                        'content': rel_content,
                                        'search_score': 'N/A',
                                        'search_reasoning': f'Related to {main_file_result.file_path.name} via {rel_type}',
                                        'search_strategy': 'relationship',
                                        'matching_patterns': [],
                                        'is_main_file': False,
                                        'relationship_type': rel_type
                                    })
                                    related_count += 1
                                    print(f" Added related file: {rel_path.name} ({rel_type})")
                            except Exception as e:
                                print(f"     ⚠️  Could not read related file {rel_path_str}: {e}")
                    
                    print(f"Batch {i+1}: {len(batch_files)} files ({1} main + {related_count} related)")
                    
                    # Analyze this relationship batch with LLM
                    batch_context = {
                        'main_file': main_file_result.file_path.name,
                        'files': batch_files,
                        'telemetry_intent': self.enhanced_intent
                    }
                    
                    batch_result = self.llm_reasoner.final_telemetry_file_selection(batch_context)
                    
                    # If this batch can solve the telemetry gap, add selected files
                    if batch_result.can_solve_telemetry_gap:
                        print(f" Batch {i+1} CAN solve telemetry gap - selected {len(batch_result.selected_files)} files")
                        
                        # Find the selected files in our batch and add them
                        for selected_path in batch_result.selected_files:
                            for file_data in batch_files:
                                if str(file_data['path']) == selected_path or file_data['path'].name in selected_path:
                                    all_selected_files.append(file_data)
                                    print(f"       • Selected: {file_data['path'].name}")
                                    break
                        
                        batch_reasoning.append(f"Batch {i+1} ({main_file_result.file_path.name}): {batch_result.reasoning}")
                    else:
                        print(f"     ⏭️  Batch {i+1} cannot solve telemetry gap - skipping")
                        batch_reasoning.append(f"Batch {i+1} ({main_file_result.file_path.name}): Cannot solve gap - {batch_result.reasoning}")
                
                except Exception as e:
                    print(f"     ❌ Error processing batch {i+1}: {e}")
                    batch_reasoning.append(f"Batch {i+1} ({main_file_result.file_path.name}): Error - {e}")
            
            # Deduplicate selected files (in case multiple batches selected the same file)
            unique_selected_files = []
            seen_paths = set()
            for file_data in all_selected_files:
                file_path_str = str(file_data['path'])
                if file_path_str not in seen_paths:
                    unique_selected_files.append(file_data)
                    seen_paths.add(file_path_str)
            
            # Apply strategic filtering with LLM if we have multiple files
            if len(unique_selected_files) > 1:
                print(f"🎯 Applying strategic filtering to {len(unique_selected_files)} candidate files...")
                strategically_filtered_files = self._apply_strategic_llm_filter(unique_selected_files)
                final_files = strategically_filtered_files
            else:
                print(f"✅ Using single file (no filtering needed)")
                final_files = unique_selected_files
            
            combined_reasoning = "\n".join(batch_reasoning)
            
            print(f"✅ Relationship-aware selection completed:")
            print(f"   • Processed {len(promising_files)} relationship batches")
            print(f"   • Candidate files: {len(unique_selected_files)}")
            print(f"   • Final strategic selection: {len(final_files)} files")
            
            for f in final_files:
                main_indicator = "🎯" if f.get('is_main_file', False) else "🔗"
                print(f"   {main_indicator} {f['path'].name}")
            
            return final_files, combined_reasoning

    def generate_enhanced_patch(self, selection_data):
            """
            Generate patch using direct instrumentation strategy.
            
            This function forces the direct instrumentation approach per the coding instructions,
            ensuring consistent application of "add span.SetAttribute after every span creation"
            approach rather than random strategy selection.
            
            Args:
                selection_data: Tuple of (selected_files, reasoning_chain)
                
            Returns:
                Dict with diff, explanation, and reasoning information
            """
            selected_files, reasoning_chain = selection_data
            
            if not selected_files:
                return {
                    "diff": "", 
                    "explanation": "No files selected for modification", 
                    "reasoning": reasoning_chain,
                    "selected_files": []
                }
            
            # Prepare intent for patch generation
            basic_intent = {
                "issue_category": self.enhanced_intent.issue_category,
                "semantic_description": self.enhanced_intent.semantic_description,
                "telemetry_operation": self.enhanced_intent.telemetry_operation
            }
            
            # Force direct strategy per coding instructions
            # This ensures consistency with "Preferred Approach: Direct instrumentation"
            strategy = "direct"  # Always use direct instrumentation, not random "auto" choice
            
            print(f" Generating patch using direct instrumentation strategy")
            
            # Generate patch with direct instrumentation focus
            diff, explanation, patch_reasoning = self.llm_reasoner.enhanced_patch_generation(
                basic_intent, selected_files, reasoning_chain, strategy=strategy
            )
            
            return {
                "diff": diff,
                "explanation": explanation,
                "selection_reasoning": reasoning_chain,
                "patch_reasoning": patch_reasoning,
                "selected_files": [f["path"] for f in selected_files],
                "strategy_used": strategy
            }

    async def _stage_report_generation(self) -> None:
        """Stage 5: Generate comprehensive reports."""
        
        def generate_reports(all_data):
            if not self.generation_result.get("diff"):
                # Generate summary report for no-change scenarios
                summary_report = f"""# Telemetry Refactoring Analysis Report

## Summary
No code changes were generated for this ticket.

## Intent Analysis
- **Category**: {self.enhanced_intent.issue_category}
- **Confidence**: {self.enhanced_intent.confidence.value}
- **Complexity**: {self.enhanced_intent.complexity_score}/10
- **Description**: {self.enhanced_intent.semantic_description}

## Search Results
Found {len(self.search_results)} candidate files, but none were selected for modification.

## Recommendations
{chr(10).join(f"- {suggestion}" for suggestion in self.enhanced_intent.validation_result.suggestions)}
"""
                write_markdown(self.output_dir, "analysis_report.md", summary_report)
                return {"report_type": "analysis_only"}
            
            # Generate comprehensive remediation report
            diff_content = f"```diff\n{self.generation_result['diff']}\n```"
            explanation = self.generation_result['explanation']
            
            # Build comprehensive report
            report_sections = [
                "# Telemetry Refactoring Remediation Report",
                "",
                "## Executive Summary",
                f"**Ticket Category**: {self.enhanced_intent.issue_category}",
                f"**Confidence Level**: {self.enhanced_intent.confidence.value}",
                f"**Files Modified**: {len(self.generation_result['selected_files'])}",
                f"**Strategy Used**: {self.generation_result.get('strategy_used', 'direct')} instrumentation",
            ]
            
            report_sections.extend([
                "",
                "## Intent Analysis",
                f"**Semantic Description**: {self.enhanced_intent.semantic_description}",
                f"**Operation Type**: {self.enhanced_intent.operation_type.value}",
                f"**Complexity Score**: {self.enhanced_intent.complexity_score}/10",
                f"**Estimated Impact**: {self.enhanced_intent.estimated_files} files",
                "",
                "### Sub-tasks Identified",
            ])
            
            if self.enhanced_intent.sub_tasks:
                for i, task in enumerate(self.enhanced_intent.sub_tasks, 1):
                    report_sections.append(f"{i}. {task.get('description', 'N/A')}")
            
            report_sections.extend([
                "",
                "## Code Changes",
                diff_content,
                "",
                "## Implementation Details",
                explanation,
                "",
                "## Batch Selection Analysis",
                f"**Total Search Results Processed**: {len(self.search_results)}",
                f"**Files with Telemetry Potential**: {len(getattr(self, 'promising_files', []))}",
                f"**Final Files Selected**: {len(self.generation_result['selected_files'])}",
                f"**Selection Efficiency**: {len(self.generation_result['selected_files'])/len(self.search_results)*100:.1f}%",
            ])
            
            
            
            # Add reasoning summary
            report_sections.extend([
                "",
                "## Reasoning Summary",
                "",
                "### File Selection Reasoning",
                str(self.generation_result.get('selection_reasoning', 'No reasoning available')),
                "",
                "### Patch Generation Reasoning", 
                str(self.generation_result.get('patch_reasoning', 'No reasoning available')),
            ])
            
            comprehensive_report = "\n".join(report_sections)
            write_markdown(self.output_dir, "remediation.md", comprehensive_report)
            
            return {"report_type": "comprehensive", "report_length": len(comprehensive_report)}
        
        report_result = await self.orchestrator.execute_stage(
            "report_generation",
            generate_reports,
            {
                "intent": self.enhanced_intent,
                "search_results": self.search_results,
                "generation_result": self.generation_result
            },
            dependencies=["patch_generation"]
        )
        
        if report_result.status == StageStatus.COMPLETED:
            report_info = report_result.result
            print(f"📄 Generated {report_info['report_type']} report")
            print(f"📊 Report saved to {self.output_dir / 'remediation.md'}")
        else:
            print(f"⚠️  Report generation failed: {report_result.error}")
        
        print(f"\n🎉 Enhanced pipeline completed successfully!")
        print(f"📁 All outputs saved to: {self.output_dir}")

async def main():
    """Enhanced main function with comprehensive argument parsing."""
    parser = argparse.ArgumentParser(
        description="Enhanced Telemetry Refactoring Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with direct instrumentation (recommended)
  python enhanced_cli.py --ticket-key ATL-90561 --repo-root ~/Atlas --dirs-proj-path ~/Atlas/src/dirs.proj

  # Comprehensive analysis with caching
  python enhanced_cli.py --ticket-key ATL-90561 --repo-root ~/Atlas --dirs-proj-path ~/Atlas/src/dirs.proj \\
    --comprehensive-validation --enable-cache --max-candidates 50

  # Local ticket with direct instrumentation focus
  python enhanced_cli.py --local-ticket --ticket-key ./ticket.txt --repo-root ~/Atlas \\
    --dirs-proj-path ~/Atlas/src/dirs.proj
        """
    )
    
    # Required arguments
    parser.add_argument("--ticket-key", required=True,
                       help="Jira ticket key (e.g., 'ATL-93035') or local file path")
    parser.add_argument("--repo-root", required=True,
                       help="Path to the root of the monorepo")
    parser.add_argument("--dirs-proj-path", required=True,
                       help="Path to the dirs.proj file for the monorepo")
    
    # Optional arguments
    parser.add_argument("--output", default="runs/enhanced-run",
                       help="Output folder (default: runs/enhanced-run)")
    parser.add_argument("--batch-size", type=int, default=50,
                       help="Number of files to analyze per batch (default: 50)")
    parser.add_argument("--max-candidates", type=int, default=100,
                       help="Maximum number of candidate files to find (default: 100)")
    
    # Strategy options - Default changed to 'direct' per coding instructions
    parser.add_argument("--strategy", choices=["auto", "direct", "helpers"], 
                       default="direct", help="Modification strategy: direct (preferred, force direct modification), auto (AI decides), helpers (force helper methods)")
    
    # Advanced options
    parser.add_argument("--local-ticket", action='store_true',
                       help="Use a local file for ticket text instead of Jira")
    parser.add_argument("--build-graph-only", action='store_true',
                       help="Only build the monorepo graph and exit")
    parser.add_argument("--comprehensive-validation", action='store_true',
                       help="Run comprehensive validation (slower but more thorough)")
    parser.add_argument("--enable-cache", action='store_true', default=True,
                       help="Enable caching of intermediate results")
    parser.add_argument("--max-retries", type=int, default=3,
                       help="Maximum number of retries for failed stages")
    parser.add_argument("--parallel-workers", type=int, default=4,
                       help="Number of parallel workers for batch processing")
    
    # Reasoning options
    parser.add_argument("--reasoning-strategy", 
                       choices=["direct", "chain_of_thought", "tree_of_thought", "self_consistency"],
                       default="chain_of_thought",
                       help="LLM reasoning strategy to use")
    
    args = parser.parse_args()
    
    # Create and run enhanced agent
    agent = EnhancedTelemetryAgent(args)
    await agent.run_enhanced_pipeline()

if __name__ == "__main__":
    asyncio.run(main())