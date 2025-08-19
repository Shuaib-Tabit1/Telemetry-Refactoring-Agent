import os
from typing import List, Tuple

# Constants
FILE_CONTENT_TRIM_LINE_LIMIT = 500
TRIM_MARKER = "\n\n... (file trimmed for brevity) ...\n\n"

def _trim_content(content: str) -> str:
    """Trims file content if it exceeds the line limit."""
    lines = content.splitlines()
    if len(lines) > FILE_CONTENT_TRIM_LINE_LIMIT:
        return "\n".join(lines[:FILE_CONTENT_TRIM_LINE_LIMIT]) + TRIM_MARKER
    return content

def load_source_files(directory: str, max_files: int = 2) -> List[Tuple[str, str]]:
    """
    Finds, reads, and trims C# source files from a given directory.

    Args:
        directory: The path to the directory containing .cs files.
        max_files: The maximum number of files to load.

    Returns:
        A list of tuples, where each tuple contains a filename and its content.
        Returns an empty list if the directory is not found or contains no .cs files.
    """
    if not os.path.isdir(directory):
        print(f"Error: Service path not found: {directory}")
        return []

    all_files = sorted([f for f in os.listdir(directory) if f.endswith(".cs")])
    selected_files = all_files[:max_files]
    
    print(f"Found {len(all_files)} C# files. Selecting the first {len(selected_files)}: {selected_files}")

    loaded_files: List[Tuple[str, str]] = []
    for filename in selected_files:
        file_path = os.path.join(directory, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                trimmed_content = _trim_content(content)
                loaded_files.append((filename, trimmed_content))
        except Exception as e:
            print(f" Warning: Could not read source file {filename}. Error: {e}")
            
    return loaded_files