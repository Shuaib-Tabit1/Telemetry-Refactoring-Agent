"""
patch_composer.py
Ask the LLM for the full, remediated code file plus an explanation.
"""
from __future__ import annotations
import json
import os
from typing import Tuple, List, Dict, Optional
from pathlib import Path
from openai import AzureOpenAI

# Lazy initialization of OpenAI client
_client: Optional[AzureOpenAI] = None

def get_openai_client() -> AzureOpenAI:
    """Get or create the OpenAI client."""
    global _client
    if _client is None:
        _client = AzureOpenAI(
            api_version="2024-12-01-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        )
    return _client

def compose_patch(intent: dict, file_contexts: List[Dict], model: str = "o3") -> Tuple[str, str]:
    """
    Asks the LLM to generate a single unified diff to fix a telemetry gap
    across multiple files.
    """
    code_context_str = ""
    for context in file_contexts:
        code_context_str += f"--- FILE: {context['path'].name} ---\n"
        code_context_str += f"```csharp\n{context['content']}\n```\n\n"

    system_prompt = (
        "You are an expert .NET developer specializing in OpenTelemetry. "
        "Your task is to generate a precise, unified diff to implement a telemetry request.\n\n"
        "## Guiding Principles\n"
        "1.  **Use Idiomatic Code:** Always prefer simple, built-in OpenTelemetry or .NET SDK library features over complex, manual reimplementations. "
        "2.  **Follow Conventions:** Adhere strictly to OpenTelemetry semantic conventions for all attribute names (e.g., `db.statement`, `http.method`, `server.address`). Do not invent custom attribute names.\n"
        "3.  **Be Consistent:** Analyze the provided code to infer existing patterns. Use pre-defined `ActivitySource` or `Meter` instances if they already exist in the code rather than creating new ones.\n"
        "\n## Your Task\n"
        "Analyze the code to find the exact locations to apply the change based on the intent. "
        "Generate ONE unified diff that correctly implements all changes. "
        "The diff format should start with `--- a/path/to/file.cs` and `+++ b/path/to/file.cs` for each file. "
        "Place the entire diff inside a single ```diff code block. "
        "After the diff, provide a concise '### Explanation' of your changes."
    )

    user_prompt = (
        "## Intent\n"
        f"```json\n{json.dumps(intent, indent=2)}\n```\n\n"
        "## Full Code of Affected Files\n"
        f"{code_context_str}\n\n"
    )
    
    response = get_openai_client().chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    resp = response.choices[0].message.content.strip()

    # Parsing logic for a diff block
    diff_text, md_text = "", resp
    if "```diff" in resp:
        _before, after = resp.split("```diff", 1)
        diff_block, remainder = after.split("```", 1)
        diff_text = diff_block.strip()
        md_text = remainder.strip() if remainder.strip() else _before.strip()

    return diff_text, md_text

def select_files_for_edit(intent: dict, candidate_contexts: List[Dict], model: str = "o3") -> List[Path]:
    """
    Uses an LLM with Chain-of-Thought to select all necessary files.
    """
    if not candidate_contexts:
        return []

    code_context_str = ""
    candidate_paths = {context['path'].name: context['path'] for context in candidate_contexts}
    for context in candidate_contexts:
        code_context_str += f"--- CANDIDATE FILE: {context['path'].name} ---\n"
        code_context_str += f"```csharp\n{context['content']}\n```\n\n"

    # New Chain-of-Thought Prompt
    prompt = (
        "You are an expert software engineer analyzing a codebase to find all locations for a required change.\n\n"
        "## Intent\n"
        f"A user wants to make a change related to this topic: '{intent['semantic_description']}'\n\n"
        "## Candidate Files and Their Full Code\n"
        f"Here are the candidate files and their complete source code:\n\n{code_context_str}"
        "## Your Task\n"
        "Follow these steps to determine the correct files to modify:\n"
        "1.  **Analysis:** For each candidate file, write a one-sentence analysis of its relevance to the user's intent.\n"
        "2.  **Reasoning:** Based on your analysis, provide a step-by-step explanation for which file(s), if any, should be modified.\n"
        "3.  **Final Answer:** Based on your reasoning, provide a final answer in a JSON block. The JSON should contain a single key, \"files\", with a list of the full names of the files you are highly confident should be changed. If none are correct, the list should be empty."
        "\n\nRespond using the following markdown format:\n\n"
        "### Analysis\n"
        "- `FileA.cs`: [Your one-sentence analysis here.]\n"
        "- `FileB.cs`: [Your one-sentence analysis here.]\n\n"
        "### Reasoning\n"
        "[Your step-by-step reasoning here.]\n\n"
        "### Final Answer\n"
        "```json\n"
        "{\n"
        "  \"files\": [\"FileB.cs\"]\n"
        "}\n"
        "```"
    )

    response = get_openai_client().chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
        # We remove response_format because we now expect a markdown response, not just JSON.
    )
    
    try:
        response_text = response.choices[0].message.content
        if response_text is None:
            # Handle empty response due to content filters, etc.
            finish_reason = response.choices[0].finish_reason
            print(f"Warning: LLM response was empty. Finish Reason: '{finish_reason}'. Rejecting batch.")
            return []

        # New parsing logic to find the JSON block within the markdown
        json_block_start = response_text.find("```json")
        if json_block_start == -1:
            print("Warning: LLM did not return a JSON block. Rejecting batch.")
            return []
        
        json_str = response_text[json_block_start + 7:] # Move past "```json"
        json_str = json_str.split("```")[0] # Get content before the closing ```

        data = json.loads(json_str)
        selected_names = data.get("files", [])
        
        if not isinstance(selected_names, list):
             return []

        selected_paths = [candidate_paths[name] for name in selected_names if name in candidate_paths]
        
        if selected_paths:
            print(f"LLM selected {len(selected_paths)} file(s) for editing: {[p.name for p in selected_paths]}")
        else:
            print("LLM indicated no files in this batch need to be changed.")
            
        return selected_paths
    except (json.JSONDecodeError, KeyError, IndexError, AttributeError):
        print("Warning: LLM returned a malformed response. Rejecting batch.")
        return []