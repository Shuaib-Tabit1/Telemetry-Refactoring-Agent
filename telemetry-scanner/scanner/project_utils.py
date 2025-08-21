import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List

def parse_dirs_proj(dirs_proj_path: Path) -> List[str]:
    """
    Parses a dirs.proj file to get a list of non-test C# project paths.
    """
    project_paths = []
    try:
        tree = ET.parse(dirs_proj_path)
        root = tree.getroot()
        # Find all ProjectReference nodes
        for project_ref in root.findall(".//{*}ProjectReference"):
            # Exclude test projects
            if project_ref.get("Test") != "true":
                path_str = project_ref.get("Include")
                if path_str:
                    # Make the path relative to the dirs.proj file's parent directory
                    full_path = (dirs_proj_path.parent / path_str).resolve()
                    project_paths.append(str(full_path))
    except Exception as e:
        print(f"Error parsing {dirs_proj_path}: {e}")
    
    return project_paths