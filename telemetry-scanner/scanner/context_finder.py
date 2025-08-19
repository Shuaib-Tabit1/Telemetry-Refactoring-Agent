"""
Finds candidate files and enriches them with the necessary context
for the patch composer using semantic search.
"""
from __future__ import annotations
from typing import List, Dict
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Load the AI model. This can be done once when the module is loaded.
# 'all-MiniLM-L6-v2' is a good, general-purpose model.
print("Loading semantic search model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded.")

def find_candidate_files(repo_path: str, intent: Dict, top_k: int = 5) -> List[Path]:
    """
    Finds the top_k best C# file candidates using semantic search.
    """
    p = Path(repo_path)
    all_cs_files = [file for file in p.rglob("*.cs") if file.stat().st_size > 0]
    
    if not all_cs_files:
        return []

    query = intent.get("semantic_description")
    if not query:
        return all_cs_files[:top_k]

    file_contents = [path.read_text(encoding="utf-8", errors="ignore") for path in all_cs_files]
    
    print(f"Generating embeddings for {len(file_contents)} files...")
    query_embedding = model.encode([query])
    file_embeddings = model.encode(file_contents)

    similarities = cosine_similarity(query_embedding, file_embeddings)[0]
    
    # Get the indices of the top_k most similar files instead of just the single best one
    top_k_indices = np.argsort(similarities)[-top_k:][::-1]
    
    best_files = [all_cs_files[i] for i in top_k_indices]
    print(f"Top {top_k} semantic matches: {[f.name for f in best_files]}")
    
    return best_files

def enrich_context(files: List[Path], intent: Dict) -> str:
    """
    Loads the full content of the best candidate file to be used as context.
    
    """
    if not files:
        return ""
    
    best_file = files[0]
    
    try:
        return best_file.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading context file {best_file}: {e}")
        return ""
    

