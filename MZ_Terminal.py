import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

client = genai.Client()

def terminal_chat():
    # System rules - keeping it strictly technical
    system_rules = """
    You are a strictly technical Python code generator. 
    Return ONLY raw, valid Python code.
    Do NOT wrap the code in markdown blocks (like ```python).
    Do NOT add any explanations, greetings, or notes before or after the code.
    """
    
    # A helper function to conceptualize opening a fresh chat session
    def create_new_chat():
        print("\n[System: Creating a fresh chat session... Memory wiped.]")
        return client.chats.create(
            model='gemini-2.5-flash',
            config=types.GenerateContentConfig(
                system_instruction=system_rules,
                temperature=0.1,
            )
        )

    # Initialize the very first chat
    chat = create_new_chat()
    
    print("\n================================================")
    print(" Welcome to Mainframe Zero Terminal")
    print(" Type 'exit' to quit.")
    print(" Type 'reset' to clear memory and start a new chat.")
    print("================================================\n")

    # The infinite loop for terminal interaction
    while True:
        # Get input from the user in the terminal
        user_input = input("You: ")
        
        # Check for exit command
        if user_input.lower() in ['exit', 'quit']:
            print("Shutting down...")
            break
            
        # Check for our custom 'reset' command to wipe the context
        if user_input.lower() == 'reset':
            chat = create_new_chat()
            continue
            
        # Ignore empty inputs
        if not user_input.strip():
            continue

        try:
            # Send the message to the current active chat session
            response = chat.send_message(user_input)
            
            print("\n--- AI Output ---")
            print(response.text)
            print("-----------------\n")
            
        except Exception as e:
            print(f"\n[Error executing request: {e}]\n")

if __name__ == "__main__":
    terminal_chat()