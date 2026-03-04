import os
import ast
import json
import importlib.util
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv
from senses.python_runner_sense import run_and_sense
from core_utils.skill_loader import get_available_skills

###################################################################################
def enrich_prompt_with_files(user_input: str) -> str:
    # Find all words starting with @ (supports letters, numbers, dots, slashes)
    file_matches = re.findall(r'@([\w\.\-\/]+)', user_input)
    
    if not file_matches:
        return user_input 

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
        result_data = run_and_sense(filename)
        return result_data 
    return None 

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

    def create_new_chat():
        print("\n[System: Creating a fresh chat session... Memory wiped.]")
        return client.chats.create(
            model='gemini-2.5-flash',
            config=types.GenerateContentConfig(
                system_instruction=system_rules,
                temperature=0.1,
                # Force the model to strictly return JSON
                response_mime_type="application/json",
            )
        )

    # Initialize the very first chat
    chat = create_new_chat()

    print("\n================================================")
    print(" Welcome to Mainframe Zero Terminal (v5 - Dynamic Cerebellum)")
    print(" Type 'exit' to quit.")
    print(" Type 'reset' to clear memory and start a new chat.")
    print("================================================\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() in ['exit', 'quit']:
            print("Shutting down...")
            break

        if user_input.lower() == 'reset':
            chat = create_new_chat()
            continue

        if not user_input.strip():
            continue

        try:
            # --- [System: The Cerebellum Injection] ---
            # Dynamically load skills at the start of every turn
            current_skills = get_available_skills("cerebellum")
            skills_context = "\n\n[System Context: Current Available Skills in Cerebellum]\n"
            if current_skills:
                for name, desc in current_skills.items():
                    skills_context += f"- Skill Name: '{name}'\n  Description & API: {desc}\n\n"
            else:
                skills_context += "No skills available yet.\n"
            
            # Inject it quietly into the prompt
            final_prompt = enrich_prompt_with_files(user_input) + skills_context

            # --- Sending to the Brain ---
            response = chat.send_message(final_prompt)

            try:
                # Convert the AI's string response into a Python dictionary
                ai_data = json.loads(response.text)

                # Extract fields based on the NEW system_prompt.md schema
                thought_process = ai_data.get("thought_process", "")
                action = ai_data.get("action", "chat")
                content = ai_data.get("content", "")
                target_filename = ai_data.get("target_filename")
                skill_name = ai_data.get("skill_name")
                skill_kwargs = ai_data.get("skill_kwargs", {})

                print(f"\n[AI Thought Process]: {thought_process}")
                print(f"\n--- AI Output (Action: {action}) ---")
                
                # Only print content if it exists (skills usually have null content)
                if content:
                    print(content)
                print("-----------------\n")

                # --- The New Generic Router ---
                
                if action == "python":
                    if passes_syntax_qa(content):
                        execution_results = save_and_execute(content, target_filename)
                        if execution_results: 
                            print("\n--- Python Execution Results ---")
                            print(f"Success: {execution_results['success']}")
                            print(f"Output:\n{execution_results['output']}")
                            print(f"Error:\n{execution_results['error']}")
                            print("------------------------------\n")

                            # Send execution feedback to the AI
                            chat.send_message(f"[System Execution Feedback] Python run Success: {execution_results['success']}, Output: {execution_results['output']}, Error: {execution_results['error']}")

                elif action == "use_skill":
                    if not skill_name:
                        print("[System Error: AI requested 'use_skill' but provided no skill_name]")
                        chat.send_message("[System Error: You must provide a valid skill_name when using the 'use_skill' action.]")
                        continue

                    print(f"[System: Invoking Cerebellum Skill -> {skill_name}]")
                    skill_path = os.path.join("cerebellum", f"{skill_name}.py")
                    
                    if not os.path.exists(skill_path):
                        error_msg = f"Skill file {skill_path} does not exist."
                        print(f"[System Error: {error_msg}]")
                        chat.send_message(f"[System Execution Feedback] Failed to execute skill. Error: {error_msg}")
                        continue

                    try:
                        # Dynamically load the specific skill module
                        spec = importlib.util.spec_from_file_location(skill_name, skill_path)
                        skill_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(skill_module)

                        # Ensure kwargs is a dictionary
                        kwargs = skill_kwargs if isinstance(skill_kwargs, dict) else {}
                        
                        # Fire the motor function with unpacked arguments
                        result_data = skill_module.execute(**kwargs)

                        # Print the result for the user
                        result_msg = result_data.get('message', 'Executed with no message returned.')
                        success_flag = result_data.get('success', False)
                        print(f"Skill Result [{success_flag}]: {result_msg}\n")

                        # Send the feeling back to the brain
                        chat.send_message(f"[System Execution Feedback] Skill '{skill_name}' executed. Success: {success_flag}, Message: {result_msg}")

                    except Exception as e:
                        print(f"[System Error: Failed to execute skill '{skill_name}': {e}]\n")
                        chat.send_message(f"[System Execution Feedback] Skill '{skill_name}' crashed. Error: {str(e)}")

                elif action == "chat":
                    # Just chat, do nothing else
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