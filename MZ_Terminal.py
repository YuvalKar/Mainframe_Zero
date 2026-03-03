import os
import ast
import subprocess
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
            ai_code = response.text
            
            print("\n--- AI Output ---")
            print(ai_code)
            print("-----------------\n")
            
            # --- QA Station: Syntax Validation ---
            is_valid_python = False

            try:
                # ast.parse reads the string and checks if it's grammatically correct Python
                # It does NOT execute the code, so it's perfectly safe
                ast.parse(ai_code)
                is_valid_python = True
                print("[System: QA Passed - The output is valid Python syntax.]")
                
            except SyntaxError as err:
                # If ast.parse fails, it throws a SyntaxError
                pass # do nothing, we just won't execute it
            
            # --- Execution Station (Only if QA passed) ---
            if is_valid_python:
                # Human in the loop: Ask the boss before doing anything crazy
                user_decision = input("Save to file and run? (y/n): ")
                
                if user_decision.lower() == 'y':
                    filename = "generated_script.py"
                    
                    # Write the raw code to a new Python file
                    with open(filename, "w", encoding="utf-8") as file:
                        file.write(ai_code)
                    
                    print(f"\n[System: Code saved to {filename}. Executing now...]\n")
                    
                    # Run the newly created file using the modern subprocess module
                    subprocess.run(["python", filename])
                
        except Exception as e:
            print(f"\n[Error handling request: {e}]\n")

if __name__ == "__main__":
    terminal_chat()