
"""
Functions to handle Slack interactive component actions.
These functions will be triggered based on the action_id in the webhook payload.
"""

import requests
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def handle_send_out_reply(payload: Dict[str, Any]) -> Dict[str, str]:
    """
    Handler for the 'send-out-reply' action.
    Sends the edited response back to the email recipient.
    
    Args:
        payload: The parsed Slack webhook payload
        
    Returns:
        Dictionary with status and message
    """
    try:
        # Extract the edited email content from the payload
        if "state" in payload and "values" in payload["state"]:
            for block_id, block_values in payload["state"]["values"].items():
                for action_id, action_data in block_values.items():
                    if action_id == "plain_text_input-action" and "value" in action_data:
                        email_content = action_data["value"]
                        
                        # TODO: Implement actual email sending logic here
                        # This would connect to your email service
                        logger.info(f"Would send email with content: {email_content[:100]}...")
                        
                        return {
                            "status": "success",
                            "message": "Your edited response has been sent!"
                        }
        
        return {
            "status": "error",
            "message": "Could not find email content in the payload"
        }
    
    except Exception as e:
        logger.error(f"Error in handle_send_out_reply: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to send email: {str(e)}"
        }

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
