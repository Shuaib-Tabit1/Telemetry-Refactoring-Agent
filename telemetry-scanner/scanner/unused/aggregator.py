"""
aggregator.py
Merge & deduplicate chunk findings based on highest confidence.
"""

from typing import List, Dict, Tuple

def _key(f: Dict) -> Tuple:
    return (f["file"], f["issue"], f.get("details", ""), f["start"], f["end"])

def merge_findings(raw: List[Dict], min_conf: float = 0.15) -> List[Dict]:
    merged = {}
    for f in raw:
        if f.get("confidence", 0) < min_conf:
            continue
        k = _key(f)
        if k not in merged or f["confidence"] > merged[k]["confidence"]:
            merged[k] = f
    return list(merged.values())