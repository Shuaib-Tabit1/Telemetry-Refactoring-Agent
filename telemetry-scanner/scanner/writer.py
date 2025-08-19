"""
writer.py
---------
Utility helpers to persist output artifacts (markdown, diff, JSON, etc.).
"""

from pathlib import Path
from typing import Union

def write_markdown(out_dir: Path, filename: str, content: str) -> None:
    """
    Ensure the output directory exists and write a UTF-8 markdown (or text) file.

    Parameters
    ----------
    out_dir   : Path
        Directory where the file will be created.
    filename  : str
        Name of the file, e.g. 'remediation.md'.
    content   : str
        File contents.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / filename).write_text(content, encoding="utf-8")

def write_text(out_dir: Path, filename: str, content: Union[str, bytes]) -> None:
    """
    Generic writer for arbitrary text or bytes.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    mode = "wb" if isinstance(content, bytes) else "w"
    with open(out_dir / filename, mode, encoding=None if mode == "wb" else "utf-8") as fh:
        fh.write(content)

# Example usage in cli.py / llm_scan_cli.py:
# write_markdown(out_dir, "remediation.md", md_text)
# (out_dir / "patch.diff").write_text(diff_text, encoding="utf-8")
