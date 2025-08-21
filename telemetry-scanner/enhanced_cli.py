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
from scanner.validation_framework import TelemetryAgentValidator, ValidationLevel

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
        self.validator = TelemetryAgentValidator(self.output_dir)
    
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
            
            # Stage 4: Advanced Code Analysis and Selection
            await self._stage_advanced_analysis()
            
            # Stage 5: LLM-Powered Reasoning and Patch Generation
            await self._stage_reasoning_and_generation()
            
            # Stage 6: Comprehensive Validation
            await self._stage_validation()
            
            # Stage 7: Report Generation
            await self._stage_report_generation()
            
        except Exception as e:
            print(f"❌ Pipeline failed: {e}")
            raise
        finally:
            # Save execution report
            self.orchestrator.save_stage_report()
            print(f"📊 Execution report saved to {self.output_dir / 'pipeline_report.json'}")
    
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
            
            # Initialize advanced graph analyzer
            self.graph_analyzer = AdvancedCodeGraphAnalyzer(
                "codegraph.json",
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
        
        # Build enhanced graph (skip if --build-graph-only)
        if self.args.build_graph_only:
            graph_result = await self.orchestrator.execute_stage(
                "graph_building",
                build_enhanced_graph,
                project_paths,
                dependencies=["project_parsing"]
            )
            
            if graph_result.status == StageStatus.COMPLETED:
                print("✅ Enhanced code graph built successfully")
                return
            else:
                raise RuntimeError(f"Graph building failed: {graph_result.error}")
        
        # Initialize search engine
        self.search_engine = IntelligentSearchEngine(
            self.args.repo_root,
            "codegraph.json"
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
    
    async def _stage_advanced_analysis(self) -> None:
        """Stage 4: Advanced code analysis and impact assessment."""
        
        def perform_impact_analysis(search_results):
            # Extract file paths from search results
            candidate_files = [result.file_path for result in search_results[:20]]  # Limit for analysis
            
            # Convert enhanced intent to basic format for analysis
            basic_intent = {
                "issue_category": self.enhanced_intent.issue_category,
                "semantic_description": self.enhanced_intent.semantic_description,
                "telemetry_operation": self.enhanced_intent.telemetry_operation
            }
            
            # Perform impact analysis
            impact_analysis = self.graph_analyzer.analyze_impact(candidate_files, basic_intent)
            
            # Create code clusters
            all_affected_files = impact_analysis.direct_impact + impact_analysis.indirect_impact
            clusters = self.graph_analyzer.create_code_clusters(all_affected_files[:50])  # Limit cluster analysis
            
            return {
                "impact_analysis": impact_analysis,
                "code_clusters": clusters
            }
        
        analysis_result = await self.orchestrator.execute_stage(
            "advanced_analysis",
            perform_impact_analysis,
            self.search_results,
            dependencies=["intelligent_search"]
        )
        
        if analysis_result.status != StageStatus.COMPLETED:
            raise RuntimeError(f"Advanced analysis failed: {analysis_result.error}")
        
        analysis_data = analysis_result.result
        self.impact_analysis = analysis_data["impact_analysis"]
        self.code_clusters = analysis_data["code_clusters"]
        
        # Save analysis results
        analysis_summary = {
            "impact_analysis": {
                "direct_impact_count": len(self.impact_analysis.direct_impact),
                "indirect_impact_count": len(self.impact_analysis.indirect_impact),
                "risk_score": self.impact_analysis.risk_score,
                "affected_patterns": [pattern.value for pattern in self.impact_analysis.affected_patterns],
                "breaking_changes": self.impact_analysis.breaking_changes,
                "test_requirements": self.impact_analysis.test_requirements
            },
            "code_clusters": [
                {
                    "name": cluster.name,
                    "file_count": len(cluster.files),
                    "patterns": [pattern.value for pattern in cluster.architectural_patterns],
                    "complexity_score": cluster.complexity_score
                }
                for cluster in self.code_clusters
            ]
        }
        
        (self.output_dir / "advanced_analysis.json").write_text(
            json.dumps(analysis_summary, indent=2), encoding="utf-8"
        )
        
        print(f"📊 Impact Analysis: {len(self.impact_analysis.direct_impact)} direct, {len(self.impact_analysis.indirect_impact)} indirect files")
        print(f"⚠️  Risk Score: {self.impact_analysis.risk_score}/10")
        print(f"🏗️  Architectural Patterns: {', '.join(pattern.value for pattern in self.impact_analysis.affected_patterns)}")
    
    async def _stage_reasoning_and_generation(self) -> None:
        """Stage 5: Advanced LLM reasoning and patch generation."""
        
        def perform_file_selection(analysis_data):
            # Prepare candidate files for selection
            candidate_files = []
            for result in self.search_results[:self.args.batch_size]:
                try:
                    content = result.file_path.read_text(encoding='utf-8')
                    candidate_files.append({
                        'path': result.file_path,
                        'content': content,
                        'relevance_score': result.relevance_score
                    })
                except Exception as e:
                    print(f"Warning: Could not read file {result.file_path.name}: {e}")
            
            # Use enhanced LLM reasoning for file selection
            basic_intent = {
                "issue_category": self.enhanced_intent.issue_category,
                "semantic_description": self.enhanced_intent.semantic_description,
                "telemetry_operation": self.enhanced_intent.telemetry_operation
            }
            
            selected_files, reasoning_chain = self.llm_reasoner.enhanced_file_selection(
                basic_intent, candidate_files
            )
            
            # Convert selected file names back to file objects
            selected_file_objects = []
            for file_name in selected_files:
                for candidate in candidate_files:
                    if candidate['path'].name == file_name:
                        selected_file_objects.append(candidate)
                        break
            
            return {
                "selected_files": selected_file_objects,
                "reasoning_chain": reasoning_chain
            }
        
        def generate_enhanced_patch(selection_data):
            selected_files = selection_data["selected_files"]
            reasoning_chain = selection_data["reasoning_chain"]
            
            if not selected_files:
                return {"diff": "", "explanation": "No files selected for modification", "reasoning": reasoning_chain}
            
            basic_intent = {
                "issue_category": self.enhanced_intent.issue_category,
                "semantic_description": self.enhanced_intent.semantic_description,
                "telemetry_operation": self.enhanced_intent.telemetry_operation
            }
            
            # Generate patch with enhanced reasoning
            diff, explanation, patch_reasoning = self.llm_reasoner.enhanced_patch_generation(
                basic_intent, selected_files, reasoning_chain
            )
            
            return {
                "diff": diff,
                "explanation": explanation,
                "selection_reasoning": reasoning_chain,
                "patch_reasoning": patch_reasoning,
                "selected_files": [f["path"] for f in selected_files]
            }
        
        # File selection with reasoning
        selection_result = await self.orchestrator.execute_stage(
            "file_selection",
            perform_file_selection,
            {"search_results": self.search_results, "analysis": self.impact_analysis},
            dependencies=["advanced_analysis"]
        )
        
        if selection_result.status != StageStatus.COMPLETED:
            raise RuntimeError(f"File selection failed: {selection_result.error}")
        
        # Patch generation with reasoning
        generation_result = await self.orchestrator.execute_stage(
            "patch_generation",
            generate_enhanced_patch,
            selection_result.result,
            dependencies=["file_selection"]
        )
        
        if generation_result.status != StageStatus.COMPLETED:
            raise RuntimeError(f"Patch generation failed: {generation_result.error}")
        
        self.generation_result = generation_result.result
        
        # Save reasoning and patch results
        reasoning_data = {
            "selected_files": [str(f) for f in self.generation_result["selected_files"]],
            "selection_reasoning": self.generation_result["selection_reasoning"].final_conclusion,
            "patch_reasoning": self.generation_result["patch_reasoning"].final_conclusion,
            "diff_length": len(self.generation_result["diff"]),
            "explanation_length": len(self.generation_result["explanation"])
        }
        
        (self.output_dir / "reasoning_summary.json").write_text(
            json.dumps(reasoning_data, indent=2), encoding="utf-8"
        )
        
        if self.generation_result["selected_files"]:
            print(f"✅ Selected {len(self.generation_result['selected_files'])} files for modification")
            print(f"📝 Generated patch with {len(self.generation_result['diff'].split())} lines")
        else:
            print("⚠️  No files selected for modification")
    
    async def _stage_validation(self) -> None:
        """Stage 6: Comprehensive validation."""
        
        def perform_validation(generation_result):
            if not generation_result["selected_files"]:
                return {"validation_skipped": True, "reason": "No files selected"}
            
            # Prepare original files for validation
            original_files = []
            for file_path in generation_result["selected_files"]:
                try:
                    content = file_path.read_text(encoding='utf-8')
                    original_files.append({"path": file_path, "content": content})
                except Exception as e:
                    print(f"Warning: Could not read file for validation: {e}")
            
            # Convert enhanced intent to basic format
            basic_intent = {
                "issue_category": self.enhanced_intent.issue_category,
                "semantic_description": self.enhanced_intent.semantic_description,
                "telemetry_operation": self.enhanced_intent.telemetry_operation
            }
            
            # Run comprehensive validation
            validation_level = ValidationLevel.COMPREHENSIVE if self.args.comprehensive_validation else ValidationLevel.BASIC
            validation_report = self.validator.run_comprehensive_validation(
                basic_intent,
                original_files,
                generation_result["diff"],
                validation_level
            )
            
            return validation_report
        
        validation_result = await self.orchestrator.execute_stage(
            "validation",
            perform_validation,
            self.generation_result,
            dependencies=["patch_generation"]
        )
        
        if validation_result.status != StageStatus.COMPLETED:
            print(f"⚠️  Validation failed: {validation_result.error}")
            self.validation_report = None
        else:
            self.validation_report = validation_result.result
            
            if not self.validation_report.get("validation_skipped"):
                # Save validation report
                validation_summary = {
                    "overall_score": self.validation_report.overall_score,
                    "risk_assessment": self.validation_report.risk_assessment,
                    "compliance_status": self.validation_report.compliance_status,
                    "recommendations": self.validation_report.recommendations,
                    "test_summary": {
                        "total_tests": len(self.validation_report.test_results),
                        "passed_tests": sum(1 for t in self.validation_report.test_results if t.passed),
                        "failed_tests": sum(1 for t in self.validation_report.test_results if not t.passed)
                    }
                }
                
                (self.output_dir / "validation_report.json").write_text(
                    json.dumps(validation_summary, indent=2), encoding="utf-8"
                )
                
                print(f"✅ Validation completed: {self.validation_report.overall_score:.2f}/1.0 score")
                print(f"🛡️  Risk Level: {self.validation_report.risk_assessment}")
            else:
                print("⏭️  Validation skipped (no files selected)")
    
    async def _stage_report_generation(self) -> None:
        """Stage 7: Generate comprehensive reports."""
        
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
            ]
            
            if self.validation_report and not self.validation_report.get("validation_skipped"):
                report_sections.extend([
                    f"**Validation Score**: {self.validation_report.overall_score:.2f}/1.0",
                    f"**Risk Assessment**: {self.validation_report.risk_assessment}",
                ])
            
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
                "## Impact Analysis",
                f"**Direct Impact**: {len(self.impact_analysis.direct_impact)} files",
                f"**Indirect Impact**: {len(self.impact_analysis.indirect_impact)} files",
                f"**Risk Score**: {self.impact_analysis.risk_score}/10",
                "",
                "### Affected Architectural Patterns",
            ])
            
            for pattern in self.impact_analysis.affected_patterns:
                report_sections.append(f"- {pattern.value}")
            
            if self.impact_analysis.breaking_changes:
                report_sections.extend([
                    "",
                    "### Potential Breaking Changes",
                ])
                for change in self.impact_analysis.breaking_changes:
                    report_sections.append(f"- {change}")
            
            report_sections.extend([
                "",
                "### Test Requirements",
            ])
            for req in self.impact_analysis.test_requirements:
                report_sections.append(f"- {req}")
            
            if self.validation_report and not self.validation_report.get("validation_skipped"):
                report_sections.extend([
                    "",
                    "## Validation Results",
                    f"**Overall Score**: {self.validation_report.overall_score:.2f}/1.0",
                    f"**Tests Passed**: {sum(1 for t in self.validation_report.test_results if t.passed)}/{len(self.validation_report.test_results)}",
                    "",
                    "### Recommendations",
                ])
                for rec in self.validation_report.recommendations:
                    report_sections.append(f"- {rec}")
            
            # Add reasoning summary
            report_sections.extend([
                "",
                "## Reasoning Summary",
                "",
                "### File Selection Reasoning",
                self.generation_result['selection_reasoning'].final_conclusion,
                "",
                "### Patch Generation Reasoning", 
                self.generation_result['patch_reasoning'].final_conclusion,
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
                "impact_analysis": self.impact_analysis,
                "generation_result": self.generation_result,
                "validation_report": self.validation_report
            },
            dependencies=["validation"]
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
  # Basic usage
  python enhanced_cli.py --ticket-key ATL-90561 --repo-root ~/Atlas --dirs-proj-path ~/Atlas/src/dirs.proj

  # Comprehensive analysis with caching
  python enhanced_cli.py --ticket-key ATL-90561 --repo-root ~/Atlas --dirs-proj-path ~/Atlas/src/dirs.proj \\
    --comprehensive-validation --enable-cache --max-candidates 50

  # Local ticket with advanced reasoning
  python enhanced_cli.py --local-ticket --ticket-key ./ticket.txt --repo-root ~/Atlas \\
    --dirs-proj-path ~/Atlas/src/dirs.proj --reasoning-strategy tree_of_thought
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
    parser.add_argument("--batch-size", type=int, default=15,
                       help="Number of files to analyze per batch (default: 15)")
    parser.add_argument("--max-candidates", type=int, default=30,
                       help="Maximum number of candidate files to find (default: 30)")
    
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
