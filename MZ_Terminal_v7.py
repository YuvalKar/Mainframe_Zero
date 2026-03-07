import os
import json
import importlib.util
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Import Sense and utility functions
from core_utils.actions_scanner import get_available_actions

###################################################################################
def enrich_prompt(user_input: str) -> str:
    """
    Orchestrates the context injection: Files (@), Skills, and Senses dynamically.
    """
    # 1. Handle @file attachments
    file_matches = re.findall(r'@([\w\.\-\/]+)', user_input)
    enriched_prompt = user_input
    
    if file_matches:
        enriched_prompt += "\n\n--- Attached Files Context ---\n"
        for filename in file_matches:
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        enriched_prompt += f"\n[Content of {filename}]:\n{f.read()}\n"
                    print(f"[System: Contextualized '{filename}']")
                except Exception as e:
                    print(f"[System Error: Could not read '{filename}': {e}]")
        enriched_prompt += "------------------------------\n"

    # 2. Inject Available Actions (Skills from Cerebellum)
    # Using the new generic get_available_actions function
    current_skills = get_available_actions("cerebellum")
    enriched_prompt += "\n\n[System Context: Available Actions in Cerebellum]\n"
    if current_skills:
        for name, desc in current_skills.items():
            enriched_prompt += f"- Action Name: '{name}' (Skill)\n  API: {desc}\n\n"
    else:
        enriched_prompt += "No skills available.\n\n"
    
    # 3. Inject Available Senses (from senses directory)
    # Using the same generic function for the senses folder
    current_senses = get_available_actions("senses")
    enriched_prompt += "[System Context: Available Senses]\n"
    if current_senses:
        for name, desc in current_senses.items():
            enriched_prompt += f"- Action Name: '{name}' (Sense)\n  API: {desc}\n\n"
    else:
        enriched_prompt += "No senses available.\n\n"
    
    return enriched_prompt

###############################################################################
load_dotenv()
client = genai.Client()

def terminal_chat():
    # Load system rules from the updated markdown file
    try:
        with open("system_prompt.md", "r", encoding="utf-8") as f:
            system_rules = f.read()
    except FileNotFoundError:
        print("[System Error: system_prompt.md not found!]")
        return

    def create_new_chat():
        print("\n[System: Resetting Mainframe Zero Brain...]")
        return client.chats.create(
            model='gemini-2.5-flash',
            config=types.GenerateContentConfig(
                system_instruction=system_rules,
                temperature=0.1,
                response_mime_type="application/json",
            )
        )

    chat = create_new_chat()

    print("\n========================================================")
    print(" Mainframe Zero Terminal (v7 - Multi-Action Orchestrator)")
    print("========================================================\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() in ['exit', 'quit']: break
        if user_input.lower() == 'reset':
            chat = create_new_chat()
            continue
        if not user_input.strip(): continue

        try:
            # Step 1: Enrich the user prompt with system context
            final_prompt = enrich_prompt(user_input)

            # Step 2: Get Brain's decision
            response = chat.send_message(final_prompt)
            ai_data = json.loads(response.text)

            # Extract top-level fields
            thought = ai_data.get("thought_process", "")
            action_type = ai_data.get("action", "chat")
            chat_text = ai_data.get("chat")
            actions_list = ai_data.get("act", [])

            print(f"\n[AI Thought]: {thought}")
            
            if chat_text:
                print(f"\n[AI Chat]: {chat_text}")

            # Step 3: Action Router (Iterating over the 'act' list)
            if action_type == "act" and isinstance(actions_list, list):
                execution_summary = []

                for act_item in actions_list:
                    action_name = act_item.get("name")
                    action_data = act_item.get("data", {})

                    print(f"\n[System: Initiating Action -> {action_name}]")
                    
                    # --- BRANCH A: Built-in Senses ---
                    if action_name == "sense_python_function_execution":
                        result = sense_python_function_execution(**action_data)
                        print(f"Sense Outcome: {result}")
                        execution_summary.append(f"Sense '{action_name}': {result}")

                    # --- BRANCH B: Dynamic Skills (Cerebellum) ---
                    else:
                        skill_path = os.path.join("cerebellum", f"{action_name}.py")
                        if os.path.exists(skill_path):
                            # Human-in-the-loop confirmation
                            confirm = input(f"Confirm execution of Skill '{action_name}'? (y/n): ")
                            if confirm.lower() == 'y':
                                spec = importlib.util.spec_from_file_location(action_name, skill_path)
                                skill_module = importlib.util.module_from_spec(spec)
                                spec.loader.exec_module(skill_module)
                                
                                res = skill_module.execute(**action_data)
                                print(f"Skill Outcome: {res}")
                                execution_summary.append(f"Skill '{action_name}': {res}")
                            else:
                                execution_summary.append(f"Skill '{action_name}': Aborted by user.")
                        else:
                            err = f"Action '{action_name}' not found in Cerebellum or Senses."
                            print(f"[Error: {err}]")
                            execution_summary.append(f"Action '{action_name}': Failed (Not Found)")

                # Step 4: Send the combined "Sensation" back to the brain
                feedback_msg = "[System Sensory Feedback]\n" + "\n".join(execution_summary)
                chat.send_message(feedback_msg)

        except Exception as e:
            print(f"\n[System Error during execution: {e}]\n")

if __name__ == "__main__":
    terminal_chat()