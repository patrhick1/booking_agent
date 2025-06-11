#!/usr/bin/env python3
"""
Complete functionality test for the Booking Assistant.
Tests the entire pipeline without sending to Slack or creating Gmail drafts.
"""

import sys
import os
import json
import uuid
from typing import Dict, Any

# Add src to path for imports
sys.path.append('src')

from dotenv import load_dotenv
load_dotenv()

# Import the main graph and services
from src.main import graph
from src.email_service import EmailService

def test_email_classification():
    """Test various email classification scenarios."""
    print("\n" + "="*60)
    print("TESTING EMAIL CLASSIFICATION")
    print("="*60)
    
    test_emails = [
        {
            "name": "Conditional Acceptance",
            "email": """
            Subject: Re: Podcast Guest - Erick Vargas

            Hi Adrian,
            
            Thanks for reaching out about Erick Vargas from Followup CRM. He sounds interesting, but I'd like to know more about his background in CRM automation before we proceed. Could you send his bio and some previous interviews?
            
            Also, what specific topics would he want to discuss on our show?
            
            Best,
            Mike Peterson
            The Tech Talk Podcast
            """,
            "sender_email": "mike@techtalk.com",
            "sender_name": "Mike Peterson"
        },
        {
            "name": "Hard Rejection",
            "email": """
            Subject: Re: Guest Pitch
            
            Hi there,
            
            Thank you for reaching out, but we don't accept guest pitches or external guests on our show. We only feature internal team members.
            
            Best of luck elsewhere!
            """,
            "sender_email": "noreply@internalonly.com", 
            "sender_name": "Admin"
        },
        {
            "name": "Pay-to-Play",
            "email": """
            Subject: Re: Podcast Appearance
            
            Hello,
            
            We'd be happy to feature your client, but we only offer paid sponsorship slots. Our rate is $500 for a 30-minute interview.
            
            Let me know if you're interested in this option.
            
            Thanks,
            Jennifer
            """,
            "sender_email": "jennifer@paidpodcast.com",
            "sender_name": "Jennifer Smith"
        },
        {
            "name": "Topic-based Rejection",
            "email": """
            Subject: Re: Podcast Guest Proposal
            
            Hi Adrian,
            
            Thanks for the pitch about John's marketing expertise. Unfortunately, we only focus on cybersecurity topics on our show, so John wouldn't be a good fit.
            
            Feel free to reach out if you have any cybersecurity experts!
            
            Best,
            Alex
            """,
            "sender_email": "alex@cybersecuritypod.com",
            "sender_name": "Alex Rodriguez"
        },
        {
            "name": "Accepted",
            "email": """
            Subject: Re: Guest Opportunity - Ashwin Ramesh
            
            Hi,
            
            Ashwin Ramesh from Synup sounds like a perfect fit for our entrepreneurship show! I'd love to have him on. 
            
            When is he available for recording? We typically record on Tuesday and Thursday afternoons.
            
            Looking forward to it!
            
            Best,
            David
            """,
            "sender_email": "david@entrepreneurpod.com",
            "sender_name": "David Chen"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_emails, 1):
        print(f"\n--- Test Case {i}: {test_case['name']} ---")
        
        state = {
            "email_text": test_case["email"],
            "subject": f"Re: Podcast Guest Test {i}",
            "sender_name": test_case["sender_name"],
            "sender_email": test_case["sender_email"]
        }
        
        thread_id = str(uuid.uuid4())
        thread = {"configurable": {"thread_id": thread_id}}
        
        try:
            result = graph.invoke(state, thread)
            
            print(f"✅ Classification: {result.get('label', 'N/A')}")
            print(f"📧 Draft Status: {result.get('draft_status', 'N/A')}")
            print(f"📝 Final Draft Length: {len(result.get('final_draft', ''))}")
            if result.get('rejection_type'):
                print(f"🚫 Rejection Type: {result['rejection_type']}")
            if result.get('document_extraction_status'):
                print(f"📁 Document Status: {result['document_extraction_status']}")
            
            results.append({
                "test_case": test_case['name'],
                "classification": result.get('label'),
                "success": True,
                "has_draft": bool(result.get('final_draft')),
                "rejection_type": result.get('rejection_type'),
                "doc_status": result.get('document_extraction_status')
            })
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append({
                "test_case": test_case['name'],
                "classification": None,
                "success": False,
                "error": str(e)
            })
    
    return results

def test_email_fetching():
    """Test email fetching from both Gmail and Maildoso (dry run)."""
    print("\n" + "="*60)
    print("TESTING EMAIL FETCHING SERVICES")
    print("="*60)
    
    email_service = EmailService()
    
    # Test Gmail service initialization
    try:
        print("📧 Testing Gmail service...")
        gmail_service = email_service.gmail_service
        if gmail_service:
            print("✅ Gmail service initialized successfully")
        else:
            print("❌ Gmail service failed to initialize")
    except Exception as e:
        print(f"❌ Gmail service error: {e}")
    
    # Test spam filtering logic
    print("\n📋 Testing spam filter logic...")
    test_cases = [
        ("Normal email", "Hello, interested in guest", "user@example.com", True),
        ("Spam keyword", "delivery status notification failed", "user@example.com", False),
        ("Ignored sender", "Hello there", "aidrian@podcastguestlaunch.com", False),
        ("Another spam", "whale-floor content here", "user@example.com", False),
    ]
    
    for description, body, sender, expected in test_cases:
        result = email_service._should_process_email("Test Subject", body, sender)
        status = "✅" if result == expected else "❌"
        print(f"{status} {description}: Expected {expected}, Got {result}")
    
    # Test text cleaning
    print("\n🧹 Testing text cleaning...")
    dirty_text = "Hello\t\tworld\r\nwith\tstrange   spacing"
    clean_text = email_service._clean_text(dirty_text)
    print(f"Original: '{dirty_text}'")
    print(f"Cleaned:  '{clean_text}'")

def test_vector_database():
    """Test vector database connectivity and search."""
    print("\n" + "="*60)  
    print("TESTING VECTOR DATABASE")
    print("="*60)
    
    try:
        from src.astradb_services import AstraDBService
        astra_service = AstraDBService()
        
        print("✅ AstraDB service initialized")
        
        # Test vector search
        test_query = "podcast host accepted our guest booking request"
        print(f"🔍 Testing search with query: '{test_query}'")
        
        results = astra_service.fetch_threads(test_query, top_k=3)
        print(f"📊 Found {len(results)} relevant threads")
        
        for i, thread in enumerate(results[:2], 1):  # Show first 2
            print(f"   Thread {i}: {thread[:100]}...")
            
    except Exception as e:
        print(f"❌ AstraDB test failed: {e}")

def test_google_drive_integration():
    """Test Google Drive document extraction."""
    print("\n" + "="*60)
    print("TESTING GOOGLE DRIVE INTEGRATION") 
    print("="*60)
    
    try:
        from src.google_docs_service import GoogleDocsService
        google_service = GoogleDocsService()
        
        print("✅ Google Docs service initialized")
        
        # Test folder listing (if root folder ID is available)
        root_folder_id = os.getenv("GDRIVE_CLIENT_ROOT_FOLDER_ID")
        if root_folder_id:
            print(f"📁 Testing folder listing for root: {root_folder_id}")
            files = google_service.get_files_in_folder(root_folder_id)
            print(f"📊 Found {len(files)} items in root folder")
            
            # Show first few folders
            folders = [f for f in files if 'folder' in f.get('mimeType', '')]
            print(f"📂 Client folders found: {len(folders)}")
            for folder in folders[:3]:  # Show first 3
                print(f"   - {folder.get('name')}")
        else:
            print("⚠️  GDRIVE_CLIENT_ROOT_FOLDER_ID not set, skipping folder test")
            
    except Exception as e:
        print(f"❌ Google Drive test failed: {e}")

def test_environment_variables():
    """Check if all required environment variables are set."""
    print("\n" + "="*60)
    print("TESTING ENVIRONMENT CONFIGURATION")
    print("="*60)
    
    required_vars = [
        "OPENAI_API_KEY",
        "ASTRA_DB_TOKEN", 
        "ASTRA_DB_ENDPOINT",
        "SLACK_WEBHOOK_URL",
        "GDRIVE_CLIENT_ROOT_FOLDER_ID",
        "GMAIL_TARGET_EMAIL"
    ]
    
    optional_vars = [
        "MAILODOSO_IMAP_HOST",
        "MAILODOSO_IMAP_PORT", 
        "MAILODOSO_USER",
        "MAILODOSO_PASSWORD",
        "GOOGLE_APPLICATION_CREDENTIALS"
    ]
    
    print("📋 Required Environment Variables:")
    for var in required_vars:
        value = os.getenv(var)
        status = "✅" if value else "❌"
        masked_value = "***SET***" if value else "NOT SET"
        print(f"   {status} {var}: {masked_value}")
    
    print("\n📋 Optional Environment Variables:")
    for var in optional_vars:
        value = os.getenv(var)
        status = "✅" if value else "⚠️ "
        masked_value = "***SET***" if value else "NOT SET"
        print(f"   {status} {var}: {masked_value}")

def print_summary(classification_results):
    """Print a summary of all test results."""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    print("\n📊 Classification Test Results:")
    successful_tests = sum(1 for r in classification_results if r['success'])
    total_tests = len(classification_results)
    
    print(f"✅ Successful: {successful_tests}/{total_tests}")
    
    if successful_tests < total_tests:
        print("❌ Failed tests:")
        for result in classification_results:
            if not result['success']:
                print(f"   - {result['test_case']}: {result.get('error', 'Unknown error')}")
    
    print(f"\n📝 Draft Generation:")
    drafts_created = sum(1 for r in classification_results if r.get('has_draft'))
    print(f"   Drafts created: {drafts_created}/{successful_tests}")
    
    print(f"\n🏷️  Classifications Found:")
    classifications = {}
    for result in classification_results:
        if result.get('classification'):
            label = result['classification']
            classifications[label] = classifications.get(label, 0) + 1
    
    for label, count in classifications.items():
        print(f"   - {label}: {count}")
    
    print("\n🎯 Next Steps:")
    print("   1. Review any failed tests above")
    print("   2. Enable Gmail API in Google Cloud Console if needed:")
    print("      https://console.developers.google.com/apis/api/gmail.googleapis.com/overview?project=176736895476")
    print("   3. Check environment variables if services failed")
    print("   4. Test with real emails using run_assistant.py")
    print("   5. Monitor Slack notifications (currently disabled for testing)")

def main():
    """Run all tests."""
    print("🚀 BOOKING ASSISTANT - COMPLETE FUNCTIONALITY TEST")
    print("This test validates the entire pipeline without sending emails or Slack messages.")
    
    # Set testing mode to skip Gmail draft creation
    os.environ["TESTING_MODE"] = "true"
    
    # Test environment setup
    test_environment_variables()
    
    # Test individual services  
    test_email_fetching()
    test_vector_database()
    test_google_drive_integration()
    
    # Test end-to-end pipeline
    classification_results = test_email_classification()
    
    # Print summary
    print_summary(classification_results)
    
    print(f"\n✨ Testing complete! Check the results above.")

if __name__ == "__main__":
    main()