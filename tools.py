# .tools.py
# Defines the OpenAI tools variable for an MCP server (Google Calendar) running at http://127.0.0.1:3000

# See: https://platform.openai.com/docs/guides/function-calling/tools

tools = [
    {
        "type": "mcp",
        "server_label": "google_calendar",
        "server_url": "https://99ae-86-60-114-67.ngrok-free.app",
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
] 