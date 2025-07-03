# .tools.py
# Defines the OpenAI tools variable for an MCP server (Google Calendar) running at http://127.0.0.1:3000

# See: https://platform.openai.com/docs/guides/function-calling/tools

tools = [
    {
        "type": "mcp",
        "server_label": "google_calendar",
        "server_url": "http://127.0.0.1:3000",
        # Optionally, you can specify allowed_tools, headers, or require_approval here
        # "allowed_tools": ["list_events", "create_event", "delete_event"],
        # "headers": {"Authorization": "Bearer <token>"},
        # "require_approval": "always"
    }
] 