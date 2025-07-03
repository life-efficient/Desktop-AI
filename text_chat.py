import sys
from main import ConversationManager


def main():
    print("Text Chat with AI Agent (type 'exit' to quit)")
    conversation = ConversationManager()
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting chat.")
            break
        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        if not user_input:
            continue
        conversation.add_message("user", user_input)
        print("Agent is thinking...")
        response = conversation.generate_response()
        if response:
            print(f"Agent: {response}")
        else:
            print("Agent failed to respond.")

if __name__ == "__main__":
    main() 