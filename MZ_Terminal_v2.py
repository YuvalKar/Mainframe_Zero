import os
import ast
import json
import subprocess
from google import genai
from google.genai import types
from dotenv import load_dotenv
import re
from senses.python_runner_sense import run_and_sense # New import

###################################################################################
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

#########################################################################
def passes_syntax_qa(code_string: str) -> bool:
    # ast.parse checks if it's grammatically correct Python without executing
    try:
        ast.parse(code_string)
        print("[System: QA Passed - The output is valid Python syntax.]")
        return True
    except SyntaxError as err:
        # print(f"\n[QA Alert: The AI generated invalid Python code!]\nError details: {err}")
        # print("Skipping execution. Please ask the AI to fix the code.\n")
        # Do nothing
        return False

#################################################################
def save_and_execute(code_string: str, target_filename: str = None):
    # Use the filename from the JSON, or a default one if missing
    filename = target_filename if target_filename else "generated_script.py"

    # Ask the human in the loop before firing
    user_decision = input(f"Save to {filename} and run? (y/n): ")

    if user_decision.lower() == 'y':
        with open(filename, "w", encoding="utf-8") as file:
            file.write(code_string)

        print(f"\n[System: Code saved to {filename}. Executing now...]\n")
        # Modern execution using subprocess - MODIFIED to use run_and_sense
        result_data = run_and_sense(filename)
        return result_data # Return the result data
    return None # Return None if not executed

#################################################################
def save_markdown(content_string: str, target_filename: str = None):
    # Use the filename from the JSON, or a default one if missing
    filename = target_filename if target_filename else "output.md"

    with open(filename, "w", encoding="utf-8") as file:
        file.write(content_string)
    print(f"\n[System: Markdown content cleanly saved to {filename}]\n")


###############################################################

# Load environment variables
load_dotenv()

client = genai.Client()

def terminal_chat():

    # Read the system prompt from our markdown file
    try:
        with open("system_prompt.md", "r", encoding="utf-8") as f:
            system_rules = f.read()
    except FileNotFoundError:
        print("[System Error: system_prompt.md not found!]")
        return

    # A helper function to conceptualize opening a fresh chat session
    def create_new_chat():
        print("\n[System: Creating a fresh chat session... Memory wiped.]")
        return client.chats.create(
            model='gemini-2.5-flash',
            config=types.GenerateContentConfig(
                system_instruction=system_rules,
                temperature=0.1,
                # Force the model to strictly return JSON!
                response_mime_type="application/json",
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

            # Station 3: JSON Parsing and Routing
            try:
                # Convert the AI's string response into a Python dictionary
                ai_data = json.loads(response.text)

                # Extract the fields based on our system_prompt.md schema
                thought_process = ai_data.get("thought_process", "")
                action = ai_data.get("action", "chat")
                content = ai_data.get("content", "")
                target_filename = ai_data.get("target_filename")

                print(f"\n[AI Thought Process]: {thought_process}")
                print(f"\n--- AI Output (Action: {action}) ---")
                print(content)
                print("-----------------\n")

                # --- The Router ---
                if action == "python":
                    # Station 4a: Python QA and Execution
                    if passes_syntax_qa(content):
                        execution_results = save_and_execute(content, target_filename)
                        if execution_results: # Only if execution actually happened
                            print("\n--- Python Execution Results ---")
                            print(f"Success: {execution_results['success']}")
                            print(f"Output:\n{execution_results['output']}")
                            print(f"Error:\n{execution_results['error']}")
                            print("------------------------------\n")

                            # CRITICAL: Send feedback to the AI
                            chat.send_message(f"[System Execution Feedback] Success: {execution_results['success']}, Output: {execution_results['output']}, Error: {execution_results['error']}")

                elif action == "markdown":
                    # Station 4b: Save Markdown
                    save_markdown(content, target_filename)

                elif action == "chat":
                    # Station 4c: Just chat, do nothing else
                    pass

                else:
                    print(f"[System Warning: Unknown action '{action}' received from AI.]")

            except json.JSONDecodeError:
                print("\n[System Error: AI did not return valid JSON!]")
                print("Raw output:", response.text)

        except Exception as e:
            print(f"\n[Error handling request: {e}]\n")

if __name__ == "__main__":
    terminal_chat()