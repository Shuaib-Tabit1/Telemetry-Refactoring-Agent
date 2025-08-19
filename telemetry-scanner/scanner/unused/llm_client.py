import os
import json
import regex
from typing import Dict, Any
from openai import AzureOpenAI

# --- Constants ---
# It's recommended to use a model that supports JSON mode and has a large context window.
DEPLOYMENT_NAME = 'o4-mini' 

def get_client() -> AzureOpenAI:
    """
    Initializes and returns the AzureOpenAI client, checking for environment variables.
    
    Returns:
        An instance of the AzureOpenAI client.
        
    Raises:
        KeyError: If required environment variables are not set.
    """
    try:
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-05-01-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        return client
    except KeyError:
        raise KeyError(
            "ERROR: Please set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT environment variables."
        )

def get_telemetry_suggestions(client: AzureOpenAI, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    """
    Calls the OpenAI API to get telemetry suggestions and parses the JSON response.

    Args:
        client: The initialized AzureOpenAI client.
        system_prompt: The system prompt string.
        user_prompt: The user prompt string containing the code to analyze.

    Returns:
        A dictionary containing the parsed JSON response from the LLM.
    """
    print(" Calling LLM to analyze code and generate suggestions...")
    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1, # Lower temperature for more predictable, structured output
            max_tokens=4096
        )
        
        raw_content = response.choices[0].message.content

        # The LLM can sometimes wrap the JSON in markdown, so we extract it.
        json_match = regex.search(r"```json\s*(\{.*\}|\[.*\])\s*```|\{.*\}|\[.*\]", raw_content, regex.DOTALL)
        if not json_match:
            print(f" Warning: No valid JSON object found in LLM response.\nRaw Response: {raw_content}")
            return {}

        json_string = json_match.group(0).replace("```json", "").replace("```", "").strip()
        return json.loads(json_string)

    except json.JSONDecodeError:
        print(f"ERROR: Failed to decode JSON from LLM response.\nRaw Response: {raw_content}")
        return {}
    except Exception as e:
        print(f"An unexpected error occurred during the API call: {e}")
        return {}