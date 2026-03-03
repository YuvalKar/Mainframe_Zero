import os
import ast
import subprocess
from google import genai
from google.genai import types
from dotenv import load_dotenv
import re


def enrich_prompt_with_files(user_input: str) -> str:
    # Find all words starting with @ (supports letters, numbers, dots, slashes)
    file_matches = re.findall(r'@([\w\.\-\/]+)', user_input)
    
    if not file_matches:
        return user_input # Return as is if no files requested
        
    enriched_prompt = user_input + "\n\n--- Attached Files Context ---\n"
    
    for filename in file_matches:
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                enriched_prompt += f"\n[Content of {filename}]:\n{file_content}\n"
                print(f"[System: Successfully attached '{filename}' to context]")
            except Exception as e:
                print(f"[System Error: Could not read '{filename}': {e}]")
        else:
            print(f"[System Warning: File '{filename}' not found. Ignored.]")
            
    enriched_prompt += "------------------------------\n"
    return enriched_prompt


def passes_syntax_qa(code_string: str) -> bool:
    # ast.parse checks if it's grammatically correct Python without executing
    try:
        ast.parse(code_string)
        print("[System: QA Passed - The output is valid Python syntax.]")
        return True
    except SyntaxError as err:
        print(f"\n[QA Alert: The AI generated invalid Python code!]\nError details: {err}")
        print("Skipping execution. Please ask the AI to fix the code.\n")
        return False


def save_and_execute(code_string: str):
    # Ask the human in the loop before firing
    user_decision = input("Save to file and run? (y/n): ")
    
    if user_decision.lower() == 'y':
        filename = "generated_script.py"
        with open(filename, "w", encoding="utf-8") as file:
            file.write(code_string)
            
        print(f"\n[System: Code saved to {filename}. Executing now...]\n")
        # Modern execution using subprocess
        subprocess.run(["python", filename])

###############################################################
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
            # Station 1: Parsing & Enrichment
            final_prompt = enrich_prompt_with_files(user_input)
            
            # Station 2: The LLM Brain
            response = chat.send_message(final_prompt)
            ai_code = response.text
            
            print("\n--- AI Output ---")
            print(ai_code)
            print("-----------------\n")
            
            # Station 3: Quality Assurance
            if passes_syntax_qa(ai_code):
                
                # Station 4: Execution
                save_and_execute(ai_code)
                
        except Exception as e:
            print(f"\n[Error handling request: {e}]\n")

if __name__ == "__main__":
    terminal_chat()