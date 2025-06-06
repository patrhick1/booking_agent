
#!/usr/bin/env python3
"""Test script for the send_interactive_message function."""

import sys
sys.path.append('src')  # Add src directory to path

from utils import send_interactive_message

def main():
    # Example message and draft
    message = """New response received from James Baca, host of a faith-based podcast.

This email is in response to our message asking if he'd like to feature Erick Vargas on his show.

He apologizes for the slow reply, says he's very interested in discussing this further, and asks if you're available for a call.

Do check the email for more information. I've drafted a reply to help you get started.

Classification: Accepted"""

    draft = """Dear James,

Thank you for your response and interest in featuring Erick Vargas on your podcast! I appreciate your enthusiasm despite the delayed reply.

Erick would be delighted to schedule a call to discuss the potential collaboration further. Please let me know what times work best for you in the coming week, and we can arrange a convenient time to connect.

Looking forward to exploring this opportunity with you!

Best regards,
[Your Signature]"""

    # Example sender email and subject line
    sender_email = "james@3rdbrain.co"
    subject_line = "Re: Podcast Guest Opportunity - Erick Vargas"
    
    # Example URLs for Attio and Google Drive
    attio_url = "https://www.google.com/"
    gdrive_url = "https://www.wikipedia.org/"
    
    # Send the interactive message
    status_code = send_interactive_message(message, draft, sender_email, subject_line, attio_url, gdrive_url)
    
    # Print the result
    print(f"Message sent with status code: {status_code}")
    if status_code == 200:
        print("✅ Successfully sent interactive message to Slack!")
    else:
        print("❌ Failed to send interactive message to Slack.")

if __name__ == "__main__":
    main()
