import os
from typing import List

def load_context_from_directory(context_dir: str) -> str:
    """
    Loads all .cs and .tt files from a directory and concatenates them.

    Args:
        context_dir: The path to the directory containing context files.

    Returns:
        A single string containing all context, or an empty string if the
        directory is not found or contains no valid files.
    """
    print(f"Reading company-specific context from '{context_dir}' folder...")
    context_str = ""
    if not os.path.isdir(context_dir):
        print(f" Warning: Context directory not found: {context_dir}")
        return ""

    context_files: List[str] = [f for f in os.listdir(context_dir) if f.endswith((".cs", ".tt"))]

    for filename in context_files:
        file_path = os.path.join(context_dir, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                context_str += f"--- File: {filename} ---\n"
                context_str += f.read()
                context_str += "\n\n"
        except Exception as e:
            print(f" Warning: Could not read context file {filename}. Error: {e}")

    if not context_str:
        print(f"️️Warning: No context files were loaded from '{context_dir}'.")

    return context_str.strip()