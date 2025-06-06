
import requests
import json

def test_webhook():
    """
    Test script to directly send sample data to the webhook URL
    to verify the webhook integration with Make.com
    """
    webhook_url = "https://hook.us1.make.com/vaggalj5a1oe5llfeolhxvbjwfc705uf"
    
    # Sample test data
    test_payload = {
        "draft": "Dear John,\n\nThank you for considering our podcast guest. We would be delighted to participate in your show.\n\nLooking forward to hearing from you.\n\nBest regards,\nAidrian",
        "subject": "Re: Podcast Guest Invitation - Test Email",
        "sender_email": "guest@example.com"
    }
    
    try:
        # Make the POST request to the webhook
        response = requests.post(webhook_url, json=test_payload)
        
        # Print the response details
        print(f"Status code: {response.status_code}")
        if response.text:
            try:
                print(f"Response: {json.dumps(response.json(), indent=2)}")
            except:
                print(f"Response text: {response.text}")
        
        # Check if the request was successful
        if response.status_code == 200:
            print("✅ Webhook test successful! Data was sent to Make.com.")
        else:
            print(f"❌ Webhook test failed with status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error during webhook test: {str(e)}")

if __name__ == "__main__":
    print("Starting webhook test...")
    test_webhook()
    print("Webhook test completed.")
