import subprocess
import json
import tempfile
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# IMPORTANT: Update this path to point to your compiled C# tool
ROSLYN_TOOL_PATH = "~/Documents/TRA/CodeGraphBuilder/bin/Release/net9.0/CodeGraphBuilder.dll"
# Path where the code graph will be saved/read
# Define a function to get the best available code graph path
def get_best_code_graph_path() -> str:
    """Find the best available code graph file."""
    print("[DEBUG] get_best_code_graph_path: Starting search for best code graph...")
    
    # First try the main codegraph.json
    main_graph = Path("codegraph.json")
    print(f"[DEBUG] get_best_code_graph_path: Checking main graph: {main_graph}")
    if main_graph.exists():
        size = main_graph.stat().st_size
        print(f"[DEBUG] get_best_code_graph_path: Main graph exists, size: {size} bytes")
        if size > 100:  # Non-empty file
            print(f"[DEBUG] get_best_code_graph_path: Using main graph: {main_graph}")
            return str(main_graph)
        else:
            print(f"[DEBUG] get_best_code_graph_path: Main graph too small ({size} bytes), looking for cached graphs")
    else:
        print(f"[DEBUG] get_best_code_graph_path: Main graph does not exist")
    
    # Look for cached code graphs
    cache_dir = Path(".cache/code-graphs")
    print(f"[DEBUG] get_best_code_graph_path: Checking cache directory: {cache_dir}")
    if cache_dir.exists():
        print(f"[DEBUG] get_best_code_graph_path: Cache directory exists")
        # Find the most recent atlas-monorepo graph
        atlas_graphs = list(cache_dir.glob("atlas-monorepo-*.json"))
        print(f"[DEBUG] get_best_code_graph_path: Found {len(atlas_graphs)} atlas graphs: {[g.name for g in atlas_graphs]}")
        if atlas_graphs:
            # Use the most recent one (by name, which should be timestamp-based)
            latest_graph = max(atlas_graphs, key=lambda x: x.name)
            size = latest_graph.stat().st_size
            print(f"[DEBUG] get_best_code_graph_path: Latest graph: {latest_graph}, size: {size} bytes")
            if size > 100:  # Non-empty file
                print(f"[DEBUG] get_best_code_graph_path: Using cached graph: {latest_graph}")
                return str(latest_graph)
            else:
                print(f"[DEBUG] get_best_code_graph_path: Latest graph too small ({size} bytes)")
        else:
            print(f"[DEBUG] get_best_code_graph_path: No atlas graphs found in cache")
    else:
        print(f"[DEBUG] get_best_code_graph_path: Cache directory does not exist")
    
    print(f"[DEBUG] get_best_code_graph_path: Falling back to default: codegraph.json")
    return "codegraph.json"  # Fallback to default

CODE_GRAPH_PATH = get_best_code_graph_path()
print(f"[DEBUG] static_analyzer: CODE_GRAPH_PATH set to: {CODE_GRAPH_PATH}")
# Cache directory
CACHE_DIR = Path(".cache/code-graphs")

def get_cache_file_path(project_paths: List[str]) -> Path:
    """Generate a cache file path based on the project list."""
    # Create a hash from the sorted project paths to ensure consistent naming
    project_list_str = "|".join(sorted(project_paths))
    cache_hash = hashlib.md5(project_list_str.encode()).hexdigest()[:12]
    
    # Ensure cache directory exists
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    return CACHE_DIR / f"atlas-monorepo-{cache_hash}.json"

def should_use_cache(project_paths: List[str], cache_file: Path) -> Tuple[bool, str]:
    """
    Check if we should use the cached code graph.
    Returns (should_use, reason)
    """
    if not cache_file.exists():
        return False, "Cache file doesn't exist"
    
    try:
        # Get the newest .csproj file modification time
        newest_project_time = 0
        for project_path in project_paths:
            path = Path(project_path)
            if path.exists():
                newest_project_time = max(newest_project_time, path.stat().st_mtime)
        
        cache_time = cache_file.stat().st_mtime
        
        if newest_project_time > cache_time:
            time_diff = newest_project_time - cache_time
            return False, f"Code has been modified {time_diff:.0f} seconds after cache was created"
        
        # Quick validation that cache file is valid JSON with symbols
        with open(cache_file, 'r') as f:
            data = json.load(f)
            symbol_count = len(data.get('Symbols', []))
            if symbol_count == 0:
                return False, "Cache exists but has no symbols"
            
            cache_age_hours = (time.time() - cache_time) / 3600
            return True, f"Cache valid with {symbol_count} symbols (age: {cache_age_hours:.1f} hours)"
            
    except Exception as e:
        return False, f"Cache validation failed: {str(e)}"

def load_cached_graph(cache_file: Path) -> bool:
    """
    Load the cached code graph to the main CODE_GRAPH_PATH.
    Returns True if successful.
    """
    try:
        # Copy cached graph to the expected location
        import shutil
        shutil.copy2(cache_file, CODE_GRAPH_PATH)
        return True
    except Exception as e:
        print(f"Failed to load cached graph: {e}")
        return False

def save_to_cache(cache_file: Path) -> bool:
    """
    Save the current code graph to cache.
    Returns True if successful.
    """
    try:
        if Path(CODE_GRAPH_PATH).exists():
            import shutil
            shutil.copy2(CODE_GRAPH_PATH, cache_file)
            return True
        return False
    except Exception as e:
        print(f"Failed to save to cache: {e}")
        return False

def build_monorepo_graph(project_paths: List[str], force_rebuild: bool = False):
    """
    Calls the C# tool's 'index' command to build the code graph.
    Uses caching to avoid rebuilding when code hasn't changed.
    
    Args:
        project_paths: List of .csproj file paths
        force_rebuild: If True, ignore cache and rebuild from scratch
    """
    # Expand the user path (e.g., '~') to a full, absolute path
    expanded_tool_path = str(Path(ROSLYN_TOOL_PATH).expanduser())
    
    # Ensure all paths are in the correct format for macOS
    normalized_paths = []
    for path in project_paths:
        # Replace backslashes with forward slashes
        path = path.replace('\\', '/')
        # Ensure the path exists
        if Path(path).exists():
            normalized_paths.append(path)
        else:
            print(f"Warning: Project path does not exist: {path}")
    
    print(f"Normalized {len(normalized_paths)} valid project paths")
    
    # Check cache first (unless force rebuild)
    cache_file = get_cache_file_path(normalized_paths)
    
    if not force_rebuild:
        print("🔍 Checking for cached code graph...")
        use_cache, reason = should_use_cache(normalized_paths, cache_file)
        
        if use_cache:
            print(f"✅ Using cached code graph: {reason}")
            print(f"📁 Cache location: {cache_file}")
            
            if load_cached_graph(cache_file):
                print("🚀 Code graph loaded from cache successfully!")
                return
            else:
                print("⚠️ Failed to load cache, rebuilding...")
        else:
            print(f"🔄 Cache miss: {reason}")
            print(f"🏗️ Building fresh code graph...")
    else:
        print("🔄 Force rebuild requested, ignoring cache...")
    
    # Build the graph from scratch
    print(f"Building code graph for {len(normalized_paths)} projects...")
    
    # Add debug logging for a few paths to verify format
    if normalized_paths:
        print(f"First project path: {normalized_paths[0]}")
        if len(normalized_paths) > 1:
            print(f"Second project path: {normalized_paths[1]}")
        # Check if the paths actually exist
        print(f"First project exists: {Path(normalized_paths[0]).exists()}")
    
    # Instead of using a single command with all projects, we'll use a multi-step approach:
    # 1. Process each project individually to avoid command line argument issues
    # 2. Merge the resulting graphs
    
    # Create temporary directory for batch results
    batch_dir = Path(tempfile.mkdtemp())
    print(f"Using temporary directory for batch results: {batch_dir}")
    
    # Process projects in batches of 20 for organization
    batch_size = 20
    batch_graphs = []
    
    try:
        for batch_index in range(0, len(normalized_paths), batch_size):
            batch_paths = normalized_paths[batch_index:batch_index+batch_size]
            batch_output = batch_dir / f"batch_{batch_index//batch_size}.json"
            batch_graphs.append(batch_output)
            
            print(f"Processing batch {batch_index//batch_size + 1} with {len(batch_paths)} projects...")
            
            # Process one project at a time
            all_successful = True
            single_graphs = []
            
            for proj_index, project_path in enumerate(batch_paths):
                single_output = batch_dir / f"single_{batch_index//batch_size}_{proj_index}.json"
                single_graphs.append(single_output)
                
                # Create a temporary file with the single project path
                temp_projects_file = batch_dir / f"projects_{batch_index//batch_size}_{proj_index}.txt"
                with open(temp_projects_file, 'w') as f:
                    f.write(project_path + '\n')
                
                # Handle each project individually using --projects-file
                command = [
                    "dotnet",
                    expanded_tool_path,
                    "index",
                    "--projects-file", str(temp_projects_file),  # Use projects-file as expected
                    "--output-file", str(single_output)
                ]
                
                try:
                    print(f"Processing project {proj_index+1}/{len(batch_paths)}: {project_path}")
                    result = subprocess.run(command, capture_output=True, text=True, check=True)
                    
                    if result.stdout:
                        print(f"STDOUT: {result.stdout}")
                    if result.stderr:
                        print(f"STDERR: {result.stderr}")
                        
                except subprocess.CalledProcessError as e:
                    print(f"--- Warning: Project {proj_index+1} failed ---")
                    print(f"Command: {' '.join(command)}")
                    print(f"STDOUT: {e.stdout}")
                    print(f"STDERR: {e.stderr}")
                    all_successful = False
            
            # Create a merged file for this batch
            batch_symbols = {"Symbols": []}
            symbol_fullnames = set()
            
            for single_graph in single_graphs:
                if single_graph.exists():
                    try:
                        with open(single_graph, 'r') as f:
                            try:
                                single_data = json.load(f)
                                for symbol in single_data.get("Symbols", []):
                                    symbol_fullname = symbol.get("FullName")
                                    if symbol_fullname and symbol_fullname not in symbol_fullnames:
                                        symbol_fullnames.add(symbol_fullname)
                                        batch_symbols["Symbols"].append(symbol)
                            except json.JSONDecodeError:
                                print(f"Warning: Failed to parse JSON from {single_graph}")
                    except Exception as e:
                        print(f"Error reading {single_graph}: {str(e)}")
            
            # Write the merged batch result
            with open(batch_output, 'w') as f:
                json.dump(batch_symbols, f)
            
            print(f"Batch {batch_index//batch_size + 1} combined graph has {len(batch_symbols['Symbols'])} symbols")
            
            # We no longer need this block as we're processing one project at a time
            # The above batch processing code already handles running the commands and error reporting
        
        # After processing all batches, merge the results into a single comprehensive graph
        successful_batches = [bg for bg in batch_graphs if bg.exists()]
        
        if not successful_batches:
            print("Warning: No batch graphs were created successfully.")
            # Create an empty graph file to avoid later errors
            with open(CODE_GRAPH_PATH, 'w') as f:
                f.write('{"Symbols":[]}')
            return
            
        print(f"Merging {len(successful_batches)} batch graphs into a single comprehensive graph...")
        
        # Load and merge all graphs
        merged_graph = {"Symbols": []}
        symbol_fullnames = set()  # To track unique symbols by their full name
        
        for batch_graph in successful_batches:
            try:
                with open(batch_graph, 'r') as f:
                    batch_data = json.load(f)
                
                # Merge symbols, avoiding duplicates
                # The CodeSymbol class uses FullName as the unique identifier
                for symbol in batch_data.get("Symbols", []):
                    # Use FullName as a unique identifier (based on CodeSymbol class in C#)
                    symbol_fullname = symbol.get("FullName")
                    if symbol_fullname and symbol_fullname not in symbol_fullnames:
                        symbol_fullnames.add(symbol_fullname)
                        merged_graph["Symbols"].append(symbol)
                
                print(f"Added symbols from {batch_graph}")
            except Exception as e:
                print(f"Error processing batch graph {batch_graph}: {str(e)}")
        
        # Write the merged graph to the output file
        with open(CODE_GRAPH_PATH, 'w') as f:
            json.dump(merged_graph, f)
            
        total_symbols = len(merged_graph['Symbols'])
        print(f"Code graph built successfully with {total_symbols} total symbols.")
        
        # Save to cache for future use
        if total_symbols > 0:  # Only cache if we actually got symbols
            print("💾 Saving code graph to cache...")
            if save_to_cache(cache_file):
                print(f"✅ Code graph cached at: {cache_file}")
            else:
                print("⚠️ Failed to save to cache (non-critical)")
        else:
            print("⚠️ Not caching empty code graph")
            
    except Exception as e:
        print(f"Error during batch processing: {str(e)}")
        raise e
    finally:
        # Clean up temporary files
        try:
            import shutil
            shutil.rmtree(batch_dir)
            print(f"Cleaned up temporary directory: {batch_dir}")
        except Exception as e:
            print(f"Warning: Failed to clean up temporary directory: {str(e)}")
            pass

# (The 'expand_with_code_graph' function also needs this fix)
def expand_with_code_graph(seed_files: List[Path]) -> List[Path]:
    """
    Takes a list of seed files and uses the cached code graph to find all related files efficiently.
    """
    print(f"[DEBUG] expand_with_code_graph: Starting expansion with {len(seed_files)} seed files")
    print(f"[DEBUG] expand_with_code_graph: Seed files: {[str(f) for f in seed_files]}")
    
    if not seed_files:
        print(f"[DEBUG] expand_with_code_graph: No seed files provided, returning empty list")
        return []
        
    print(f"Expanding {len(seed_files)} seed file(s) with cached Code Graph...")
    
    # Use the cached code graph manager for efficient expansion
    print(f"[DEBUG] expand_with_code_graph: Importing code_graph_manager")
    from .code_graph_manager import code_graph_manager
    
    print(f"[DEBUG] expand_with_code_graph: Loading graph data from: {CODE_GRAPH_PATH}")
    graph_data = code_graph_manager.get_graph_data(CODE_GRAPH_PATH)
    if not graph_data:
        print(f"[DEBUG] expand_with_code_graph: Failed to load graph data, using seed files only")
        print(f"Warning: Could not load code graph from '{CODE_GRAPH_PATH}'. Using seed files only.")
        return seed_files
    
    print(f"[DEBUG] expand_with_code_graph: Graph data loaded successfully")
    print(f"[DEBUG] expand_with_code_graph: Dependency graph has {graph_data.dependency_graph.number_of_nodes()} nodes, {graph_data.dependency_graph.number_of_edges()} edges")
    
    # Convert seed files to strings for comparison
    seed_files_str = {str(f.resolve()) for f in seed_files}
    expanded_files = set(seed_files_str)  # Start with seed files
    print(f"[DEBUG] expand_with_code_graph: Seed files as strings: {list(seed_files_str)}")
    
    # Use the dependency graph for efficient expansion
    dependency_graph = graph_data.dependency_graph
    
    # For each seed file, find all connected files (both predecessors and successors)
    for seed_file_str in seed_files_str:
        print(f"[DEBUG] expand_with_code_graph: Processing seed file: {seed_file_str}")
        if seed_file_str in dependency_graph:
            print(f"[DEBUG] expand_with_code_graph: Seed file found in dependency graph")
            
            # Add files that depend on this seed file (predecessors)
            predecessors = set(dependency_graph.predecessors(seed_file_str))
            print(f"[DEBUG] expand_with_code_graph: Found {len(predecessors)} predecessors")
            expanded_files.update(predecessors)
            
            # Add files that this seed file depends on (successors)
            successors = set(dependency_graph.successors(seed_file_str))
            print(f"[DEBUG] expand_with_code_graph: Found {len(successors)} successors")
            expanded_files.update(successors)
            
            # Add second-degree connections for better coverage
            connected_files = list(predecessors) + list(successors)
            print(f"[DEBUG] expand_with_code_graph: Processing {len(connected_files)} connected files for second-degree connections")
            second_level_count = 0
            for connected_file in connected_files:
                if connected_file in dependency_graph:
                    # Add one more level of connections
                    second_level = set(dependency_graph.predecessors(connected_file))
                    second_level.update(dependency_graph.successors(connected_file))
                    second_level_count += len(second_level)
                    expanded_files.update(second_level)
            print(f"[DEBUG] expand_with_code_graph: Added {second_level_count} second-degree connections")
        else:
            print(f"[DEBUG] expand_with_code_graph: Seed file NOT found in dependency graph")
    
    print(f"[DEBUG] expand_with_code_graph: Total expanded files before filtering: {len(expanded_files)}")
    
    # Convert back to Path objects and filter existing files
    result_files = []
    skipped_files = []
    for file_str in expanded_files:
        try:
            path_obj = Path(file_str)
            if path_obj.exists():
                result_files.append(path_obj)
            else:
                skipped_files.append(file_str)
        except Exception as e:
            print(f"[DEBUG] expand_with_code_graph: Error processing file {file_str}: {e}")
            skipped_files.append(file_str)
    
    print(f"[DEBUG] expand_with_code_graph: Final result: {len(result_files)} existing files")
    print(f"[DEBUG] expand_with_code_graph: Skipped {len(skipped_files)} non-existing files")
    print(f"✅ Code Graph expanded {len(seed_files)} seed files to {len(result_files)} total files using cached data")
    return result_files

# (run_static_analysis can be removed as we are using the graph-based approach)