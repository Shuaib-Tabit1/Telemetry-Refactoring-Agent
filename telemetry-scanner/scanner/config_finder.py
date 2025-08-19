"""
Finds key configuration files using a layered search strategy.
"""
from __future__ import annotations
from typing import List
from pathlib import Path

def find_config_files(repo_path: str) -> List[Path]:
    """
    Finds a list of configuration files using a prioritized, multi-layered search.
    """
    p = Path(repo_path)
    # Use a dictionary to store found files to prevent duplicates
    # while preserving the order of discovery (priority).
    found_files = {}

    # --- Layer 1: Search for Primary Targets ---
    primary_targets = ["Program.cs", "Startup.cs", "appsettings.json"]
    for filename in primary_targets:
        for match in p.rglob(filename):
            if match not in found_files:
                found_files[match] = True

    # --- Layer 2: Search for Common Wildcard Patterns ---
    wildcard_patterns = [
        # "*Extensions.cs", "*Module.cs", "*Configuration.cs",
        # "*Telemetry*.cs", "*Instrumentation*.cs", "*Observability*.cs",
        # "*Monitoring*.cs", "*Tracing*.cs", "*Metrics*.cs", "*Logging*.cs",
        # "*Middleware*.cs", "*Filter*.cs", "*Interceptor*.cs", "*Handler*.cs", 
        # "*HostedService*.cs", "*StartupFilter*.cs", "*DependencyInjection*.cs",
        # "*Activity*.cs", "*Diagnostics*.cs", "*Source*.cs", "*Listener*.cs",
        # "*Client*.cs", "*Provider*.cs", "*Bootstrap*.cs", "*Bootstrapper*.cs",
        # "*Initializer*.cs", "*Factory*.cs", "*Hub*.cs", "*Processor*.cs",
        # "*Worker*.cs", "*Options*.cs", "*Settings*.cs", "*Config*.cs",
        # "*Collector*.cs"
        "*Extensions.cs",
        "*Module.cs",
        "*Application.cs",
        "Global.asax.cs" 
    ]
    for pattern in wildcard_patterns:
        for match in p.rglob(pattern):
            if match not in found_files:
                found_files[match] = True
    
    # --- Layer 3: Search by File Content as a Catch-All ---
    content_keywords = [
        ".AddOpenTelemetry",
        ".AddServiceTelemetry",
        ".AddHttpClientInstrumentation",
        "IServiceCollection",
    ]
    for file_path in p.rglob("*.cs"):
        if file_path not in found_files:
            try:
                content = file_path.read_text(encoding="utf-8")
                if any(keyword in content for keyword in content_keywords):
                    found_files[file_path] = True
            except Exception:
                continue # Ignore files that can't be read

    # Convert the dictionary keys back to a list
    return list(found_files.keys())