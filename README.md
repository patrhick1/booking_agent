# my-assistant

Repository for the my-assistant project.

Booking & Reply Assistant — v2.0
────────────────────────────────

PURPOSE  
Automated podcast booking assistant that processes emails, classifies responses, extracts relevant client documents, and generates contextual draft replies with minimal human intervention.

Key Features:
• **Email Classification**: Automatically categorizes incoming emails into predefined response types
• **Document Extraction**: Intelligently retrieves relevant client documents from Google Drive
• **Contextual Drafting**: Generates personalized responses using RAG (Retrieval-Augmented Generation)
• **Rejection Handling**: Special pipeline for challenging rejections with strategic angles
• **Slack Integration**: Interactive notifications for human review and approval
• **Gmail Integration**: Automated draft creation in Gmail via webhook

────────────────────────────────
1. Core Architecture (v2)
────────────────────────────────

The system uses **LangGraph** for orchestrating a complex multi-node pipeline with conditional routing:

```
┌─────────────────┐
│   Email Input   │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│   Classify      │ → Categorizes email into response types
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ Continue Check  │ → Decides if processing should continue
└─────────────────┘
         │
    ┌────┴───────┐
    ▼            ▼
┌─────────┐ ┌──────────────┐
│Standard │ │ Rejection    │
│Pipeline │ │ Handling     │
└─────────┘ └──────────────┘
    │              └─────────┐
    ▼                        ▼
┌─────────────────┐ ┌──────────────────┐
│Query Generation │ │Rejection Strategy│
└─────────────────┘ └──────────────────┘
    │                       │
    ▼                       ▼
┌─────────────────┐ ┌──────────────────┐
│Vector Retrieval │ │Soft Rejection    │
└─────────────────┘ │Drafting          │
    │              └──────────────────┘
    ▼                       │
┌─────────────────┐         │
│Doc Extraction   │         │
└─────────────────┘         │
    │                       │
    ▼                       │
┌─────────────────┐         │
│Draft Generation │         │
└─────────────────┘         │
    │                       │
    └────┬──────────────────┘
         ▼
┌─────────────────┐
│ Draft Editing   │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│Slack Notification│
└─────────────────┘
         │
         ▼
┌─────────────────┐
│Gmail Webhook    │
└─────────────────┘
```

────────────────────────────────
2. Response Classifications
────────────────────────────────

**Standard Classifications:**
- A. Rejected – "We do not allow guests."
- B. Pay-to-Play – "Paid slots only."  
- C. Accepted – "We'd love to have you!"
- D. Conditional – "Interested – more info?"
- E. Other / Unknown – Any response that doesn't fit above categories

**Special Rejection Types** (Trigger advanced handling):
- Identity-based rejection
- Topic-based rejection  
- Qualification-based rejection

────────────────────────────────
3. Document Intelligence System
────────────────────────────────

**Google Drive Integration Process:**
1. **Client Identification**: AI analyzes email content to identify relevant client
2. **Folder Mapping**: Matches client to their Google Drive folder structure
3. **Document Selection**: Intelligently selects most relevant documents (typically Final Briefs)
4. **Content Extraction**: Retrieves document content via Make.com webhooks
5. **Context Integration**: Incorporates document data into draft generation

**Document Types Processed:**
- Client Final Briefs (bios, talking points, angles, stories)
- Background information documents
- Previous interview materials
- Client expertise summaries

────────────────────────────────
4. Technology Stack
────────────────────────────────

**Core Framework:**
- **LangGraph**: State management and workflow orchestration
- **LangChain**: LLM integration and prompt management
- **OpenAI**: `o4-mini-2025-04-16` for text generation, `text-embedding-3-small` for embeddings

**Data & Storage:**
- **Vector Database**: DataStax Astra DB for email thread similarity search
- **Document Storage**: Google Drive integration via Make.com webhooks
- **State Persistence**: MemorySaver checkpointer for conversation continuity

**Integrations:**
- **Gmail API**: Draft creation and email processing
- **Slack API**: Interactive notifications with approval workflows
- **Make.com**: Google Drive document extraction webhooks
- **Attio CRM**: Client relationship management integration

**Deployment:**
- **FastAPI**: REST API for webhook endpoints (`/start_agent_v2`)
- **uvicorn**: ASGI server to run the FastAPI application.

────────────────────────────────
5. File Structure
────────────────────────────────
```
my-assistant/
├── src/
│   ├── main.py                       # Core LangGraph agent for processing emails.
│   ├── prompts.py                    # All LLM prompt templates.
│   │
│   ├── bookingagent_api.py           # FastAPI server definitions and endpoints.
│   ├── server.py                     # Script to run the FastAPI server.
│   │
│   ├── email_service.py              # Core service for fetching emails (IMAP & Gmail auth).
│   ├── gmail_service.py              # Extends EmailService for Gmail-specific actions.
│   ├── google_docs_service.py        # Service for all Google Drive/Docs interactions.
│   ├── astradb_services.py           # Service for vector database operations (AstraDB).
│   ├── slack_interactivity.py        # Handlers for interactive Slack components.
│   ├── utils.py                      # Utility functions, including Slack messaging.
│   │
│   ├── attio_service.py              # Client for interacting with the Attio CRM API.
│   ├── attio_agent.py                # LangGraph agent for Attio-related tasks.
│   │
│   └── Test Case/
│       ├── test_multiple_scenarios.py  # Automated testing for various email scenarios.
│       └── test_data.py            # Sample email data for tests.
│
├── run_assistant.py                  # Main polling script to fetch and process emails.
├── requirements.txt                  # Python package dependencies.
├── README.md                         # This file.
├── .gitignore                        # Specifies intentionally untracked files to ignore.
└── .env                              # Environment variables (e.g., API keys).
```

────────────────────────────────
6. Workflow Execution
────────────────────────────────

**Manual Testing:**
```bash
# Interactive single email test
python src/test_pipeline.py

# Automated multi-scenario testing  
python "src/Test Case/test_multiple_scenarios.py"
```

**API Deployment:**
```bash
# Start API server
python src/bookingagent_api.py

# Process email via API
POST /start_agent_v2
{
  "email": "email content",
  "subject": "subject line",
  "sender_name": "sender name", 
  "sender_email": "sender@email.com"
}
```

**Production Deployment:**
- Replit deployment handles incoming email webhooks
- Processes emails automatically via scheduled triggers
- Human approval required via Slack before sending

────────────────────────────────
7. Advanced Features (v2)
────────────────────────────────

**Smart Rejection Handling:**
- Analyzes rejection reasons (identity, topic, qualification-based)
- Generates strategic challenge angles
- Creates persuasive follow-up responses
- Leverages client expertise from documents

**Interactive Slack Workflow:**
- Rich message formatting with email context
- One-click approval/rejection buttons
- Direct links to client CRM and documents
- Real-time status updates

**Document-Aware Responses:**
- Automatically extracts relevant client context
- Incorporates talking points and angles
- Uses client stories and background
- Maintains consistent brand voice

**Quality Assurance:**
- Multi-stage draft editing and refinement
- Continuation checks to prevent unnecessary responses
- Error handling and fallback mechanisms
- Comprehensive logging and monitoring

────────────────────────────────
8. Environment Setup
────────────────────────────────

**Required Environment Variables:**
```bash
# OpenAI
OPENAI_API_KEY=your_openai_key

# Astra DB
ASTRA_DB_API_ENDPOINT=your_astra_endpoint
ASTRA_DB_APPLICATION_TOKEN=your_astra_token

# Slack
SLACK_WEBHOOK_URL=your_slack_url

# Make.com Webhooks
GDRIVE_CLIENT_ROOT_FOLDER_ID=your_gdrive_root_folder_for_clients
GMAIL_DRAFT_WEBHOOK=your_gmail_webhook
GDRIVE_FOLDER_WEBHOOK=your_folder_webhook
GDRIVE_CONTENT_WEBHOOK=your_content_webhook

# Attio CRM
ATTIO_ACCESS_TOKEN=your_attio_access_token
```

**Installation:**
```bash
# Install dependencies from requirements.txt
pip install -r requirements.txt

# To run the automated email polling assistant
python run_assistant.py
```

────────────────────────────────
9. Development Status
────────────────────────────────

**Completed Features:**
✅ LangGraph pipeline architecture  
✅ Email classification system  
✅ Vector-based thread retrieval  
✅ Document extraction from Google Drive  
✅ Contextual draft generation  
✅ Rejection handling with strategic angles  
✅ Interactive Slack notifications  
✅ Gmail draft creation via webhooks  
✅ Comprehensive testing framework  
✅ FastAPI deployment endpoints  

Legend:
✅ Completed | 🔄 In Progress | 📋 Planned
