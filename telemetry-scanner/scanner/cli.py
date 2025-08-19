"""
llm_scan_cli.py
End-to-end orchestrator for LLM-first discovery + patch generation.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from scanner.static_analyzer import run_static_analysis
from scanner.jira_client import get_formatted_ticket_text,  clean_jira_text
from scanner.intent_builder import extract_intent
from scanner.context_finder import find_candidate_files
from scanner.config_finder import find_config_files
from scanner.patch_composer import select_files_for_edit, compose_patch
from scanner.writer import write_markdown

def main() -> None:
    ap = argparse.ArgumentParser("Telemetry Refactoring Agent")
    ap.add_argument("--ticket-key", required=True, help="The Jira ticket key (e.g., 'ATL-93035')")
    ap.add_argument("--service-path", required=True, help="Path to C# repo")
    ap.add_argument("--output", default="runs/demo", help="Output folder")
    ap.add_argument("--batch-size", type=int, default=10, help="Number of files to check per iteration")
    args = ap.parse_args()

    print(f"Fetching and formatting Jira ticket '{args.ticket_key}'...")
    raw_ticket_text = get_formatted_ticket_text(args.ticket_key)
    if not raw_ticket_text:
        print("Could not retrieve ticket text. Exiting.")
        return
    
    print("Cleaning raw Jira ticket text...")
    ticket_text = clean_jira_text(raw_ticket_text)
    
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the cleaned text for debugging
    (out_dir / "cleaned_ticket.txt").write_text(ticket_text, encoding="utf-8")

    # 1. The Planner: Extract a detailed intent with a potential static query
    print("Step 1: Planning - Extracting intent from Jira ticket...")
    intent = extract_intent(ticket_text)
    (out_dir / "intent.json").write_text(json.dumps(intent, indent=2))

    # 2. The Investigators: Run all searches in parallel
    print("\nStep 2: Investigating - Running parallel searches...")
    semantic_candidates = find_candidate_files(args.service_path, intent, top_k=30)
    config_candidates = find_config_files(args.service_path)
    
    # # --- NEW: Run the static analysis search ---
    # static_query = intent.get("static_analysis_query")
    # static_candidates = run_static_analysis(static_query, args.service_path) if static_query else []
    
    # Consolidate "seed" files from all three searches
    all_candidates = {}
    # Prioritize the most precise results first
    for f in config_candidates + semantic_candidates:
        if f not in all_candidates:
            all_candidates[f] = True
    
    candidate_list = list(all_candidates.keys())
    print(f"Found a total of {len(candidate_list)} unique candidate files to analyze.")
    print("\n--- Full Candidate List to be Analyzed ---")
    for path in candidate_list:
        print(f"- {path.name}")
    print("------------------------------------------\n")

    # 3. The Decider: Iteratively analyze candidates
    print("\nStep 3: Deciding - Analyzing candidates in batches...")
    selected_files = []
    # (The rest of the loop and patching logic from here is unchanged)
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
        print(f"\nStep 4: Coding - Final selection made. Generating patch for {len(selected_files)} file(s)...")
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