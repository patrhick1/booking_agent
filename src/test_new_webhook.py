
#!/usr/bin/env python3
"""
Test script to directly send a request to the specified webhook URL
and receive the response.
"""

import requests
import json

def test_webhook():
    """
    Test the webhook by sending a request and displaying the response.
    """
    webhook_url = "https://hook.us1.make.com/xp8erjpxc28hosrpvg95pff55w6igpjh"
    
    try:
        # Make the POST request to the webhook with no payload
        print(f"Sending request to webhook: {webhook_url}")
        response = requests.post(webhook_url)
        
        # Print the response details
        print(f"Status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.text:
            try:
                # Try to parse as JSON if possible
                json_response = response.json()
                print(f"Response payload (JSON):\n{json.dumps(json_response, indent=2)}")
            except json.JSONDecodeError:
                # If not JSON, print as text
                print(f"Response payload (text):\n{response.text}")
        else:
            print("No response payload received.")
        
        # Check if the request was successful
        if response.status_code == 200:
            print("✅ Webhook test successful!")
        else:
            print(f"❌ Webhook test failed with status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error during webhook test: {str(e)}")

if __name__ == "__main__":
    print("Starting webhook test...")
    test_webhook()
    print("Webhook test completed.")
