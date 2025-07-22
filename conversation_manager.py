import os
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv
from tools import tools
from pprint import pprint
from logging_util import get_logger

# Load environment variables from .env file
load_dotenv()

logger = get_logger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
if not client.api_key:
    raise ValueError("OPENAI_API_KEY not found in .env file")

# Set the model to use for all responses
model = "gpt-4.1-nano"
print(tools)

class ConversationManager:
    def __init__(self):
        self.messages = [{
            "role": "system",
            "content": "You are a helpful assistant engaging in a voice conversation. Keep your responses clear and concise."
        }]
    
    def add_message(self, role, content):
        """Add a message to the conversation history"""
        self.messages.append({"role": role, "content": content})
    
    def generate_response(self):
        """Generate a response using the conversation history"""
        global tools
        try:
            try:
                response = client.responses.create(
                    model=model,
                    input=self.messages,
                    # tools=tools,
                )
            except Exception as e:
                # Check for MCP server down error (error code 424 and tool list retrieval message)
                if (
                    hasattr(e, "args") and e.args and isinstance(e.args[0], str)
                    and ("Error code: 424" in e.args[0] or "424" in str(e))
                    and ("Error retrieving tool list from MCP server" in e.args[0] or "tool list" in str(e))
                ):
                    print("MCP server unavailable, retrying without that server's tools...")
                    # Filter out the Google Calendar MCP server from the tools list
                    filtered_tools = [
                        t for t in tools
                        if not (t.get("type") == "mcp" and t.get("server_label") == "google_calendar")
                    ] if tools else None
                    # Update the global tools variable so it's not retried again
                    tools = filtered_tools if filtered_tools else None
                    # Add a message to the conversation context
                    self.add_message(
                        "system",
                        "Note: The Google Calendar tools are temporarily unavailable due to a server issue. Calendar-related actions will not work until the server is restored."
                    )
                    response = client.responses.create(
                        model=model,
                        input=self.messages,
                        tools=tools,
                    )
                else:
                    logger.error(f"Error generating response: {e}")
                    raise
            outputs = response.output
            # Extract the assistant's text from the output structure (using attribute access)
            response_text = None
            if outputs and isinstance(outputs, list):
                for item in outputs:
                    if (
                        getattr(item, "role", None) == "assistant"
                        and hasattr(item, "content")
                        and isinstance(item.content, list)
                    ):
                        for content_item in item.content:
                            if (
                                getattr(content_item, "type", None) == "output_text"
                                and hasattr(content_item, "text")
                            ):
                                response_text = content_item.text
                                break
                        if response_text:
                            break
            if not response_text:
                print("No assistant text found in response output.")
                return None
            self.add_message("assistant", response_text)
            return response_text
        except Exception as e:
            print(f"Error generating response: {e}")
            return None 