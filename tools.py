import requests
import logging

# .tools.py
# Defines the OpenAI tools variable for an MCP server (Google Calendar) running at http://127.0.0.1:3000

# See: https://platform.openai.com/docs/guides/function-calling/tools

all_tools = [
    {
        "type": "mcp",
        "server_label": "google_calendar",
        "server_url": "https://8810-86-60-114-67.ngrok-free.app",
        "require_approval": "never",
        "allowed_tools": [
            "list-calendars",
            "list-events",
            "search-events",
            "list-colors",
            "create-event",
            "update-event",
            "delete-event",
            "get-freebusy",
            "get-current-time"
        ],
        # Optionally, you can specify allowed_tools, headers, or require_approval here
        # "allowed_tools": ["list_events", "create_event", "delete_event"],
        # "headers": {"Authorization": "Bearer <token>"},
        # "require_approval": "always"
    }
    # ... add other tools here ...
]

def is_server_alive(url, timeout=2):
    try:
        resp = requests.get(url, timeout=timeout)
        return resp.status_code < 400
    except Exception:
        return False

def get_available_tools():
    available = []
    for tool in all_tools:
        if tool.get("type") == "mcp":
            if is_server_alive(tool["server_url"]):
                available.append(tool)
            else:
                logging.warning(f"MCP server {tool['server_label']} at {tool['server_url']} is down, skipping.")
        else:
            available.append(tool)
    return available 

tools = get_available_tools()