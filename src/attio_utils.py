
import requests
import os

# Get token from environment variable
token = os.getenv("ATTIO_ACCESS_TOKEN")
if not token:
    print("Error: ATTIO_ACCESS_TOKEN environment variable not set")
    exit(1)

# Attio workspace and object IDs
workspace_id = "bc634419-c6bf-4bfe-a42b-fb0b5e102d1c"
companies_object_id = "3b0cf7e4-9a0c-4cca-b564-0beb54de5b2f"
podcast_object_id = "3e652150-fc63-4df9-a8e5-2cf0dcfb480f"
people_object_id = "a72118b4-7eed-459b-972b-1ec303db34ab"

url = "https://api.attio.com/v2/objects"

headers = {"Authorization": f"Bearer {token}"}

response = requests.request("GET", url, headers=headers)

print(response.text)