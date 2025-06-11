# src/main.py

import os
import json
import re
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from typing import TypedDict, List

# --- Service and Utility Imports ---
# Make sure these new service files exist in your src/ directory
from src.astradb_services import AstraDBService
from src.google_docs_service import GoogleDocsService
from src.gmail_service import GmailApiService
from src.prompts import (
    classification_fewshot, draft_generation_prompt, slack_notification_prompt,
    query_for_relevant_email_prompt, rejection_strategy_prompt,
    soft_rejection_drafting_prompt, draft_editing_prompt, continuation_decision_prompt,
    client_gdrive_extract_prompt
)
from src.utils import send_interactive_message
from langgraph.checkpoint.memory import MemorySaver

# --- Initialization ---
load_dotenv()
memory = MemorySaver()
model = ChatOpenAI(model="o4-mini-2025-04-16", temperature=1)

# Initialize all services
astra_service = AstraDBService()
google_service = GoogleDocsService()
gmail_service = GmailApiService()

# --- State Definition ---
class AgentState(TypedDict):
    email_text: str
    subject: str
    sender_name: str
    sender_email: str
    label: str
    vector_query: str
    relevant_threads: List[str]
    draft: str
    final_draft: str
    slack_message: str
    notification_status: str
    rejection_type: str
    challenge_angles: List[str]
    draft_status: str  # Renamed from webhook_status
    attio_url: str
    gdrive_url: str
    client_folder_id: str
    relevant_document_content: str
    document_extraction_status: str

# --- Graph Node Implementations ---

def classify_node(state: AgentState) -> dict:
    messages = [
        SystemMessage(content=classification_fewshot),
        HumanMessage(content=state["email_text"]),
    ]
    response = model.invoke(messages)
    return {"label": response.content.strip()}

def generate_query_node(state: AgentState) -> dict:
    messages = [
        SystemMessage(content=query_for_relevant_email_prompt),
        HumanMessage(content=state["email_text"]),
    ]
    response = model.invoke(messages)
    return {"vector_query": response.content}

def retrieve_threads_node(state: AgentState) -> dict:
    threads = astra_service.fetch_threads(state["vector_query"], top_k=5)
    return {"relevant_threads": threads}

def client_gdrive_document_extraction_node(state: AgentState) -> dict:
    """Extracts documents from Google Drive using the GoogleService."""
    root_folder_id = os.getenv("GDRIVE_CLIENT_ROOT_FOLDER_ID")
    if not root_folder_id:
        return {"document_extraction_status": "GDRIVE_CLIENT_ROOT_FOLDER_ID not set in .env file."}

    try:
        # Step 1: Get client folders from Google Drive
        all_files = google_service.get_files_in_folder(root_folder_id)
        folder_data = [
            {"name": f.get("name"), "id": f.get("id"), "webViewLink": f.get("webViewLink")}
            for f in all_files if 'folder' in f.get('mimeType', '')
        ]
        if not folder_data:
            return {"document_extraction_status": "No client folders found in the root directory."}

        # Step 2: Use LLM to identify the relevant client folder
        client_identification_prompt = f"""
You are analyzing an email thread to identify which client is being discussed.

Email content:
---
{state["email_text"]}
---

Available client folders:
{json.dumps(folder_data, indent=2)}

Look for:
1. Client names mentioned in the email (first name, last name, or company name)
2. Company names or brands mentioned
3. Any other identifying information

Match these to the folder names. Be flexible with matching:
- "Erick Vargas" could match "Followup CRM - Erick Vargas"
- "Ashwin from Synup" could match "Synup - Ashwin Ramesh"
- "Ringmaster" could match the "Ringmaster" folder

Respond ONLY with a JSON object:
{{"folder_id": "folder_id_here", "link": "webViewLink_here", "client_name": "matched_folder_name"}}

If no clear match, respond with:
{{"folder_id": null, "link": null, "client_name": null}}
"""
        messages = [
            SystemMessage(content="You are an expert at matching client names in emails to folder names. Be flexible and look for partial matches."),
            HumanMessage(content=client_identification_prompt)
        ]
        client_response = model.invoke(messages)
        
        json_match = re.search(r'\{.*\}', client_response.content, re.DOTALL)
        if not json_match:
            return {"document_extraction_status": "Failed to parse client identification response"}
        
        try:
            client_data = json.loads(json_match.group(0))
        except json.JSONDecodeError:
            return {"document_extraction_status": "JSON parse error in client identification"}
            
        client_folder_id = client_data.get("folder_id")
        gdrive_url = client_data.get("link")

        if not client_folder_id:
            return {"document_extraction_status": "No matching client folder found"}

        # Step 3 & 4: Get docs from that folder and identify the most relevant one
        client_docs = google_service.get_files_in_folder(client_folder_id)
        document_data = [
            {"name": d.get("name"), "id": d.get("id")}
            for d in client_docs if 'document' in d.get('mimeType', '')
        ]
        
        if not document_data:
            return {"document_extraction_status": "No documents found in the client folder", "gdrive_url": gdrive_url}

        # Create document selection prompt
        document_selection_prompt = f"""
You need to select the most relevant document for responding to this email:

Email content:
---
{state["email_text"]}
---

Available documents in client folder:
{json.dumps(document_data, indent=2)}

Choose the document that would be most helpful for crafting a response. Look for:
1. "Final Brief" or "Final Draft" documents (highest priority)
2. Bio documents if bio is requested
3. Angles/talking points documents if topics are discussed
4. Recent/latest versions (v2, v3, etc.)

Respond with JSON format:
{{"document_id": "document_id_here", "reasoning": "why this document was selected"}}

If no document seems relevant:
{{"document_id": null, "reasoning": "explanation why no document was selected"}}
"""
        
        messages = [
            SystemMessage(content="You are an expert at selecting the most relevant client document for email responses. Prioritize Final Briefs and latest versions."),
            HumanMessage(content=document_selection_prompt)
        ]
        doc_response = model.invoke(messages)
        
        json_match = re.search(r'\{.*\}', doc_response.content, re.DOTALL)
        if not json_match:
            return {"document_extraction_status": "Failed to parse document selection response", "gdrive_url": gdrive_url}

        try:
            doc_selection_data = json.loads(json_match.group(0))
        except json.JSONDecodeError:
            return {"document_extraction_status": "JSON parse error in document selection", "gdrive_url": gdrive_url}

        document_id = doc_selection_data.get("document_id")

        if not document_id:
            return {"document_extraction_status": "No relevant document found", "gdrive_url": gdrive_url}

        # Step 5: Extract content from the selected document
        document_content = google_service.get_document_content(document_id)
        
        return {
            "client_folder_id": client_folder_id,
            "relevant_document_content": document_content,
            "document_extraction_status": "Success",
            "gdrive_url": gdrive_url
        }
    except Exception as e:
        return {"document_extraction_status": f"An unexpected error occurred: {e}"}

def draft_node(state: AgentState) -> dict:
    prompt_with_examples = draft_generation_prompt.replace("{samplemailshere}", "\n\n".join(state["relevant_threads"]))
    if state.get("relevant_document_content"):
        additional_context = f"\n\nAdditional Client Context from Documents:\n{state['relevant_document_content']}"
        prompt_with_examples += additional_context
    messages = [SystemMessage(content=prompt_with_examples), HumanMessage(content=state["email_text"])]
    response = model.invoke(messages)
    return {"draft": response.content}

def rejection_strategy_node(state: AgentState) -> dict:
    prompt = rejection_strategy_prompt.replace("{{email}}", state["email_text"])
    prompt = prompt.replace("{{client}}", "Client information would go here")
    prompt = prompt.replace("{{podcast}}", "Podcast information would go here") 
    prompt = prompt.replace("{{host_info}}", "Host information would go here")
    messages = [SystemMessage(content=prompt)]
    response = model.invoke(messages)
    response_content = response.content
    try:
        json_start = response_content.rfind("{")
        json_end = response_content.rfind("}") + 1
        json_str = response_content[json_start:json_end]
        result = json.loads(json_str)
        return {
            "rejection_type": result.get("rejection_type", "Hard Rejection"),
            "challenge_angles": result.get("angles", [])
        }
    except Exception:
        return {"rejection_type": "Hard Rejection", "challenge_angles": []}

def soft_rejection_drafting_node(state: AgentState) -> dict:
    prompt = soft_rejection_drafting_prompt.replace("{{rejection_scenario}}", state["label"])
    angles = state.get("challenge_angles", [])
    angle_replacements = {
        "{{angle1}}": angles[0] if angles else "No specific angle available",
        "{{angle2}}": angles[1] if len(angles) > 1 else "No specific angle available",
        "{{angle3}}": angles[2] if len(angles) > 2 else "No specific angle available"
    }
    for placeholder, value in angle_replacements.items():
        prompt = prompt.replace(placeholder, value)
    prompt = prompt.replace("{{emailthreadhere}}", state["email_text"])
    if state.get("relevant_document_content"):
        prompt += f"\n\nAdditional Client Context from Documents:\n{state['relevant_document_content'][:2000]}..."
    messages = [SystemMessage(content=prompt)]
    response = model.invoke(messages)
    draft = response.content
    if "<response>" in draft and "</response>" in draft:
        start_idx = draft.find("<response>") + len("<response>")
        end_idx = draft.find("</response>")
        draft = draft[start_idx:end_idx].strip()
    return {"draft": draft}

def edit_draft_node(state: AgentState) -> dict:
    human_message_content = f"""Original Email:\n{state["email_text"]}\n\nDraft Response:\n{state["draft"]}"""
    messages = [SystemMessage(content=draft_editing_prompt), HumanMessage(content=human_message_content)]
    response = model.invoke(messages)
    return {"final_draft": response.content}

# def slack_notification_node(state: AgentState) -> dict:
#     print("Currently in: slack_notification_node")
#     # (No changes needed)
#     messages = [SystemMessage(content=slack_notification_prompt), HumanMessage(content=state["email_text"])]
#     response = model.invoke(messages)
#     notification_message = response.content + f"\n\nClassification: {state['label']}"
#     if state.get("rejection_type"):
#         notification_message += f"\nRejection Type: {state['rejection_type']}"
#     status_code = send_interactive_message(
#         notification_message, state["final_draft"], state["sender_email"], state["subject"],
#         state.get("attio_url", ""), state.get("gdrive_url", "")
#     )
#     return {"notification_status": f"Slack notification sent with status: {status_code}"}

def slack_notification_node(state: AgentState) -> dict:
    """Send interactive Slack notification for human review and approval."""
    if os.getenv("TESTING_MODE") == "true":
        return {"notification_status": "SKIPPED (Testing Mode)"}
    
    # Generate Slack notification message
    messages = [SystemMessage(content=slack_notification_prompt), HumanMessage(content=state["email_text"])]
    response = model.invoke(messages)
    notification_message = response.content + f"\n\nClassification: {state['label']}"
    
    if state.get("rejection_type"):
        notification_message += f"\nRejection Type: {state['rejection_type']}"
    
    # Send interactive message with approval buttons
    status_code = send_interactive_message(
        notification_message, 
        state["final_draft"], 
        state["sender_email"], 
        state["subject"],
        state.get("attio_url", ""), 
        state.get("gdrive_url", "")
    )
    
    return {"notification_status": f"Slack notification sent (Status: {status_code})"}

def create_gmail_draft_node(state: AgentState) -> dict:
    """Creates a Gmail draft using the GmailApiService, replacing the webhook."""
    # Check if we're in testing mode (skip Gmail draft creation)
    if os.getenv("TESTING_MODE") == "true":
        return {"draft_status": "SKIPPED (Testing Mode)"}
    
    try:
        status = gmail_service.create_draft(
            to=state["sender_email"],
            subject=f"Re: {state['subject']}",
            body=state["final_draft"]
        )
        return {"draft_status": status}
    except Exception as e:
        return {"draft_status": f"Failed: {str(e)[:100]}..."}

def passing_node(state: AgentState) -> AgentState:
    return state

def should_continue_processing(state: AgentState):
    messages = [SystemMessage(content=continuation_decision_prompt), HumanMessage(content=state["email_text"])]
    response = model.invoke(messages)
    decision = response.content.strip().lower()
    return "end" if decision == "no" else "continue"

def rejection_router(state: AgentState):
    rejection_types = ["Identity-based rejection", "Topic-based rejection", "Qualification-based rejection"]
    if state["label"] in rejection_types:
        return "handle_rejection"
    else:
        return "standard_pipeline"

# --- Graph Definition and Compilation ---
builder = StateGraph(AgentState)

# Add all nodes
builder.add_node("classify", classify_node)
builder.add_node("rejection_routing", passing_node)
builder.add_node("gen_query", generate_query_node)
builder.add_node("retrieve", retrieve_threads_node)
builder.add_node("client_gdrive_document_extraction", client_gdrive_document_extraction_node)
builder.add_node("generate_draft", draft_node)
builder.add_node("edit_draft", edit_draft_node)
builder.add_node("rejection_strategy", rejection_strategy_node)
builder.add_node("soft_rejection_drafting", soft_rejection_drafting_node)
builder.add_node("slack_notification", slack_notification_node)
builder.add_node("create_gmail_draft", create_gmail_draft_node)

# Define the workflow edges
builder.set_entry_point("classify")

builder.add_conditional_edges(
    "classify",
    should_continue_processing,
    {"end": END, "continue": "rejection_routing"}
)

builder.add_conditional_edges(
    "rejection_routing",
    rejection_router,
    {"handle_rejection": "rejection_strategy", "standard_pipeline": "gen_query"}
)

# Rejection Path
builder.add_edge("rejection_strategy", "gen_query")
builder.add_edge("soft_rejection_drafting", "edit_draft")

# Standard Path
builder.add_edge("gen_query", "retrieve")
builder.add_edge("retrieve", "client_gdrive_document_extraction")

# Common Path after document extraction
builder.add_edge("client_gdrive_document_extraction", "generate_draft")
builder.add_edge("generate_draft", "edit_draft")
builder.add_edge("edit_draft", "slack_notification")
builder.add_edge("slack_notification", "create_gmail_draft")
builder.add_edge("create_gmail_draft", END)

graph = builder.compile(checkpointer=memory)

# Main function for direct execution (testing)
if __name__ == "__main__":
    # Example usage for testing
    EMAIL_TEXT = """
    Hi Aidrian,
    Thanks for the email. Tom Elliot sounds interesting.
    Could you send over his bio and some potential talking points for our show?
    We focus on early-stage startup growth.
    Best,
    Jane Doe
    """
    state = {
        "email_text": EMAIL_TEXT,
        "subject": "Re: Podcast Guest - Tom Elliot",
        "sender_name": "Jane Doe",
        "sender_email": "jane.doe@example.com"
    }
    import uuid
    thread_id = str(uuid.uuid4())
    thread = {"configurable": {"thread_id": thread_id}}
    
    result = graph.invoke(state, thread)
    print("\n--- FINAL RESULT ---")
    print(json.dumps(result, indent=2))