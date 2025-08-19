"""
chunker.py
----------
Walks every .cs file and splits it into ≤ max_lines chunks.
"""

from pathlib import Path
from typing import Iterator, Dict

def chunk_service(service_path: str, max_lines: int = 300) -> Iterator[Dict]:
    """
    Yield dictionaries:
        { file, start, end, text }
    where 'start'/'end' are 1‑based line numbers.
    """
    for cs_file in Path(service_path).rglob("*.cs"):
        lines = cs_file.read_text(encoding="utf-8", errors="ignore").splitlines()
        for i in range(0, len(lines), max_lines):
            yield {
                "file": str(cs_file),
                "start": i + 1,
                "end": min(i + max_lines, len(lines)),
                "text": "\n".join(lines[i : i + max_lines])
            }
