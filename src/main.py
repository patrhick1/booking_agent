import os
from astradb_services import AstraDBService

import argparse
import requests
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from typing import TypedDict, List, Literal, Dict, Any
from langgraph.prebuilt import ToolNode, tools_condition

from astradb_services import AstraDBService
from astrapy import DataAPIClient
from prompts import (
    classification_fewshot,
    draft_generation_prompt,
    slack_notification_prompt,
    query_for_relevant_email_prompt,
    rejection_strategy_prompt,
    soft_rejection_drafting_prompt,
    client_gdrive_extract_prompt,
)
from utils import send_message, send_interactive_message

# Load environment and initialize model, memory, and services
load_dotenv()

from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()

model = ChatOpenAI(model="o4-mini-2025-04-16", temperature=1)
astra_service = AstraDBService()


# Define the state shape for the graph
class AgentState(TypedDict):
    email_text: str
    subject: str
    sender_name: str
    sender_email: str
    label: str
    vector_query: str
    relevant_threads: List[str]
    draft: str
    slack_message: str
    notification_status: str
    rejection_type: str
    challenge_angles: List[str]
    webhook_status: str
    attio_url: str
    gdrive_url: str
    client_folder_id: str
    relevant_document_content: str
    document_extraction_status: str


# Graph node implementations
def classify_node(state: AgentState) -> dict:
    print("Currently in: classify_node")
    messages = [
        SystemMessage(content=classification_fewshot),
        HumanMessage(content=state["email_text"]),
    ]
    response = model.invoke(messages)
    return {"label": response.content.strip()}


def generate_query_node(state: AgentState) -> dict:
    print("Currently in: generate_query_node")
    messages = [
        SystemMessage(content=query_for_relevant_email_prompt),
        HumanMessage(content=state["email_text"]),
    ]
    response = model.invoke(messages)
    return {"vector_query": response.content}


def retrieve_threads_node(state: AgentState) -> dict:
    print("Currently in: retrieve_threads_node")
    threads = astra_service.fetch_threads(state["vector_query"], top_k=5)
    return {"relevant_threads": threads}


def draft_node(state: AgentState) -> dict:
    print("Currently in: draft_node (generate_draft)")
    # Replace the placeholder with actual relevant threads
    prompt_with_examples = draft_generation_prompt.replace("{samplemailshere}", "\n\n".join(state["relevant_threads"]))
    
    # Add client document content if available
    if state.get("relevant_document_content"):
        additional_context = f"\n\nAdditional Client Context from Documents:\n{state['relevant_document_content']}"
        prompt_with_examples += additional_context

    messages = [
        SystemMessage(content=prompt_with_examples),
        HumanMessage(content=state["email_text"]),
    ]
    response = model.invoke(messages)
    print(f"Draft: {response.content}")
    return {"draft": response.content}


def rejection_strategy_node(state: AgentState) -> dict:
    print("Currently in: rejection_strategy_node")
    # Process the email to determine rejection type and potential challenge angles
    prompt = rejection_strategy_prompt.replace("{{email}}", state["email_text"])
    # Note: In a real implementation, you would replace these placeholders with actual data
    prompt = prompt.replace("{{client}}", "Client information would go here")
    prompt = prompt.replace("{{podcast}}", "Podcast information would go here") 
    prompt = prompt.replace("{{host_info}}", "Host information would go here")

    messages = [
        SystemMessage(content=prompt),
    ]

    response = model.invoke(messages)
    response_content = response.content

    # Extract JSON from the response - in a real implementation you'd want more robust parsing
    import json
    # Find JSON part from the response (simple approach)
    try:
        # Look for JSON-like structure at the end of the response
        if "{" in response_content and "}" in response_content:
            json_start = response_content.rfind("{")
            json_end = response_content.rfind("}") + 1
            json_str = response_content[json_start:json_end]
            result = json.loads(json_str)

            rejection_type = result.get("rejection_type", "Hard Rejection")
            challenge_angles = result.get("angles", []) if rejection_type == "Soft Rejection" else []

            return {
                "rejection_type": rejection_type,
                "challenge_angles": challenge_angles
            }
    except Exception as e:
        print(f"Error parsing rejection strategy response: {e}")

    # Default return if parsing fails
    return {
        "rejection_type": "Hard Rejection",
        "challenge_angles": []
    }

def soft_rejection_drafting_node(state: AgentState) -> dict:
    print("Currently in: soft_rejection_drafting_node")
    # Generate a draft response that challenges the rejection
    prompt = soft_rejection_drafting_prompt.replace("{{rejection_scenario}}", state["label"])

    # Add challenge angles to the prompt
    angles = state.get("challenge_angles", [])
    angle_replacements = {
        "{{angle1}}": angles[0] if len(angles) > 0 else "No specific angle available",
        "{{angle2}}": angles[1] if len(angles) > 1 else "No specific angle available",
        "{{angle3}}": angles[2] if len(angles) > 2 else "No specific angle available"
    }

    for placeholder, value in angle_replacements.items():
        prompt = prompt.replace(placeholder, value)

    # Replace email thread placeholder
    prompt = prompt.replace("{{emailthreadhere}}", state["email_text"])
    
    # Add client document content if available
    if state.get("relevant_document_content"):
        additional_context = f"\n\nAdditional Client Context from Documents:\n{state['relevant_document_content'][:2000]}..."  # Limit to first 2000 chars
        prompt += additional_context

    messages = [
        SystemMessage(content=prompt),
    ]

    response = model.invoke(messages)

    # Extract the draft response from between <response> tags (simple approach)
    response_content = response.content
    draft = response_content

    if "<response>" in response_content and "</response>" in response_content:
        start_idx = response_content.find("<response>") + len("<response>")
        end_idx = response_content.find("</response>")
        if start_idx < end_idx:
            draft = response_content[start_idx:end_idx].strip()

    return {"draft": draft}

def slack_notification_node(state: AgentState) -> dict:
    print("Currently in: slack_notification_node")
    messages = [
        SystemMessage(content=slack_notification_prompt),
        HumanMessage(content=state["email_text"]),
    ]
    response = model.invoke(messages)

    # Use the AI-generated notification content for the Slack message
    notification_message = response.content

    # Add classification information to the message
    notification_message += f"\n\nClassification: {state['label']}"

    # Add rejection handling info if applicable
    if "rejection_type" in state and state["rejection_type"]:
        notification_message += f"\nRejection Type: {state['rejection_type']}"
        if state["rejection_type"] == "Soft Rejection" and state.get("challenge_angles"):
            notification_message += "\nChallenge Angles:"
            for angle in state["challenge_angles"]:
                notification_message += f"\n- {angle}"

    # Send the interactive message to Slack with the notification, draft content, sender email, subject, and URLs
    attio_url = state.get("attio_url", "")
    gdrive_url = state.get("gdrive_url", "")

    status_code = send_interactive_message(
        notification_message, 
        state["draft"],
        state["sender_email"],
        state["subject"],
        attio_url,
        gdrive_url
    )

    return {
        "slack_message": response.content,
        "notification_status": f"Interactive Slack notification sent with status: {status_code}"
    }

def client_gdrive_document_extraction_node(state: AgentState) -> dict:
    """
    Extract relevant documents from client's Google Drive folder to provide context for drafting.
    
    Process:
    1. Get list of all client folders using root folder ID
    2. Identify the relevant client folder based on email content
    3. Get documents within that client folder
    4. Identify the most relevant document(s) for the email context
    5. Extract content from the relevant document
    """
    print("Currently in: client_gdrive_document_extraction_node")
    import json
    import re
    
    # Root folder ID that contains all client folders
    root_folder_id = "1ra5I4IpS6gr5rRd-RqFbn9RZCdrOGK31"
    
    # Webhook endpoints
    folder_list_webhook = "https://hook.us1.make.com/gh8mj9ey0x5wxf2abn1mdpilawglx4e9"
    document_content_webhook = "https://hook.us1.make.com/f6ynqm2jk2odhq0vrhexyecwjvcrn6gz"
    
    try:
        print("=== Step 1: Getting list of all client folders ===")
        
        # Call webhook to get all client folders
        response = requests.post(folder_list_webhook, json={"fileID": root_folder_id})
        
        if response.status_code != 200:
            print(f"Failed to get client folders. Status: {response.status_code}")
            return {
                "client_folder_id": "",
                "relevant_document_content": "",
                "document_extraction_status": f"Failed to fetch client folders: {response.status_code}",
                "gdrive_url": ""
            }
        
        client_folders = response.json()
        print(f"Found {len(client_folders)} client folders")
        
        # Format folder data for LLM analysis - filter only folders
        folder_data = []
        for folder in client_folders:
            # Only include items that are actually folders
            if folder.get("mimeType") == "application/vnd.google-apps.folder":
                folder_data.append({
                    "name": folder.get("name", "Unknown"),
                    "id": folder.get("id", ""),
                    "webViewLink": folder.get("webViewLink", "")
                })
        
        print("=== Step 2: Identifying relevant client folder ===")
        
        # Use OpenAI to identify the relevant client folder
        client_identification_prompt = f"""
Based on this email content:
---
{state["email_text"]}
---

Which client folder corresponds to the client we're discussing in the email?

Available client folders:
{json.dumps(folder_data, indent=2)}

Respond in JSON format with the folder ID and link:
{{"folder_id": "client_folder_id_here", "link": "https://drive.google.com/...", "client_name": "identified_client_name"}}

If no client folder matches, respond with:
{{"folder_id": null, "link": null, "client_name": null}}
"""
        
        messages = [
            SystemMessage(content="You are a helpful assistant that identifies clients mentioned in emails and matches them to folder names."),
            HumanMessage(content=client_identification_prompt)
        ]
        
        client_response = model.invoke(messages)
        print(f"Client identification response: {client_response.content}")
        
        # Parse client identification response
        json_match = re.search(r'\{.*?\}', client_response.content, re.DOTALL)
        if not json_match:
            print("No JSON found in client identification response")
            return {
                "client_folder_id": "",
                "relevant_document_content": "",
                "document_extraction_status": "Failed to parse client identification response",
                "gdrive_url": ""
            }
        
        client_data = json.loads(json_match.group(0))
        client_folder_id = client_data.get("folder_id")
        
        if not client_folder_id:
            print("No matching client folder found")
            return {
                "client_folder_id": "",
                "relevant_document_content": "",
                "document_extraction_status": "No matching client folder found",
                "gdrive_url": ""
            }
        
        print(f"Identified client folder: {client_data.get('client_name')} (ID: {client_folder_id})")
        
        print("=== Step 3: Getting documents within client folder ===")
        
        # Get documents within the client folder
        response = requests.post(folder_list_webhook, json={"fileID": client_folder_id})
        
        if response.status_code != 200:
            print(f"Failed to get client documents. Status: {response.status_code}")
            return {
                "client_folder_id": client_folder_id,
                "relevant_document_content": "",
                "document_extraction_status": f"Failed to fetch client documents: {response.status_code}",
                "gdrive_url": client_data.get("link", "")
            }
        
        client_documents = response.json()
        print(f"Found {len(client_documents)} documents in client folder")
        
        # Format document data for LLM analysis - filter only Google Docs
        document_data = []
        for doc in client_documents:
            # Only include items that are actually Google Documents
            if doc.get("mimeType") == "application/vnd.google-apps.document":
                document_data.append({
                    "name": doc.get("name", "Unknown"),
                    "id": doc.get("id", ""),
                    "mimeType": doc.get("mimeType", ""),
                    "webViewLink": doc.get("webViewLink", "")
                })
        
        print("=== Step 4: Identifying most relevant document ===")
        
        # Use OpenAI to identify the most relevant document
        document_selection_prompt = f"""
Based on this email content:
---
{state["email_text"]}
---

Which document from this client's folder would be most helpful for drafting a response to the original email content?

Important: Only choose a document if it solves / answers something that is asked in the email. Your reasoning should completely directly relate to the email content. Define in the reasoning how the chosen document is relevant to the email content (What does it answer? Or what does it provide that is being asked? etc.)

Available documents:
{json.dumps(document_data, indent=2)}

Consider documents that might contain:
- Client background information
- Podcast talking points or angles
- Previous interview topics
- Client expertise areas
- Any information that would help provide context for the email response

Important: Only choose a document if it solves / answers something that is asked in the email. Your reasoning should completely directly relate to the email content. Define in the reasoning how the chosen document is relevant to the email content (What does it answer? Or what does it provide that is being asked? etc.) Also, it's completely fine to choose nothing if nothing is relevant. Do not wildly assume the contents of the documents. 

Note that the Final Briefs of clients typically contain the following and more often than not, are what you'll need to refer to (unless very specific information is requested):
- Client Info (Company Name and Website, Client Name and Personal Website, Titles and Positions, Social Media Accounts)
- Bios (Full, Short, Summarized)
- Angles (Talking Points with Topic, Outcomes, and Descriptions)
- Stories (Personal and career stories that can be used to connect with the podcast audience)
- Topics / Search Terms / Keywords (List of Keywords that the client would like to be associated with)

Respond in JSON format with the document ID:
{{"document_id": "most_relevant_document_id_here", "document_name": "document_name", "reasoning": "why this document is relevant"}}

If no document seems relevant, respond with:
{{"document_id": null, "document_name": null, "reasoning": "no relevant documents found"}}

Important: Only choose a document if it solves / answers something that is asked in the email. Your reasoning should completely directly relate to the email content. Define in the reasoning how the chosen document is relevant to the email content (What does it answer? Or what does it provide that is being asked? etc.). Also, it's completely fine to choose nothing if nothing is relevant. Do not wildly assume the contents of the documents. 
"""
        
        messages = [
            SystemMessage(content="You are a helpful assistant that identifies the most relevant documents for providing context to email responses."),
            HumanMessage(content=document_selection_prompt)
        ]
        
        document_response = model.invoke(messages)
        print(f"Document selection response: {document_response.content}")
        
        # Parse document selection response
        json_match = re.search(r'\{.*?\}', document_response.content, re.DOTALL)
        if not json_match:
            print("No JSON found in document selection response")
            return {
                "client_folder_id": client_folder_id,
                "relevant_document_content": "",
                "document_extraction_status": "Failed to parse document selection response",
                "gdrive_url": client_data.get("link", "")
            }
        
        document_selection_data = json.loads(json_match.group(0))
        document_id = document_selection_data.get("document_id")
        
        if not document_id:
            print("No relevant document found")
            return {
                "client_folder_id": client_folder_id,
                "relevant_document_content": "",
                "document_extraction_status": f"No relevant document found. Reasoning: {document_selection_data.get('reasoning', 'Unknown')}",
                "gdrive_url": client_data.get("link", "")
            }
        
        print(f"Selected document: {document_selection_data.get('document_name')} (ID: {document_id})")
        print(f"Reasoning: {document_selection_data.get('reasoning')}")
        
        print("=== Step 5: Extracting document content ===")
        
        # Extract content from the selected document
        response = requests.post(document_content_webhook, json={"documentID": document_id})
        
        if response.status_code != 200:
            print(f"Failed to extract document content. Status: {response.status_code}")
            return {
                "client_folder_id": client_folder_id,
                "relevant_document_content": "",
                "document_extraction_status": f"Failed to extract document content: {response.status_code}",
                "gdrive_url": client_data.get("link", "")
            }
        
        # Parse JSON response to extract document content
        try:
            response_data = response.json()
            document_content = response_data.get("text", "")
            extraction_status = response_data.get("status", "Unknown")
            
            print(f"Extraction status: {extraction_status}")
            print(f"Successfully extracted document content. Length: {len(document_content)} characters")
            
            return {
                "client_folder_id": client_folder_id,
                "relevant_document_content": document_content,
                "document_extraction_status": f"Success: Extracted content from '{document_selection_data.get('document_name')}' ({len(document_content)} chars)",
                "gdrive_url": client_data.get("link", "")
            }
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response from document extraction webhook: {e}")
            return {
                "client_folder_id": client_folder_id,
                "relevant_document_content": "",
                "document_extraction_status": f"Failed to parse document extraction response: {e}",
                "gdrive_url": client_data.get("link", "")
            }
        
    except Exception as e:
        print(f"Error in client_gdrive_document_extraction_node: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return {
            "client_folder_id": "",
            "relevant_document_content": "",
            "document_extraction_status": f"Error: {str(e)}",
            "gdrive_url": ""
        }

def webhook_node(state: AgentState) -> dict:
    """
    Send a webhook to create Gmail draft via Make.com integration
    """
    print("Currently in: webhook_node")
    webhook_url = "https://hook.us1.make.com/vaggalj5a1oe5llfeolhxvbjwfc705uf"

    # Prepare the payload
    payload = {
        "draft": state["draft"],
        "subject": state["subject"],
        "sender_email": state["sender_email"]
    }

    try:
        # Make the POST request to the webhook
        response = requests.post(webhook_url, json=payload)

        # Check if the request was successful
        if response.status_code == 200:
            return {
                "webhook_status": f"Successfully sent draft to webhook with status: {response.status_code}"
            }
        else:
            return {
                "webhook_status": f"Failed to send draft to webhook. Status code: {response.status_code}"
            }
    except Exception as e:
        return {
            "webhook_status": f"Error sending webhook: {str(e)}"
        }

# Define a passing node to route based on classification type
def passing_node(state: AgentState) -> AgentState:
    print("Currently in: passing_node (rejection_routing)")
    # Simply pass the state through without modification
    # The reason for this node is to have a start point for conditional routing (since we can't conditionally route coming from another conditional node)
    return state

# Conditional router function to determine if we should continue processing
def should_continue_processing(state: AgentState):
    from prompts import continuation_decision_prompt

    # Use the model to decide if we should continue with draft generation
    messages = [
        SystemMessage(content=continuation_decision_prompt),
        HumanMessage(content=state["email_text"])
    ]

    response = model.invoke(messages)
    decision = response.content.strip().lower()

    print(f"Continuation decision: {decision}")

    if decision == "no":
        print("AI determined that no draft is needed - skipping draft generation")
        return "end"
    else:
        # Default to continuing if unclear
        return "continue"

# Router to determine if we need special rejection handling
def rejection_router(state: AgentState):
    # Check if the classification is one of the rejection types that needs special handling
    rejection_types = [
        "Identity-based rejection",
        "Topic-based rejection", 
        "Qualification-based rejection"
    ]

    if state["label"] in rejection_types:
        print(f"Detected rejection type: {state['label']} - routing to rejection handling")
        return "handle_rejection"
    else:
        print(f"Classification: {state['label']} - using standard pipeline")
        return "standard_pipeline"

# Build and compile the state graph
builder = StateGraph(AgentState)
builder.add_node("classify", classify_node)
builder.add_node("rejection_routing", passing_node)
builder.add_node("gen_query", generate_query_node)
builder.add_node("retrieve", retrieve_threads_node)
builder.add_node("generate_draft", draft_node)
builder.add_node("rejection_strategy", rejection_strategy_node)
builder.add_node("soft_rejection_drafting", soft_rejection_drafting_node)
builder.add_node("slack_notification", slack_notification_node)
builder.add_node("client_gdrive_document_extraction", client_gdrive_document_extraction_node)
builder.add_node("client_gdrive_document_extraction_rejection_path", client_gdrive_document_extraction_node)
builder.add_node("webhook", webhook_node)

builder.set_entry_point("classify")

# Add conditional edges after classification
builder.add_conditional_edges(
    "classify",
    should_continue_processing,
    {
        "end": END,  # If should not continue, end the process
        "continue": "rejection_routing"  # If should continue, route to the rejection routing node
    }
)

# Add conditional edges for rejection handling and standard pipeline
builder.add_conditional_edges(
    "rejection_routing",
    rejection_router,  # Use the rejection_router function to determine the path
    {
        "handle_rejection": "rejection_strategy",
        "standard_pipeline": "gen_query",
    }
)

# Add conditional edges after checking if it's a rejection
builder.add_edge("rejection_strategy", "client_gdrive_document_extraction_rejection_path")
builder.add_edge("client_gdrive_document_extraction_rejection_path", "soft_rejection_drafting")
builder.add_edge("soft_rejection_drafting", "slack_notification")
builder.add_edge("slack_notification", "webhook")

# Standard pipeline path
builder.add_edge("gen_query", "retrieve")
builder.add_edge("retrieve", "client_gdrive_document_extraction")
builder.add_edge("client_gdrive_document_extraction", "generate_draft")
builder.add_edge("generate_draft", "slack_notification")
builder.add_edge("slack_notification", "webhook")
builder.add_edge("webhook", END)

graph = builder.compile(checkpointer=memory)

print("Graph Initialized")


def main():
    EMAIL_TEXT = """ """
    state = {
        "email_text": EMAIL_TEXT,
        "subject": "Test Subject",
        "sender_name": "Test Sender",
        "sender_email": "test@example.com"
    }
    thread = {"configurable": {"thread_id": "1"}}
    result = graph.invoke(state, thread)

    # Print the result with better formatting
    print("\n--- FINAL RESULT ---")
    for key, value in result.items():
        if isinstance(value, list):
            print(f"\n---\n")
            print(f"\n{key}:")
            for item in value:
                print(f"\n -.-\n")
                print(f"  - {item}")
        else:
            if key == "email_text":
                # For email_text just print first few characters to avoid cluttering console
                print(f"\n---\n")
                print(f"\n{key}: {value[:100]}...")
            else:
                print(f"\n---\n")
                print(f"\n{key}: {value}")
    print("\n------------------")

if __name__ == "__main__":
    main()