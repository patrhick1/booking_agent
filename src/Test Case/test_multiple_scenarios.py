#!/usr/bin/env python3
"""
Automated test script to run the booking agent pipeline with multiple sample emails.
This script tests various email scenarios in sequence to validate different pipeline paths.
"""

import sys
import os
import json
import time
from datetime import datetime

# Add the project root directory to the path so we can import our modules
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# Import the agent from main.py and test data
from src.main import graph
from test_data import SAMPLE_EMAILS

def run_single_test(test_data, test_number, total_tests):
    """
    Run the agent pipeline with a single test case.

    Args:
        test_data (dict): Email test data containing email_text, subject, sender_name, sender_email
        test_number (int): Current test number
        total_tests (int): Total number of tests

    Returns:
        dict: The final state after pipeline completion
    """
    print("\n" + "="*80)
    print(f"TEST {test_number}/{total_tests}: {test_data['name']}")
    print(f"Sender: {test_data['sender_name']} <{test_data['sender_email']}>")
    print(f"Subject: {test_data['subject']}")
    print("="*80)

    # Initialize state with email text and metadata
    state = {
        "email_text": test_data["email_text"],
        "subject": test_data["subject"],
        "sender_name": test_data["sender_name"],
        "sender_email": test_data["sender_email"]
    }

    # Generate a unique thread ID for each request
    import uuid
    thread_id = str(uuid.uuid4())

    # Create the properly structured thread object for langgraph
    thread = {"configurable": {"thread_id": thread_id}}

    try:
        start_time = time.time()

        # Invoke the agent graph with the proper parameters
        result = graph.invoke(state, thread)

        end_time = time.time()
        processing_time = round(end_time - start_time, 2)

        # Print results summary
        print(f"\n✅ TEST {test_number} COMPLETED in {processing_time}s")
        print(f"Classification: {result.get('label', 'N/A')}")

        if 'rejection_type' in result and result['rejection_type']:
            print(f"Rejection Type: {result.get('rejection_type', 'N/A')}")

        print(f"Final Draft Generated: {'Yes' if result.get('final_draft') else 'No'}")
        print(f"Slack Notification: {'Sent' if result.get('notification_status') else 'Not sent'}")
        print(f"Webhook Status: {'Success' if 'Successfully' in result.get('webhook_status', '') else 'Failed'}")

        if result.get('gdrive_url'):
            print(f"Google Drive: Found")

        # Store summary for final report
        test_summary = {
            "test_name": test_data['name'],
            "classification": result.get('label', 'N/A'),
            "rejection_type": result.get('rejection_type', ''),
            "draft_generated": bool(result.get('final_draft')),
            "slack_sent": bool(result.get('notification_status')),
            "webhook_success": 'Successfully' in result.get('webhook_status', ''),
            "processing_time": processing_time,
            "gdrive_found": bool(result.get('gdrive_url'))
        }

        return test_summary, result

    except Exception as e:
        print(f"❌ TEST {test_number} FAILED: {str(e)}")
        return {
            "test_name": test_data['name'],
            "error": str(e),
            "processing_time": 0
        }, None

def run_all_tests():
    """
    Run all test scenarios and provide a comprehensive report.
    """
    print("🚀 Starting comprehensive pipeline testing...")
    print(f"📊 Running {len(SAMPLE_EMAILS)} test scenarios")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    all_results = []
    successful_tests = 0
    failed_tests = 0

    for i, test_data in enumerate(SAMPLE_EMAILS, 1):
        test_summary, full_result = run_single_test(test_data, i, len(SAMPLE_EMAILS))
        all_results.append(test_summary)

        if "error" in test_summary:
            failed_tests += 1
        else:
            successful_tests += 1

        # Small delay between tests to avoid overwhelming the system
        if i < len(SAMPLE_EMAILS):
            print("⏳ Waiting 2 seconds before next test...")
            time.sleep(2)

    # Generate final comprehensive report
    print("\n" + "="*80)
    print("📋 COMPREHENSIVE TEST REPORT")
    print("="*80)
    print(f"Total Tests: {len(SAMPLE_EMAILS)}")
    print(f"✅ Successful: {successful_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"📈 Success Rate: {(successful_tests/len(SAMPLE_EMAILS)*100):.1f}%")

    # Classification breakdown
    classifications = {}
    rejection_types = {}

    for result in all_results:
        if "error" not in result:
            # Count classifications
            classification = result.get('classification', 'Unknown')
            classifications[classification] = classifications.get(classification, 0) + 1

            # Count rejection types
            rejection_type = result.get('rejection_type', '')
            if rejection_type:
                rejection_types[rejection_type] = rejection_types.get(rejection_type, 0) + 1

    print(f"\n📊 Classification Breakdown:")
    for classification, count in classifications.items():
        print(f"  • {classification}: {count}")

    if rejection_types:
        print(f"\n🚫 Rejection Type Breakdown:")
        for rejection_type, count in rejection_types.items():
            print(f"  • {rejection_type}: {count}")

    # Performance metrics
    processing_times = [r.get('processing_time', 0) for r in all_results if 'error' not in r]
    if processing_times:
        avg_time = sum(processing_times) / len(processing_times)
        max_time = max(processing_times)
        min_time = min(processing_times)

        print(f"\n⚡ Performance Metrics:")
        print(f"  • Average processing time: {avg_time:.2f}s")
        print(f"  • Fastest test: {min_time:.2f}s")
        print(f"  • Slowest test: {max_time:.2f}s")

    # Feature usage stats
    drafts_generated = sum(1 for r in all_results if r.get('draft_generated'))
    slack_sent = sum(1 for r in all_results if r.get('slack_sent'))
    webhooks_success = sum(1 for r in all_results if r.get('webhook_success'))
    gdrive_found = sum(1 for r in all_results if r.get('gdrive_found'))

    print(f"\n🔧 Feature Usage:")
    print(f"  • Drafts generated: {drafts_generated}/{successful_tests}")
    print(f"  • Slack notifications: {slack_sent}/{successful_tests}")
    print(f"  • Successful webhooks: {webhooks_success}/{successful_tests}")
    print(f"  • Google Drive docs found: {gdrive_found}/{successful_tests}")

    # Detailed results table
    print(f"\n📋 Detailed Results:")
    print("-" * 80)
    print(f"{'Test Name':<30} {'Classification':<20} {'Final Draft':<11} {'Time':<6}")
    print("-" * 80)

    for result in all_results:
        if "error" in result:
            print(f"{result['test_name']:<30} {'ERROR':<20} {'No':<11} {'0.00s':<6}")
        else:
            name = result['test_name'][:29] if len(result['test_name']) > 29 else result['test_name']
            classification = result['classification'][:19] if len(result['classification']) > 19 else result['classification']
            draft = 'Yes' if result['draft_generated'] else 'No'
            time_str = f"{result['processing_time']:.2f}s"
            print(f"{name:<30} {classification:<20} {draft:<11} {time_str:<6}")

    print("\n✨ Testing completed!")
    print(f"⏰ Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return all_results

def run_interactive_mode():
    """
    Interactive mode to select and run specific tests.
    """
    print("🎛️  Interactive Testing Mode")
    print("Available test scenarios:")

    for i, test_data in enumerate(SAMPLE_EMAILS, 1):
        print(f"  {i}. {test_data['name']}")

    while True:
        try:
            choice = input(f"\nSelect test number (1-{len(SAMPLE_EMAILS)}) or 'all' or 'quit': ").strip().lower()

            if choice == 'quit':
                break
            elif choice == 'all':
                run_all_tests()
                break
            else:
                test_num = int(choice)
                if 1 <= test_num <= len(SAMPLE_EMAILS):
                    test_data = SAMPLE_EMAILS[test_num - 1]
                    run_single_test(test_data, test_num, len(SAMPLE_EMAILS))
                else:
                    print("❌ Invalid test number!")
        except ValueError:
            print("❌ Please enter a valid number, 'all', or 'quit'")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break

def main():
    """
    Main function to choose between running all tests or interactive mode.
    """
    print("🤖 Booking Agent Pipeline - Multi-Scenario Tester")
    print("=" * 50)

    mode = input("Choose mode:\n1. Run all tests automatically\n2. Interactive mode\nEnter choice (1 or 2): ").strip()

    if mode == "1":
        run_all_tests()
    elif mode == "2":
        run_interactive_mode()
    else:
        print("Invalid choice. Running all tests by default...")
        run_all_tests()

if __name__ == "__main__":
    main()