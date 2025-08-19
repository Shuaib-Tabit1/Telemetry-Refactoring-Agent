import os
from jira import JIRA
import re

def get_formatted_ticket_text(ticket_key: str) -> str:
    """
    Connects to Jira, fetches a ticket, and formats the key fields
    into a single text block for the LLM.
    """
    try:
        server = os.environ["JIRA_SERVER"]
        email = os.environ["JIRA_USER_EMAIL"]
        token = os.environ["JIRA_API_TOKEN"]

        jira_client = JIRA(
            server=server,
            basic_auth=(email, token)
        )

        # Fetch the full issue object from Jira
        issue = jira_client.issue(ticket_key)
        
        # Extract the most important fields
        summary = issue.fields.summary
        description = issue.fields.description
        components = [c.name for c in issue.fields.components]
        
        # Format them into a clean text block
        formatted_text = f"Title: {summary}\n\n"
        if components:
            formatted_text += f"Components: {', '.join(components)}\n\n"
        
        formatted_text += f"Description:\n{description}"
        
        return formatted_text
        
    except KeyError:
        print("Error: Please set JIRA_SERVER, JIRA_USER_EMAIL, and JIRA_API_TOKEN environment variables.")
        return ""
    except Exception as e:
        print(f"An error occurred while fetching the Jira ticket '{ticket_key}': {e}")
        return ""
    


def clean_jira_text(raw_text: str) -> str:
    """
    Cleans raw Jira description text by removing formatting, links, and other noise.
    """
    # 1. Remove the entire Atlassian Document Format (ADF) JSON block
    cleaned_text = re.sub(r'\{adf:.*?\{adf\}', '', raw_text, flags=re.DOTALL)
    
    # 2. Remove image tags (e.g., !image.png|...!)
    # This improved regex is more general.
    cleaned_text = re.sub(r'![^!]+!', '', cleaned_text)
    
    # 3. Simplify Jira links [text|url] to just the text
    cleaned_text = re.sub(r'\[\+?([^|\]]+)\|[^\]]+\]', r'\1', cleaned_text)

    # 4. Remove standalone URLs
    cleaned_text = re.sub(r'https?://\S+', '', cleaned_text)
    
    # 5. Normalize multiple newlines to a maximum of two
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)

    # 6. Remove any remaining Jira-specific markup like horizontal rules
    cleaned_text = cleaned_text.replace('----', '')
    
    return cleaned_text.strip()