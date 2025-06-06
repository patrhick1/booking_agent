from fastapi import FastAPI, HTTPException, Request
import uvicorn
import json
import os
import sys
from typing import Dict, Any
from pydantic import BaseModel

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the agent from main.py
from src.main import graph
# Import the v2 agent for testing
from src.main_v2 import graph as graph_v2

app = FastAPI(title="Booking Assistant API")

# Define request and response models
class StartAgentRequest(BaseModel):
    email: str
    subject: str = ""
    sender_name: str = ""
    sender_email: str = ""

class EmailPayload(BaseModel):
    content: dict

class ApiResponse(BaseModel):
    status: str
    message: str

@app.post("/start_agent", response_model=ApiResponse)
async def start_agent(request: StartAgentRequest):
    """
    Endpoint to start the agent processing pipeline

    Input:
    - email: string containing the email text to process
    - subject: email subject line
    - sender_name: name of the sender
    - sender_email: email address of the sender

    Output:
    - JSON response with status of the operation
    """
    try:
        if not request.email:
            raise HTTPException(status_code=400, detail="Email text is required")

        # Initialize state with email text and metadata
        state = {
            "email_text": request.email,
            "subject": request.subject,
            "sender_name": request.sender_name,
            "sender_email": request.sender_email
        }

        # Generate a unique thread ID for each request
        import uuid
        thread_id = str(uuid.uuid4())

        # Create the properly structured thread object for newer langgraph versions
        thread = {"configurable": {"thread_id": thread_id}}

        # Invoke the agent graph with the proper parameters
        result = graph.invoke(state, thread)

        return {"status": "success", "message": "Agent process completed"}

    except Exception as e:
        print(f"Error in start_agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/start_agent_v2", response_model=ApiResponse)
async def start_agent_v2(request: StartAgentRequest):
    """
    Endpoint to start the v2 agent processing pipeline

    Input:
    - email: string containing the email text to process
    - subject: email subject line
    - sender_name: name of the sender
    - sender_email: email address of the sender

    Output:
    - JSON response with status of the operation
    """
    try:
        if not request.email:
            raise HTTPException(status_code=400, detail="Email text is required")

        # Initialize state with email text and metadata
        state = {
            "email_text": request.email,
            "subject": request.subject,
            "sender_name": request.sender_name,
            "sender_email": request.sender_email
        }

        # Generate a unique thread ID for each request
        import uuid
        thread_id = str(uuid.uuid4())

        # Create the properly structured thread object for newer langgraph versions
        thread = {"configurable": {"thread_id": thread_id}}

        # Invoke the v2 agent graph with the proper parameters
        result = graph_v2.invoke(state, thread)

        return {"status": "success", "message": "Agent v2 process completed"}

    except Exception as e:
        print(f"Error in start_agent_v2: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/slack_webhook", response_model=ApiResponse)
async def slack_webhook(request: Request):
    """
    Endpoint to handle all Slack interactive webhooks
    This acts as a funnel for different button actions from Slack messages

    Input:
    - Raw request from Slack interactive components

    Output:
    - JSON response with status of the operation
    """
    try:
        # Get the raw payload from Slack
        form_data = await request.form()

        # The payload comes as a string in the "payload" field
        if "payload" in form_data:
            payload_str = form_data["payload"]
            payload = json.loads(payload_str)

            # Print the full payload for debugging
            print("Received Slack webhook payload:")
            print(json.dumps(payload, indent=2))

            # Check for actions in the payload
            if "actions" in payload and len(payload["actions"]) > 0:
                action_id = payload["actions"][0].get("action_id", "unknown")
                print(f"Action ID: {action_id}")

                # Import the handlers
                from slack_interactivity import (
                    handle_send_out_reply,
                    handle_attio_campaign,
                    handle_gdrive_client
                )

                # Route to the appropriate handler based on action_id
                if action_id == "send-out-reply":
                    result = handle_send_out_reply(payload)
                    return result
                elif action_id == "attio-campaign":
                    result = handle_attio_campaign(payload)
                    return result
                elif action_id == "gdrive-client":
                    result = handle_gdrive_client(payload)
                    return result
                else:
                    return {"status": "error", "message": f"Unknown action ID: {action_id}"}

            return {"status": "success", "message": "Slack webhook received"}
        else:
            print("No payload found in the request")
            return {"status": "error", "message": "No payload found"}

    except Exception as e:
        print(f"Error in slack_webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Simple health check endpoint"""
    return {"status": "Bookwriting Agent is ready"}

def start_server(host="0.0.0.0", port=5000):
    """Start the FastAPI server"""
    uvicorn.run(app, host=host, port=port)