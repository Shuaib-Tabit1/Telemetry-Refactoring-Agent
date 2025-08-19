"""
A module to interface with the external C# Roslyn-based static analysis tool.
"""
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# IMPORTANT: You must update this path to point to your compiled C# tool
ROSLYN_TOOL_PATH = "/Users/shuaib.tabit/Documents/TRA/CodeGraphBuilder/bin/Release/net9.0/CodeGraphBuilder.dll"
# Path to the pre-built code graph
CODE_GRAPH_PATH = "/Users/shuaib.tabit/Documents/TRA/CodeGraphBuilder/monorepo_graph.json"

def run_static_analysis(query: Optional[Dict[str, Any]], repo_path: str) -> List[Path]:
    """
    Executes the Roslyn tool with a specific query to find files.
    """
    if not query:
        return []
    
    # This functionality would require adding a dedicated "query" command to the C# tool
    # that is separate from the Code Graph query.
    print("NOTE: Roslyn real-time querying is a placeholder. Returning empty list.")
    return []

def expand_with_code_graph(seed_files: List[Path], repo_path: str) -> List[Path]:
    """
    Takes a list of seed files and uses the pre-built code graph to find all related files.
    """
    if not seed_files:
        return []
        
    print(f"Expanding {len(seed_files)} seed file(s) with the Code Graph...")
    
    try:
        # Construct the command to run the C# tool's 'query' command
        command = [
            "dotnet",
            ROSLYN_TOOL_PATH,
            "query",
            "--graph-file",
            CODE_GRAPH_PATH,
            "--seed-files"
        ]
        # Add all the seed file paths to the command
        command.extend([str(p) for p in seed_files])

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        
        # The C# tool returns a JSON list of file paths
        expanded_paths_str = json.loads(result.stdout)
        expanded_paths = [Path(p) for p in expanded_paths_str]
        
        print(f"Code Graph expanded the list to {len(expanded_paths)} total files.")
        return expanded_paths

    except FileNotFoundError:
        print(f"Warning: Code graph file not found at '{CODE_GRAPH_PATH}'. Skipping expansion.")
        return seed_files # Return the original list if the graph doesn't exist
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"Code Graph expansion failed: {e}")
        return seed_files # Return original list on error