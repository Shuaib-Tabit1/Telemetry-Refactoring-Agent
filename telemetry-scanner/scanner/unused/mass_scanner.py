"""
mass_scanner.py
Fan-out async calls: (intent + code chunk) → LLM → finding JSON.
"""

from __future__ import annotations
import asyncio
import json
from typing import List, Dict
import os
from openai import AsyncAzureOpenAI

client = AsyncAzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)

_CHUNK_PROMPT = """
You are a telemetry auditor.

### Intent ###
```json
{intent_json}
```

### C# Chunk ({file}:{start}-{end}) ###
```csharp
{text}
```

If this chunk violates the intent in any telemetry dimension
(spans, metrics, logs), return JSON:
{{
"file":"{file}",
"start":{start},
"end":{end},
"issue":"missing_span|missing_metric|missing_log|missing_tag",
"details":"short explanation",
"confidence":0.0‑1.0,
"mini_diff":"```diff\\n- before\\n+ after\\n```"
}}

Otherwise reply exactly {{}} (two braces) with no extra text.
""".strip()

async def _scan_chunk(chunk: Dict, intent: Dict, model: str) -> Dict:
    prompt = _CHUNK_PROMPT.format(
        intent_json=json.dumps(intent, indent=2), **chunk
    )
    resp = await client.chat.completions.create(
    model=model,                                     # Note: parameter is 'model', not 'engine'
    messages=[{"role": "user", "content": prompt}],
    response_format={"type": "json_object"}
)
    txt = resp.choices[0].message.content.strip()
    return json.loads(txt) if txt.startswith("{") else {}


async def mass_scan(
    intent: Dict,
    chunks: List[Dict],
    model: str = "o4-mini",        
    max_parallel: int = 20,
) -> List[Dict]:
    sem = asyncio.Semaphore(max_parallel)

    async def bounded(c):
        async with sem:
            return await _scan_chunk(c, intent, model)

    results = await asyncio.gather(*(bounded(c) for c in chunks))
    return [r for r in results if r]
