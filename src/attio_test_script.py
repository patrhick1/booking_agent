
#!/usr/bin/env python3
"""
Test script for Attio API methods.
This script tests various operations of the AttioClient class.
"""

import os
import json
from attio_service import AttioClient

def print_response(title, response):
    """Pretty print API response"""
    print(f"\n==== {title} ====")
    if isinstance(response, dict):
        print(json.dumps(response, indent=2)[:500] + "..." if len(json.dumps(response)) > 500 else json.dumps(response, indent=2))
    else:
        print(response)
    print("=" * (len(title) + 10))

def test_list_records():
    """Test listing records from Attio"""
    print("\nTesting list_records()...")
    attio = AttioClient()
    
    # Test with podcast object
    response = attio.list_records("podcast", page=1, limit=3)
    print_response("List Podcast Records (First 3)", response)
    
    # Test with people object
    response = attio.list_records("people", page=1, limit=3)
    print_response("List People Records (First 3)", response)

def test_filter_records():
    """Test filtering records by attribute"""
    print("\nTesting filter_records()...")
    attio = AttioClient()
    
    # Test podcast filter
    print("Filtering podcasts by name...")
    response = attio.filter_records("podcast", "podcast_name", "The Libertarian Christian Podcast")
    print_response("Filter Podcast by Name", response)
    
    # Test people filter
    print("Filtering people by name...")
    # Replace with an actual name that exists in your Attio database
    response = attio.filter_records("people", "name", "John Doe") 
    print_response("Filter People by Name", response)

def test_get_record():
    """Test getting a specific record"""
    print("\nTesting get_record()...")
    attio = AttioClient()
    
    # First get a record ID through listing
    list_response = attio.list_records("podcast", page=1, limit=1)
    if list_response and "data" in list_response and "records" in list_response["data"] and list_response["data"]["records"]:
        record_id = list_response["data"]["records"][0]["id"]
        print(f"Found record ID: {record_id}")
        
        # Now get the specific record
        response = attio.get_record("podcast", record_id)
        print_response(f"Get Podcast Record ({record_id})", response)
    else:
        print("No records found to test get_record()")

def test_create_record():
    """Test creating a new record"""
    print("\nTesting create_record()...")
    attio = AttioClient()
    
    # Create a test podcast record
    attributes = {
        "podcast_name": "Test Automation Podcast",
        "host_name": "Test Host",
        "category": "Technology"
    }
    
    response = attio.create_record("podcast", attributes)
    print_response("Create Podcast Record", response)
    
    # Return the ID for use in update and delete tests
    if response and "data" in response and "record" in response["data"]:
        return response["data"]["record"]["id"]
    return None

def test_update_record(record_id):
    """Test updating a record"""
    if not record_id:
        print("\nSkipping update_record test: No record ID available")
        return
    
    print(f"\nTesting update_record() for record {record_id}...")
    attio = AttioClient()
    
    # Update the test record
    update_attributes = {
        "host_name": "Updated Test Host",
        "category": "Programming"
    }
    
    response = attio.update_record("podcast", record_id, update_attributes)
    print_response(f"Update Podcast Record ({record_id})", response)

def test_delete_record(record_id):
    """Test deleting a record"""
    if not record_id:
        print("\nSkipping delete_record test: No record ID available")
        return
    
    print(f"\nTesting delete_record() for record {record_id}...")
    attio = AttioClient()
    
    # Delete the test record
    response = attio.delete_record("podcast", record_id)
    print_response(f"Delete Podcast Record ({record_id})", response)

def run_all_tests():
    """Run all the test functions"""
    print("Starting Attio API tests...")
    print(f"Using API key: {'*' * (len(os.getenv('ATTIO_ACCESS_TOKEN', '')) - 4)}{os.getenv('ATTIO_ACCESS_TOKEN', '')[-4:] if os.getenv('ATTIO_ACCESS_TOKEN') else 'NOT FOUND'}")
    
    # Test query functions
    test_list_records()
    test_filter_records()
    test_get_record()
    
    # Test create-update-delete cycle
    created_record_id = test_create_record()
    test_update_record(created_record_id)
    test_delete_record(created_record_id)
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    run_all_tests()
