"""Helper functions for embeddings."""

from dotenv import load_dotenv
import os
from pathlib import Path

# load environment variables from .env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from openai import OpenAI
import requests
from typing import List
import base64
import numpy as np

# Initialize OpenAI client with API key from environment
_api_key = os.getenv("OPENAI_API_KEY")
if not _api_key:
    raise ValueError("OPENAI_API_KEY is not set")
_client = OpenAI(api_key=_api_key)


def generate_embedding(text: str,
                       model: str = "text-embedding-3-small") -> List[float]:
    """
    Generate an embedding vector for the given text using the OpenAI Embedding API.
    Uses text-embedding-3-small by default.
    """
    # Replace newlines to avoid splitting issues
    cleaned = text.replace("\n", " ")
    response = _client.embeddings.create(input=[cleaned], model=model)
    # Extract and normalize the embedding to a Python list of floats
    embedding = response.data[0].embedding
    if hasattr(embedding, "tolist"):
        embedding = embedding.tolist()
    return list(embedding)


def decode_embedding(b64json, dtype=np.float32) -> List[float]:
    """
    Decode a Base64-encoded embedding blob (Mongo $binary format or raw base64 string)
    into a Python list of floats.
    """
    if isinstance(b64json, dict) and "$binary" in b64json:
        b64 = b64json["$binary"]
    else:
        b64 = b64json
    raw = base64.b64decode(b64)
    emb = np.frombuffer(raw, dtype=dtype)
    return emb.tolist()


def send_message(message: str):
    """
    Send a message to Slack using the configured webhook URL.
    Returns the status code from the Slack API response.
    """
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    payload = {"text": message}
    response = requests.post(webhook_url, json=payload)
    
    # Print the response details
    print(f"Status code: {response.status_code}")
    print(f"Response text: {response.text}")
    try:
        # Try to parse and print JSON response if available
        if response.text:
            response_json = response.json()
            print(f"Response payload: {response_json}")
    except Exception as e:
        print(f"Could not parse response as JSON: {e}")
    
    return response.status_code


def send_interactive_message(message: str, draft: str, sender_email: str = "", subject_line: str = "", attio_url: str = "", gdrive_url: str = ""):
    """
    Send an interactive message to Slack with buttons and a text input area.
    
    Args:
        message: The notification message to display at the top
        draft: The draft email content to populate in the text input area
        sender_email: The email address of the sender
        subject_line: The subject line of the email
        attio_url: URL for the Attio campaign button
        gdrive_url: URL for the Google Drive client button
        
    Returns:
        The status code from the Slack API response
    """
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    
    # Debug input parameters
    print("====== SLACK NOTIFICATION DEBUG ======")
    print(f"Message length: {len(message)} characters")
    print(f"Draft length: {len(draft)} characters")
    print(f"Sender email: {sender_email}")
    print(f"Subject line: {subject_line}")
    print(f"Attio URL: {attio_url}")
    print(f"GDrive URL: {gdrive_url}")
    
    # Check for overly long text that might cause issues
    if len(message) > 3000:
        print("WARNING: Message is very long (>3000 chars), truncating for Slack")
        message = message[:3000] + "... [truncated]"
    
    # Create the base blocks for the payload
    blocks = [{
        "type": "section",
        "text": {
            "type": "plain_text",
            "text": message,
            "emoji": True
        }
    }, {
        "type": "divider"
    }, {
        "type": "input",
        "element": {
            "type": "plain_text_input",
            "action_id": "plain_text_input-action",
            "initial_value": sender_email
        },
        "label": {
            "type": "plain_text",
            "text": "Sender",
            "emoji": True
        }
    }, {
        "type": "input",
        "element": {
            "type": "plain_text_input",
            "action_id": "plain_text_input-action",
            "initial_value": subject_line
        },
        "label": {
            "type": "plain_text",
            "text": "Subject",
            "emoji": True
        }
    }, {
        "type": "input",
        "element": {
            "type": "plain_text_input",
            "multiline": True,
            "action_id": "plain_text_input-action",
            "initial_value": draft
        },
        "label": {
            "type": "plain_text",
            "text": "Draft Reply",
            "emoji": True
        }
    }]

    # Create action elements list starting with the "Send" button that's always included
    action_elements = [{
        "type": "button",
        "text": {
            "type": "plain_text",
            "text": "Send Out Edited Response",
            "emoji": True
        },
        "value": "click_me_123",
        "action_id": "send-out-reply"
    }]

    # Only add the Attio button if a URL is provided
    if attio_url and attio_url.strip():
        action_elements.append({
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "Attio Campaign",
                "emoji": True
            },
            "value": "click_me_123",
            "action_id": "attio-campaign",
            "url": attio_url
        })

    # Only add the GDrive button if a URL is provided
    if gdrive_url and gdrive_url.strip():
        action_elements.append({
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "Client Google Drive",
                "emoji": True
            },
            "value": "click_me_123",
            "action_id": "gdrive-client",
            "url": gdrive_url
        })

    # Add the actions block to the blocks list if there are any action elements
    if action_elements:
        blocks.append({
            "type": "actions",
            "elements": action_elements
        })

    # Create the final payload
    payload = {
        "blocks": blocks
    }
    
    import json
    print(f"Payload being sent to Slack: {json.dumps(payload)}")
    
    # Make the request
    try:
        response = requests.post(webhook_url, json=payload)
        
        # Print the response details
        print(f"Status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response text: {response.text}")
        
        try:
            # Try to parse and print JSON response if available
            if response.text:
                response_json = response.json()
                print(f"Response payload: {response_json}")
        except Exception as e:
            print(f"Could not parse response as JSON: {e}")
        
        return response.status_code
    except Exception as e:
        import traceback
        print(f"Exception when sending to Slack: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return 500
    finally:
        print("====== END SLACK NOTIFICATION DEBUG ======")
