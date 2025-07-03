import os
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv
from tools import tools
from pprint import pprint

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
if not client.api_key:
    raise ValueError("OPENAI_API_KEY not found in .env file")

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
        try:
            response = client.responses.create(
                model="gpt-4.1-mini",
                input=self.messages,
                tools=tools,
            )
            outputs = response.output
            # pprint(outputs, indent=4)
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