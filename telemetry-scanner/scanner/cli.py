import argparse
import json
from pathlib import Path

# Import all necessary functions from our helper modules
from scanner.jira_client import get_formatted_ticket_text, clean_jira_text
from scanner.intent_builder import extract_intent
from scanner.project_utils import parse_dirs_proj
from scanner.context_finder import find_candidate_files
from scanner.config_finder import find_config_files
from scanner.static_analyzer import build_monorepo_graph, expand_with_code_graph
from scanner.patch_composer import select_files_for_edit, compose_patch
from scanner.writer import write_markdown

def main() -> None:
    # --- Step 1: Parse Command-Line Arguments ---
    ap = argparse.ArgumentParser("Telemetry Refactoring Agent")
    ap.add_argument("--ticket-key", required=True, help="The Jira ticket key (e.g., 'ATL-93035') or local file path")
    ap.add_argument("--repo-root", required=True, help="Path to the root of the monorepo.")
    ap.add_argument("--dirs-proj-path", required=True, help="Path to the dirs.proj file for the monorepo.")
    ap.add_argument("--output", default="runs/demo", help="Output folder")
    ap.add_argument("--batch-size", type=int, default=10, help="Number of files to check per iteration")
    ap.add_argument("--local-ticket", action='store_true', help="Use a local file for ticket text instead of Jira")
    ap.add_argument("--build-graph-only", action='store_true', help="Only build the monorepo graph and exit")
    ap.add_argument("--force-rebuild-graph", action='store_true', help="Force rebuild the code graph, ignoring cache")
    args = ap.parse_args()

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # --- Step 2: Fetch and Pre-process Jira Ticket ---
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

    # --- Step 4: Index the Monorepo (Build Code Graph) ---
    print("\nStep 2: Indexing - Building full monorepo Code Graph...")
    project_paths = parse_dirs_proj(Path(args.dirs_proj_path))
    if not project_paths:
        print("Could not find any projects in dirs.proj. Exiting.")
        return
    
    print(f"Found {len(project_paths)} projects in dirs.proj.")
    for i, path in enumerate(project_paths[:10]):
        print(f"  [{i+1}] {path}")
    if len(project_paths) > 10:
        print(f"  ... and {len(project_paths) - 10} more")
    
    build_monorepo_graph(project_paths, force_rebuild=args.force_rebuild_graph)
    
    # If --build-graph-only is set, exit after building the graph
    if args.build_graph_only:
        print("\nMonorepo graph built successfully. Exiting as requested.")
        return

    # --- Step 3: The Planner (Generate Intent) ---
    print("\nStep 1: Planning - Extracting intent from Jira ticket...")
    intent = extract_intent(ticket_text)
    (out_dir / "intent.json").write_text(json.dumps(intent, indent=2))
    
    # --- Step 5: The Investigators (Gather Seed Files) ---
    print("\nStep 3: Investigating - Running parallel searches...")
    semantic_candidates = find_candidate_files(args.repo_root, intent, top_k=30)
    config_candidates = find_config_files(args.repo_root)
    static_query = intent.get("static_analysis_query")
    # Note: run_static_analysis is currently a placeholder, but we keep the hook for it.
    # For now, return an empty list since the static analysis is not fully implemented
    static_candidates = [] if static_query else []

    seed_files = {}
    for f in static_candidates + config_candidates + semantic_candidates:
        if f not in seed_files:
            seed_files[f] = True
    
    # --- Step 6: The Cartographer (Expand Context with Graph) ---
    print("\nStep 4: Expanding context with Code Graph...")
    candidate_list = expand_with_code_graph(list(seed_files.keys()))
    print(f"Found a total of {len(candidate_list)} unique candidate files to analyze.")
    (out_dir / "candidate_list.txt").write_text("\n".join(str(p) for p in candidate_list))

    # --- Step 7: The Decider (Iteratively Select Files) ---
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

    # --- Step 8: The Coder (Generate Patch) ---
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

if __name__ == "__main__":
    main()