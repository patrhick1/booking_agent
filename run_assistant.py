# run_assistant.py

import time
import os
import sys
from dotenv import load_dotenv

# Add src to path and load environment variables
sys.path.append('src')
load_dotenv()

from src.email_service import EmailService
from src.main import graph

def process_email(email_details: dict):
    """Invokes the LangGraph pipeline for a single email."""
    print("\n" + "="*50)
    print(f"--- Processing new email from: {email_details['sender_email']} ---")
    print(f"Subject: {email_details['subject']}")
    print("="*50)

    # The 'body' from the service already contains the combined subject and content
    state = {
        "email_text": email_details["body"],
        "subject": email_details["subject"],
        "sender_name": email_details["sender_name"],
        "sender_email": email_details["sender_email"]
    }

    import uuid
    thread_id = str(uuid.uuid4())
    thread = {"configurable": {"thread_id": thread_id}}

    try:
        result = graph.invoke(state, thread)
        print(f"--- Finished processing email from: {email_details['sender_email']} ---")
        print(f"Final Draft Status: {result.get('draft_status', 'N/A')}")
    except Exception as e:
        print(f"ERROR processing email from {email_details['sender_email']}: {e}")
        import traceback
        traceback.print_exc()

def main_loop():
    """Main loop to poll for new emails and process them."""
    email_service = EmailService()
    polling_interval = 60  # seconds

    print("🚀 Starting Booking & Reply Assistant...")
    
    while True:
        try:
            print(f"\n>>> Checking for new emails... (Next check in {polling_interval}s)")
            
            # Fetch from both sources
            gmail_emails = email_service.fetch_unread_gmail_emails()
            maildoso_emails = email_service.fetch_unread_maildoso_emails()
            
            all_new_emails = gmail_emails + maildoso_emails
            
            if not all_new_emails:
                print("No new emails found.")
            else:
                print(f"Found {len(all_new_emails)} new email(s) to process.")
                for email_details in all_new_emails:
                    process_email(email_details)
            
            time.sleep(polling_interval)
        
        except KeyboardInterrupt:
            print("\n👋 Shutting down assistant.")
            break
        except Exception as e:
            print(f"An unexpected error occurred in the main loop: {e}")
            print("Restarting loop in 60 seconds...")
            time.sleep(60)

if __name__ == "__main__":
    main_loop()