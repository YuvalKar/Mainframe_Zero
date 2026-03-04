import os
import ast
import json
import subprocess
from google import genai
from google.genai import types
from dotenv import load_dotenv
import re
from senses.python_runner_sense import run_and_sense
from core_utils.skill_loader import get_available_skills # <-- [System: Implemented the new Library mechanism]

###################################################################################
def enrich_prompt_with_files(user_input: str) -> str:
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
    try:
        ast.parse(code_string)
        print("[System: QA Passed - The output is valid Python syntax.]")
        return True
    except SyntaxError as err:
        return False

#################################################################
def save_and_execute(code_string: str, target_filename: str = None):
    filename = target_filename if target_filename else "generated_script.py"
    user_decision = input(f"Save to {filename} and run? (y/n): ")

    if user_decision.lower() == 'y':
        with open(filename, "w", encoding="utf-8") as file:
            file.write(code_string)

        print(f"\n[System: Code saved to {filename}. Executing now...]\n")
        result_data = run_and_sense(filename)
        return result_data 
    return None 

#################################################################
def save_markdown(content_string: str, target_filename: str = None):
    filename = target_filename if target_filename else "output.md"
    with open(filename, "w", encoding="utf-8") as file:
        file.write(content_string)
    print(f"\n[System: Markdown content cleanly saved to {filename}]\n")


###############################################################

load_dotenv()
client = genai.Client()

def terminal_chat():
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
                response_mime_type="application/json",
            )
        )

    chat = create_new_chat()

    print("\n================================================")
    print(" Welcome to Mainframe Zero Terminal (v3 - Cerebellum Aware)")
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
            # dynamically load skills at the start of every turn
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
                ai_data = json.loads(response.text)

                thought_process = ai_data.get("thought_process", "")
                action = ai_data.get("action", "chat")
                content = ai_data.get("content", "")
                target_filename = ai_data.get("target_filename")

                print(f"\n[AI Thought Process]: {thought_process}")
                print(f"\n--- AI Output (Action: {action}) ---")
                print(content)
                print("-----------------\n")

                if action == "python":
                    if passes_syntax_qa(content):
                        execution_results = save_and_execute(content, target_filename)
                        if execution_results: 
                            print("\n--- Python Execution Results ---")
                            print(f"Success: {execution_results['success']}")
                            print(f"Output:\n{execution_results['output']}")
                            print(f"Error:\n{execution_results['error']}")
                            print("------------------------------\n")

                            chat.send_message(f"[System Execution Feedback] Success: {execution_results['success']}, Output: {execution_results['output']}, Error: {execution_results['error']}")

                elif action == "markdown":
                    save_markdown(content, target_filename)

                elif action == "chat":
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