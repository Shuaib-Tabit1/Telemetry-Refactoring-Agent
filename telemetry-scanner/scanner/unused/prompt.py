
from typing import Optional

SYSTEM_PROMPT = """
You are an expert Senior Site Reliability Engineer and a C# specialist with deep knowledge of .NET observability.
"""

USER_PROMPT_WITH_INTERFACE = """
**Your Goal:**
You are to perform a complete observability review of the provided C# implementation. Your task is to identify all critical observability gaps and provide a complete, actionable solution for each.

---
### 1. General Principles (Your Knowledge Base)
- All suggested code must adhere to the patterns of the .NET `System.Diagnostics` library (`Activity`, `Counter`, `Histogram`).
- All suggested attributes and tags must follow standard OpenTelemetry Semantic Conventions.
- **Service Mesh Awareness:** Assume baseline HTTP server telemetry (request counts, latency) is provided by an Istio service mesh. Do NOT suggest this basic telemetry.
- **Duration Measurement:** When a trace `Activity` is present, you MUST get the latency measurement from the built-in `activity.Duration` property. Do NOT use a separate `Stopwatch` object.

---
### 2. Company-Specific Patterns & Rules (Provided Context)
This is the required way of implementing telemetry at this company. You MUST follow these patterns.

<COMPANY_CONTEXT>
{company_context_code}
</COMPANY_CONTEXT>

---
### 3. The Telemetry Interface (The "Source of Truth")
This interface is the contract that the class under review MUST follow.

<TELEMETRY_INTERFACE>
{interface_code}
</TELEMETRY_INTERFACE>

---
### 4. Implementation to Review
This is the specific C# service that needs to be analyzed.

<IMPLEMENTATION_TO_REVIEW>
{implementation_code}
</IMPLEMENTATION_TO_REVIEW>
---

**Instructions & Workflow:**
You will analyze the `<IMPLEMENTATION_TO_REVIEW>` on a method-by-method basis. For each method, you MUST follow this exact sequence:

1.  **Identify a Gap:** First, analyze the method's business logic to identify a critical observability gap (e.g., a database call is untracked, a failure condition is not counted, etc.).
2.  **Check the Interface:** Next, check the `<TELEMETRY_INTERFACE>` to see if a suitable metric or trace for that gap has already been defined. **As part of this, you must also critique the interface. If an existing metric is ambiguous or not specific enough for the operation (e.g., a generic 'GetErrors' counter for a specific 'GetByID' method), you must consider that a suitable definition does not exist.**
3.  **Generate a Solution:**
    * **If a definition already exists** but is not used, your suggestion should provide the `instrumentationCode` to correctly implement it. The `interfaceCode` in your response for this item MUST be `null`.
    * **If a definition does not exist**, your suggestion must include both the new `interfaceCode` to define the new telemetry and the `instrumentationCode` to implement it.
4.  **Repeat:** Continue this process until all critical gaps in the method are addressed.

**Output Format:**
You MUST format your response as a single JSON object with one key, "suggestions". The value should be a list of JSON objects. Each object must have FOUR keys:
- `targetMethod`: The name of the method for the suggestion.
- `modifiedMethodCode`: The **complete C# code for the entire method**, now including the new instrumentation and comments explaining the changes.
- `interfaceCode`: The C# code to be added to the interface file. This MUST be `null` if the telemetry is already defined.
- `reason`: A brief explanation for the suggestion.
"""


USER_PROMPT_WITHOUT_INTERFACE="""
**Your Goal:**
You are to act as an expert Senior Site Reliability Engineer performing a deep observability review of the provided C# service. Since no telemetry interface is provided, you must invent a complete, modern, and robust telemetry strategy from scratch based on a deep analysis of the code's business logic.

---
### 1. General Principles (Your Knowledge Base)
- All suggested code must adhere to the patterns of the .NET `System.Diagnostics` library (`Activity`, `Counter`, `Histogram`).
- All suggested attributes and tags must follow standard OpenTelemetry Semantic Conventions.
- **Service Mesh Awareness:** Assume baseline HTTP server telemetry (request counts, latency) is provided by an Istio service mesh. Do NOT suggest this basic telemetry.
- **Duration Measurement:** When a trace `Activity` is present, you MUST get the latency measurement from the built-in `activity.Duration` property. Do NOT use a separate `Stopwatch` object.

---
### 2. Company-Specific Patterns & Rules (Provided Context)
This is the required way of implementing telemetry at this company. You MUST follow these patterns.

<COMPANY_CONTEXT>
{company_context_code}
</COMPANY_CONTEXT>

---
### 3. Code to Review
This is the specific C# service that needs to be analyzed.

<IMPLEMENTATION_TO_REVIEW>
{implementation_code}
</IMPLEMENTATION_TO_REVIEW>
---

**Instructions & Workflow:**
You MUST follow this exact sequence:

1.  **Deep Analysis:** You will perform a deep analysis of the entire class. You MUST analyze **every method**, including `private` helper methods, not just the public gRPC endpoints.
2.  **Identify Critical Gaps:** Your primary goal is to identify critical observability gaps by analyzing the business logic. Pay special attention to:
    * **External Dependencies:** Any I/O operations, such as database calls (`CosmosClient`) or external HTTP requests (`HttpClient` to MS Graph), that are not traced or measured.
    * **Logical Flaws:** Existing instrumentation that is incorrect, such as a method using metrics that belong to a different method (a common copy-paste error).
    * **Missing Signals:** Key operations that lack success/failure counters, making it impossible to calculate a success rate.
3.  **Design a Unified Interface:** Based on all the gaps you find, design a single, consolidated C# interface that contains all the necessary telemetry definitions.
4.  **Generate Implementation Code:** For each identified gap, provide the specific C# code needed to implement the telemetry correctly within the target method.

**Output Format:**
You MUST format your response as a single JSON object with **two** top-level keys:

1.  `consolidatedInterfaceFile`: A single string containing the C# code for the **complete and final** new telemetry interface. This interface MUST contain **all** the necessary definitions for every suggestion you have made.
2.  `suggestions`: A list of JSON objects, where each object represents a code change and has THREE keys:
    - `targetMethod`: The name of the method for the suggestion.
    - `modifiedMethodCode`: The C# code to add within the method. This code should be surgical and integrate with the existing logic.
    - `reason`: A clear, concise explanation of the specific business logic gap this change fixes.
"""

def build_user_prompt(
    company_context: str,
    implementation_code: str,
    interface_code: Optional[str] = None
) -> str:
    """
    Selects and formats the appropriate prompt based on whether an interface file is provided.

    Args:
        company_context: Content of company-specific coding patterns.
        implementation_code: The C# code of the service to be analyzed.
        interface_code: The C# code of the telemetry interface, if it exists.

    Returns:
        The fully formatted user prompt string for the LLM.
    """
    if interface_code:
        return USER_PROMPT_WITH_INTERFACE.format(
            company_context_code=company_context or "No company context provided.",
            interface_code=interface_code,
            implementation_code=implementation_code
        )
    else:
        return USER_PROMPT_WITHOUT_INTERFACE.format(
            company_context_code=company_context or "No company context provided.",
            implementation_code=implementation_code
        )