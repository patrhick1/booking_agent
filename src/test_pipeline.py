
#!/usr/bin/env python3
"""
Test script to run the booking agent pipeline with custom email parameters.
This script allows testing the full pipeline without needing actual email integration.
"""

import sys
import os
import json

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the agent from main_v2.py
from src.main_v2 import graph

def test_agent_pipeline(email_text, subject, sender_name, sender_email):
    """
    Run the agent pipeline with the provided email parameters.
    
    Args:
        email_text (str): The content of the email
        subject (str): The subject line of the email
        sender_name (str): The name of the sender
        sender_email (str): The email address of the sender
    
    Returns:
        dict: The final state after pipeline completion
    """
    print("\n" + "="*50)
    print(f"STARTING PIPELINE TEST")
    print(f"Sender: {sender_name} <{sender_email}>")
    print(f"Subject: {subject}")
    print("="*50 + "\n")
    
    # Initialize state with email text and metadata
    state = {
        "email_text": email_text,
        "subject": subject,
        "sender_name": sender_name,
        "sender_email": sender_email
    }
    
    # Generate a unique thread ID for each request
    import uuid
    thread_id = str(uuid.uuid4())
    
    # Create the properly structured thread object for langgraph
    thread = {"configurable": {"thread_id": thread_id}}
    
    try:
        # Invoke the agent graph with the proper parameters
        result = graph.invoke(state, thread)
        
        # Print results
        print("\n" + "="*50)
        print("PIPELINE COMPLETED")
        print("="*50)
        
        # Print a summary of the key results
        print("\nRESULTS SUMMARY:")
        print(f"Classification: {result.get('label', 'N/A')}")
        if 'rejection_type' in result:
            print(f"Rejection Type: {result.get('rejection_type', 'N/A')}")
        print(f"Draft Generated: {'Yes' if result.get('draft') else 'No'}")
        print(f"Slack Notification: {result.get('notification_status', 'Not sent')}")
        print(f"Webhook Status: {result.get('webhook_status', 'Not called')}")
        
        if result.get('gdrive_url'):
            print(f"Google Drive URL: {result.get('gdrive_url')}")
            
        # Ask if user wants to see the full response details
        show_details = input("\nShow full draft and details? (y/n): ")
        if show_details.lower() == 'y':
            print("\nINITIAL DRAFT:")
            print("-" * 40)
            print(result.get('draft', 'No initial draft generated'))
            print("-" * 40)
            
            print("\nFINAL EDITED DRAFT:")
            print("-" * 40)
            print(result.get('final_draft', 'No final draft generated'))
            print("-" * 40)
            
            print("\nSLACK MESSAGE:")
            print("-" * 40)
            print(result.get('slack_message', 'No Slack message generated'))
            
        return result
        
    except Exception as e:
        print(f"Error running agent pipeline: {str(e)}")
        raise

def main():
    """
    Main function to run the test with user input or example data.
    """
    use_example = input("Use example email? (y/n): ").lower() == 'y'
    
    if use_example:
        # Example email data
        email_text = """
        "Hi Aidrian,

        Heard great things on Tom Elliot. But the podcast is about CI/CD pipelines, I'm not sure if he fits.

        Best,
        Grant
        """
        
        subject = "Re: Great episode on digital transformation"
        sender_name = "Grant Bliphless"
        sender_email = "Assistant@thegrantedgrantpodcast.com"
    else:
        # Get user input
        print("\nEnter the email details:")
        email_text = input("Email content (press Enter twice when done):\n")
        
        # Allow multiline input for email content
        line = input()
        while line:
            email_text += "\n" + line
            line = input()
            
        subject = input("Subject line: ")
        sender_name = input("Sender name: ")
        sender_email = input("Sender email: ")
    
    # Run the pipeline
    test_agent_pipeline(email_text, subject, sender_name, sender_email)

if __name__ == "__main__":
    main()
