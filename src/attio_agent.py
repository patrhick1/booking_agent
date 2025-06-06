from typing import Annotated

from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI

from attio_service import AttioClient

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

def list_records(object_type: str, filters: dict = None, page: int = 1, limit: int = 5):
    """List records from Attio for the specified object type with optional filtering.

    Args:
        object_type: The type/slug of the object (e.g., 'podcast', 'company')
        filters: Optional dictionary of filters to apply
        page: Page number for pagination
        limit: Number of records per page
    """
    attio = AttioClient()
    response = attio.list_records(object_type, filters, page, limit)

    print("Calling list_records tool")

    # Format the response nicely for the agent
    # Handle different response types (dictionary or list)
    if isinstance(response, dict):
        records = response.get("data", {}).get("records", [])
    elif isinstance(response, list):
        records = response  # If response is already a list, use it directly
    else:
        records = []

    if records:
        return f"Found {len(records)} records for {object_type}. First few records: {records[:3]}"
    else:
        return f"No records found for {object_type} with the specified filters."

def filter_records(object_type: str, attribute_name: str, value: str, 
                  operator: str = "equals", page: int = 1, limit: int = 5):
    """Filter records where a specific attribute has a particular value.

    Args:
        object_type: The type/slug of the object (one of: 'companies', 'people', 'podcast')
        attribute_name: The attribute to filter on (For podcast slug: 'podcast_name', 'host_name'; For people slug: 'name', 'email_addresses'; For companies slug: 'name', 'domains')
        value: The value to filter by (exact match)
        operator: The comparison operator (currently only 'equals' is supported)
        page: Page number for pagination
        limit: Number of records per page
    """
    attio = AttioClient()
    print("Calling filter_records tool")
    response = attio.filter_records(object_type, attribute_name, value, operator, page, limit)

    # Format the response nicely for the agent
    records = []
    if isinstance(response, dict) and "data" in response:
        # Handle response format like {"data": [...]} or {"data": {"records": [...]}}
        if isinstance(response["data"], list):
            records = response["data"]
        elif isinstance(response["data"], dict) and "records" in response["data"]:
            records = response["data"]["records"]
    elif isinstance(response, list):
        records = response

    if records:
        # Return a summary and the actual records data
        record_details = []
        for record in records[:limit]:  # Limit the number of records to display
            # Extract key values from the record to display
            values = record.get("values", {})
            record_info = {
                "id": record.get("id", {}).get("record_id", ""),
                "values": values
            }
            record_details.append(record_info)

        return f"Found {len(records)} records for {object_type} where {attribute_name} {operator} '{value}'.\n\nRecord details: {record_details}"
    else:
        return f"No records yfound for {object_type} where {attribute_name} {operator} '{value}'."

def create_record(object_type: str, attributes: dict):
    """Create a new record in Attio.

    Args:
        object_type: The type/slug of the object (e.g., 'podcast', 'companies', 'people')
        attributes: Dictionary of attribute values to set for the new record
                   (For podcast: {'podcast_name': 'Name', 'host_name': 'Host', 'category': 'Category'})
                   (For people: {'name': 'Name', 'email_addresses': ['email@example.com'], 'title': 'Title'})
                   (For companies: {'name': 'Company Name', 'domains': ['example.com']})
    """
    attio = AttioClient()
    print("Calling create_record tool")

    # Validate inputs
    if not object_type:
        return "Error: Object type is required (e.g., 'podcast', 'companies', 'people')"
    if not attributes or not isinstance(attributes, dict):
        return "Error: Attributes must be provided as a dictionary"

    try:
        # Create the record
        response = attio.create_record(object_type, attributes)

        # Format the response for the agent
        if response and "data" in response and "record" in response["data"]:
            record_id = response["data"]["record"]["id"]
            return f"Successfully created {object_type} record with ID: {record_id}\n\nAttributes: {attributes}"
        else:
            return f"Record creation may have failed. Response: {response}"
    except Exception as e:
        return f"Error creating record: {str(e)}"

def get_record(object_type: str, record_id: str):
    """Get a specific record by ID from Attio.

    Args:
        object_type: The type/slug of the object (e.g., 'podcast', 'companies', 'people')
        record_id: The ID of the record to retrieve
    """
    attio = AttioClient()
    print("Calling get_record tool")

    # Validate inputs
    if not object_type:
        return "Error: Object type is required (e.g., 'podcast', 'companies', 'people')"
    if not record_id:
        return "Error: Record ID is required"

    try:
        # Get the record
        response = attio.get_record(object_type, record_id)

        # Format the response for the agent
        if response and "data" in response and "record" in response["data"]:
            record = response["data"]["record"]
            record_id = record.get("id", "Unknown ID")
            values = record.get("values", {})

            # Extract key information based on object type
            formatted_values = {}
            for key, value_list in values.items():
                if value_list and len(value_list) > 0:
                    # Take the first active value for each attribute
                    active_values = [v for v in value_list if "active_until" in v and v["active_until"] is None]
                    if active_values:
                        if "value" in active_values[0]:
                            formatted_values[key] = active_values[0]["value"]
                        elif "option" in active_values[0] and "title" in active_values[0]["option"]:
                            formatted_values[key] = active_values[0]["option"]["title"]

            return f"Found {object_type} record with ID: {record_id}\n\nAttributes: {formatted_values}"
        else:
            return f"No record found with ID {record_id} for {object_type} or the response format is unexpected."
    except Exception as e:
        return f"Error retrieving record: {str(e)}"

def update_record(object_type: str, record_id: str, attributes: dict, overwrite: bool = False):
    """Update an existing record in Attio.

    Args:
        object_type: The type/slug of the object (e.g., 'podcast', 'companies', 'people')
        record_id: The ID of the record to update
        attributes: Dictionary of attribute values to update for the record
                   (For podcast: {'podcast_name': 'Updated Name', 'host_name': 'New Host', 'category': 'New Category'})
                   (For people: {'name': 'Updated Name', 'title': 'New Title'})
                   (For companies: {'name': 'Updated Company Name'})
        overwrite: If True, replace existing multiselect values; if False, append to them (default: False)
    """
    attio = AttioClient()
    print("Calling update_record tool")

    # Validate inputs
    if not object_type:
        return "Error: Object type is required (e.g., 'podcast', 'companies', 'people')"
    if not record_id:
        return "Error: Record ID is required"
    if not attributes or not isinstance(attributes, dict):
        return "Error: Attributes must be provided as a dictionary"

    try:
        # Update the record
        response = attio.update_record(object_type, record_id, attributes, overwrite)

        # Format the response for the agent
        if response and "data" in response and "record" in response["data"]:
            updated_record_id = response["data"]["record"]["id"]
            return f"Successfully updated {object_type} record with ID: {updated_record_id}\n\nUpdated attributes: {attributes}\nOverwrite mode: {'Yes' if overwrite else 'No'}"
        else:
            return f"Record update may have failed. Response: {response}"
    except Exception as e:
        return f"Error updating record: {str(e)}"

def delete_record(object_type: str, record_id: str):
    """Delete a record from Attio.

    Args:
        object_type: The type/slug of the object (e.g., 'podcast', 'companies', 'people')
        record_id: The ID of the record to delete
    """
    attio = AttioClient()
    print("Calling delete_record tool")

    # Validate inputs
    if not object_type:
        return "Error: Object type is required (e.g., 'podcast', 'companies', 'people')"
    if not record_id:
        return "Error: Record ID is required"

    try:
        # Delete the record
        response = attio.delete_record(object_type, record_id)

        # Format the response for the agent
        if response and response.get("status", 0) == 200:
            return f"Successfully deleted {object_type} record with ID: {record_id}"
        else:
            return f"Record deletion may have failed. Response: {response}"
    except Exception as e:
        return f"Error deleting record: {str(e)}"

# Define which tools are enabled
ENABLED_TOOLS = {
    "filter_records": True,
    "list_records": False,
    "create_record": False,
    "get_record": False,
    "update_record": False,
    "delete_record": False,
}

# Initialize the LLM with tools based on configuration
llm = ChatOpenAI(model="o4-mini-2025-04-16", temperature=1)

# Build the tools list based on configuration
tools_to_bind = []
if ENABLED_TOOLS["filter_records"]:
    tools_to_bind.append(filter_records)
if ENABLED_TOOLS["list_records"]:
    tools_to_bind.append(list_records)
if ENABLED_TOOLS["create_record"]:
    tools_to_bind.append(create_record)
if ENABLED_TOOLS["get_record"]:
    tools_to_bind.append(get_record)
if ENABLED_TOOLS["update_record"]:
    tools_to_bind.append(update_record)
if ENABLED_TOOLS["delete_record"]:
    tools_to_bind.append(delete_record)

llm_with_tools = llm.bind_tools(tools_to_bind)

def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)

# Build the tool node with the same tools
tool_node = ToolNode(tools=tools_to_bind)
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)
# Any time a tool is called, we return to the chatbot to decide the next step
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")
graph = graph_builder.compile()

response = graph.invoke({"messages": [{"role": "user", "content": "Please find anything for the following podcast: The Libertarian Christian Podcast. And then find anything for the following person, our client: Erick Vargas."}]})

# Get the last message in the messages list
last_message = response['messages'][-1]

# Extract just the content from the last AI message
# For AIMessage objects specifically
ai_message_content = last_message.content

print(response)
print(ai_message_content)