"""
intent_builder.py
-----------------
One small LLM call that converts Jira ticket prose into a
machine‑readable “intent” JSON spec the rest of the pipeline can use.
"""

import json
import os
from typing import Optional
from openai import AzureOpenAI

# Lazy initialization of OpenAI client
_client: Optional[AzureOpenAI] = None

def get_openai_client() -> AzureOpenAI:
    """Get or create the OpenAI client."""
    global _client
    if _client is None:
        _client = AzureOpenAI(
            api_key=os.environ.get("AZURE_OPENAI_API_KEY", "your-api-key-here"),
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT", "your-endpoint-here"),
            api_version="2024-12-01-preview"
        )
    return _client

# _SYSTEM = """
# You are an expert in OpenTelemetry and C#. Your task is to analyze a Jira ticket and convert it into a highly detailed and structured JSON 'intent' that will drive an automated code remediation system.

# Follow this multi-step reasoning process:
# 1.  **Classify the ticket** into "CONFIGURATION" or "INSTRUMENTATION".
# 2.  **Formulate a Static Query:** Analyze the ticket for specific, structural code patterns. If a method name, class, or interface is mentioned or strongly implied, create a query for the `static_analysis_query` field. If the ticket is too vague for a precise structural query, this field MUST be `null`.
# 3.  **Define the Operation:** Fill out the `semantic_description`, `search_keywords`, and the detailed `telemetry_operation` object based on the user's request.

# The final JSON output must be detailed, unambiguous, and adhere strictly to the schema below.

# Return ONLY the JSON object with the following structure:

# - `issue_category` (string): CRITICAL. Must be "CONFIGURATION" or "INSTRUMENTATION".
# - `static_analysis_query` (object | null): A structured query for a static analysis tool to find precise code locations. The only supported query is "find_method_call". Example: `{"find_method_call": "AddHttpClientInstrumentation"}`. Set to `null` if the ticket is too vague.
# - `semantic_description` (string): CRITICAL. A concise summary of the business process or code path. Used for semantic search. Example: "The background job that processes uploaded images."
# - `search_keywords` (list[string]): A list of potential C# identifiers, method names, or keywords from the ticket.
# - `telemetry_operation` (object): A detailed description of the work to be done.
#     - `type` (string): The telemetry signal. Must be one of: "span", "metric", "log".
#     - `target_name` (string): The name of the existing span or metric to modify. Can be null if creating a new one.
#     - `action` (string): The operation to perform. Must be one of: "CREATE", "ADD_ATTRIBUTES", "UPDATE_NAME".
#     - `attributes_to_add` (list[object]): A list of attributes (tags) to add.
#         - `name` (string): The OpenTelemetry-compliant attribute name (e.g., `db.statement`).
#         - `value_source` (string): A description of where the value comes from. Examples: "the 'userId' variable in scope", "the literal string 'users.prod'", "the return value of 'GetTenantId()'".
#     - `new_span_name` (string): Required if `action` is "CREATE" and `type` is "span".
#     - `new_metric_details` (object): Required if `action` is "CREATE" and `type` is "metric".
# """

_SYSTEM = """
You are an expert in OpenTelemetry and C#. Your task is to deconstruct a Jira ticket and create a highly detailed and structured JSON 'intent' that will drive an automated code remediation system.

Follow these steps meticulously:
1.  **Identify Key Entities:** Read the entire ticket and extract all key technical entities. List the specific service names, attribute names, URLs, and technologies mentioned.
2.  **Synthesize the Core Goal:** Based on the entities you identified, write a one-sentence summary of the user's primary goal. This summary will become the `semantic_description`.
3.  **Generate the JSON Plan:** Use your goal summary and the identified entities to populate the following JSON schema. If you can deduce a specific method call from the goal, create a `static_analysis_query`; otherwise, it MUST be `null`.

The final JSON output must be detailed, unambiguous, and adhere strictly to the schema below.

Return ONLY the JSON object with the following structure:

- `issue_category` (string): CRITICAL. Must be "CONFIGURATION" or "INSTRUMENTATION".
- `static_analysis_query` (object | null): A structured query for a static analysis tool to find precise code locations. Example: `{"find_method_call": "AddHttpClientInstrumentation"}`. Set to `null` if the ticket is too vague.
- `semantic_description` (string): CRITICAL. The one-sentence "Core Goal" you synthesized in step 2.
- `search_keywords` (list[string]): A list of potential C# identifiers or keywords from the "Key Entities" you identified in step 1.
- `telemetry_operation` (object): A detailed description of the work to be done.
    - `type` (string): The telemetry signal. Must be one of: "span", "metric", "log".
    - `target_name` (string): The name of the existing span or metric to modify. Can be null if creating a new one.
    - `action` (string): The operation to perform. Must be one of: "CREATE", "ADD_ATTRIBUTES", "UPDATE_NAME".
    - `attributes_to_add` (list[object]): A list of attributes (tags) to add.
        - `name` (string): The OpenTelemetry-compliant attribute name (e.g., `db.statement`).
        - `value_source` (string): A description of where the value comes from. Examples: "the 'userId' variable in scope", "the literal string 'users.prod'", "the return value of 'GetTenantId()'".
    - `new_span_name` (string): Required if `action` is "CREATE" and `type` is "span".
    - `new_metric_details` (object): Required if `action` is "CREATE" and `type` is "metric".
"""


def extract_intent(ticket_text: str) -> dict:
    prompt = (
        f"{_SYSTEM}\n\n"
        "### Ticket ###\n"
        f"{ticket_text.strip()}\n\n"
        "Return valid JSON only."
    )

    response = get_openai_client().chat.completions.create(
        model="o3",          
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    # 3. Access the response content via attributes
    json_string = response.choices[0].message.content

    return json.loads(json_string)