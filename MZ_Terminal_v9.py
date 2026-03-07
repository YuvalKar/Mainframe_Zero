import os
import json
import importlib.util
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Import utility functions
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
    current_skills = get_available_actions("cerebellum")
    enriched_prompt += "\n\n[System Context: Available Actions in Cerebellum]\n"
    if current_skills:
        for name, desc in current_skills.items():
            enriched_prompt += f"- Action Name: '{name}' (Skill)\n  API: {desc}\n\n"
    else:
        enriched_prompt += "No skills available.\n\n"
    
    # 3. Inject Available Senses (from senses directory)
    current_senses = get_available_actions("senses")
    enriched_prompt += "[System Context: Available Senses]\n"
    if current_senses:
        for name, desc in current_senses.items():
            enriched_prompt += f"- Action Name: '{name}' (Sense)\n  API: {desc}\n\n"
    else:
        enriched_prompt += "No senses available.\n\n"
        
    # 4. Inject Hippocampus actions (Memory)
    current_memory_actions = get_available_actions("hippocampus")
    enriched_prompt += "[System Context: Available Hippocampus Actions]\n"
    if current_memory_actions:
        for name, desc in current_memory_actions.items():
            enriched_prompt += f"- Action Name: '{name}' (Memory)\n  API: {desc}\n\n"
    else:
        enriched_prompt += "No memory actions available.\n\n"
    
    return enriched_prompt


###################################################################################
# (enrich_prompt function remains the same, assuming it's correctly written above)
# ... 

def execute_single_action(action_name: str, action_data: dict) -> str:
    """
    Locates the action file, requests user confirmation if it's an active 'Skill',
    and executes it dynamically. Returns the execution result as a string.
    """
    print(f"\n[System: Initiating Action -> {action_name}]")
    
    target_path = None
    is_active_skill = False
    
    # Dynamically find which directory the action belongs to
    if os.path.exists(os.path.join("cerebellum", f"{action_name}.py")):
        target_path = os.path.join("cerebellum", f"{action_name}.py")
        is_active_skill = True # Requires user confirmation
    elif os.path.exists(os.path.join("senses", f"{action_name}.py")):
        target_path = os.path.join("senses", f"{action_name}.py")
    elif os.path.exists(os.path.join("hippocampus", f"{action_name}.py")):
        target_path = os.path.join("hippocampus", f"{action_name}.py")

    if not target_path:
        err = f"Action '{action_name}' not found in any known directory."
        print(f"[Error: {err}]")
        return f"Action '{action_name}': Failed (Not Found)"

    # Ask for confirmation only for active skills (cerebellum)
    if is_active_skill:
        confirm = input(f"Confirm execution of Skill '{action_name}'? (y/n): ")
        if confirm.lower() != 'y':
            return f"Action '{action_name}': Aborted by user."
        
    try:
        # Dynamically load the module and call the standard 'execute' function
        spec = importlib.util.spec_from_file_location(action_name, target_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        res = module.execute(**action_data)
        print(f"Outcome: {res}")
        return f"Action '{action_name}': {res}"
    except Exception as ex:
        err = f"Execution failed: {str(ex)}"
        print(f"[Error: {err}]")
        return f"Action '{action_name}': {err}"


def run_agentic_loop(chat, current_prompt: str) -> None:
    """
    Runs the interaction loop with the AI. 
    Breaks when the AI chooses 'chat' or when the safety limit is reached.
    """
    loop_counter = 0
    max_loops = 3  # Safety limit to prevent infinite loops

    while True:
        loop_counter += 1
        if loop_counter > max_loops:
            print("\n[System Alert: Agent reached maximum allowed loops. Returning control to User.]")
            break

        try:
            # Send the prompt (either user input or sensory feedback) to the AI
            response = chat.send_message(current_prompt)
            ai_data = json.loads(response.text)
            
            # Extract fields
            thought = ai_data.get("thought_process", "")
            action_type = ai_data.get("action", "chat")
            chat_text = ai_data.get("chat")
            actions_list = ai_data.get("act", [])

            print(f"\n[AI Thought (Loop {loop_counter})]: {thought}")
            
            if chat_text:
                print(f"\n[AI Chat]: {chat_text}")

            # Exit Condition: If the AI just wants to chat or has no actions
            if action_type == "chat" or not actions_list:
                break

            # If we have actions, iterate and execute them
            execution_summary = []
            for act_item in actions_list:
                action_name = act_item.get("name")
                action_data = act_item.get("data", {})
                
                # Call our extracted sub-function
                result_string = execute_single_action(action_name, action_data)
                execution_summary.append(result_string)

            # Prepare the feedback for the next iteration of the inner loop
            if execution_summary:
                current_prompt = "[System Sensory Feedback]\n" + "\n".join(execution_summary)
            else:
                current_prompt = "[System: Actions resulted in no feedback.]"

        except json.JSONDecodeError:
            print(f"\n[System Error: Failed to parse AI response as JSON. Raw response:\n{response.text}]\n")
            break
        except Exception as e:
            print(f"\n[System Error during agentic loop: {e}]\n")
            break


###############################################################################
load_dotenv()
client = genai.Client()

def terminal_chat():
    """
    The main user-facing terminal loop.
    """
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
    print(" Mainframe Zero Terminal (v8 - Refactored Orchestrator)")
    print("========================================================\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() in ['exit', 'quit']: break
        if user_input.lower() == 'reset':
            chat = create_new_chat()
            continue
        if not user_input.strip(): continue

        # Step 1: Enrich the user prompt with system context
        final_prompt = enrich_prompt(user_input)

        # Step 2: Hand over control to the agentic loop
        run_agentic_loop(chat, final_prompt)

if __name__ == "__main__":
    terminal_chat()