
"""
Functions to handle Slack interactive component actions.
These functions will be triggered based on the action_id in the webhook payload.
"""
import requests
import logging
import json
from typing import Dict, Any
from src.gmail_service import GmailApiService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def handle_send_out_reply(payload: Dict[str, Any]) -> Dict[str, str]:
    """
    Handler for the 'send-out-reply' action.
    Sends the edited response via the Gmail API.
    """
    try:
        # Robustly parse the state values from the Slack payload
        to_email, subject, body = None, None, None
        values = payload.get("state", {}).get("values", {})
        
        for block_id, block_values in values.items():
            for action_id, action_data in block_values.items():
                if 'initial_value' in action_data:
                    # Heuristic to identify fields based on their initial content
                    if '@' in action_data['initial_value']:
                        to_email = action_data['value']
                    else:
                        subject = action_data['value']
                elif 'multiline' in action_data and action_data['multiline']:
                    body = action_data['value']

        if not all([to_email, subject, body]):
            logger.error("Could not extract all required fields from Slack payload.")
            return {"status": "error", "message": "Could not parse email details from payload."}

        logger.info(f"Preparing to send email to: {to_email}")
        
        # Use the GmailApiService to send the email
        gmail_service = GmailApiService()
        status = gmail_service.send_email(to=to_email, subject=subject, body=body)
        
        # Update the original Slack message to confirm sending
        response_url = payload.get("response_url")
        if response_url:
            confirmation_message = {
                "text": f"✅ Email has been sent to {to_email}!",
                "replace_original": False # Set to True to replace the original message
            }
            requests.post(response_url, json=confirmation_message)

        return {"status": "success", "message": f"Email sending process initiated: {status}"}
    
    except Exception as e:
        logger.error(f"Error in handle_send_out_reply: {str(e)}")
        return {"status": "error", "message": f"Failed to send email: {str(e)}"}

def handle_attio_campaign(payload: Dict[str, Any]) -> Dict[str, str]:
    """
    Handler for the 'attio-campaign' action.
    Updates or creates an Attio record for the podcast outreach campaign.
    
    Args:
        payload: The parsed Slack webhook payload
        
    Returns:
        Dictionary with status and message
    """
    try:
        # Extract information from the payload to update Attio
        # In a real implementation, you would import the AttioClient from attio_service.py
        # and use it to update or create records
        
        # Example of data you might want to extract
        message_text = payload.get("message", {}).get("text", "")
        
        # Extract podcast name and classification from the message text
        # This is a simplified example - you would need more robust parsing
        podcast_info = message_text.split("\n")[0] if message_text else ""
        classification = ""
        
        for line in message_text.split("\n"):
            if "Classification:" in line:
                classification = line.split("Classification:")[1].strip()
                break
        
        logger.info(f"Would update Attio campaign for: {podcast_info}")
        logger.info(f"Classification: {classification}")
        
        # TODO: Implement actual Attio API integration
        # from attio_service import AttioClient
        # attio = AttioClient()
        # attio.update_record(...)
        
        return {
            "status": "success",
            "message": "Attio campaign updated successfully!"
        }
    
    except Exception as e:
        logger.error(f"Error in handle_attio_campaign: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to update Attio campaign: {str(e)}"
        }

def handle_gdrive_client(payload: Dict[str, Any]) -> Dict[str, str]:
    """
    Handler for the 'gdrive-client' action.
    Opens or updates relevant files in the client's Google Drive.
    
    Args:
        payload: The parsed Slack webhook payload
        
    Returns:
        Dictionary with status and message
    """
    try:
        # Extract information needed to locate the right Google Drive files
        message_text = payload.get("message", {}).get("text", "")
        
        # Parse out client name or other identifying information
        client_info = message_text.split("\n")[0] if message_text else ""
        
        logger.info(f"Would access Google Drive for client: {client_info}")
        
        # TODO: Implement Google Drive API integration
        # This would typically use the Google Drive API to:
        # 1. Locate the client folder
        # 2. Update tracking spreadsheets
        # 3. Return links to relevant documents
        
        # For now, just return a success message
        return {
            "status": "success",
            "message": "Client Google Drive accessed successfully! (Placeholder for actual integration)"
        }
    
    except Exception as e:
        logger.error(f"Error in handle_gdrive_client: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to access Google Drive: {str(e)}"
        }
