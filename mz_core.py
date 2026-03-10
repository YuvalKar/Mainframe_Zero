import os
import json
import importlib.util
import re

# Import utility functions
from core_utils.actions_scanner import get_available_actions

def enrich_prompt(user_input: str) -> str:
    """
    Orchestrates the context injection: Files (@), Skills, and Senses dynamically.
    Returns the enriched string without printing anything to the console.
    """
    file_matches = re.findall(r'@([\w\.\-\/]+)', user_input)
    enriched_prompt = user_input
    
    if file_matches:
        enriched_prompt += "\n\n--- Attached Files Context ---\n"
        for filename in file_matches:
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        enriched_prompt += f"\n[Content of {filename}]:\n{f.read()}\n"
                except Exception as e:
                    # We return the error inside the prompt so the AI knows it failed
                    enriched_prompt += f"\n[System Error: Could not read '{filename}': {e}]\n"
        enriched_prompt += "------------------------------\n"

    # Inject Available Actions (Skills from Cerebellum)
    current_skills = get_available_actions("cerebellum")
    enriched_prompt += "\n\n[System Context: Available Actions in Cerebellum]\n"
    if current_skills:
        for name, desc in current_skills.items():
            enriched_prompt += f"- Action Name: '{name}' (Skill)\n  API: {desc}\n\n"
    else:
        enriched_prompt += "No skills available.\n\n"
    
    # Inject Available Senses
    current_senses = get_available_actions("senses")
    enriched_prompt += "[System Context: Available Senses]\n"
    if current_senses:
        for name, desc in current_senses.items():
            enriched_prompt += f"- Action Name: '{name}' (Sense)\n  API: {desc}\n\n"
    else:
        enriched_prompt += "No senses available.\n\n"

    # Inject Hippocampus actions (Memory)
    # TBD - we might want to separate these out or handle them differently since they are more dynamic and might require a different approach to context injection. 
    # For now, we'll not activate it
    # 
    # current_memory_actions = get_available_actions("hippocampus")
    # enriched_prompt += "[System Context: Available Hippocampus Actions]\n"
    # if current_memory_actions:
    #     for name, desc in current_memory_actions.items():
    #         enriched_prompt += f"- Action Name: '{name}' (Memory)\n  API: {desc}\n\n"
    # else:
    #     enriched_prompt += "No memory actions available.\n\n"
    

    return enriched_prompt

################################### 
def execute_single_action(action_name: str, action_data: dict) -> str:
    """
    Locates the action file and executes it dynamically. 
    Returns the execution result as a string (no direct prints).
    """
    target_path = None
    
    if os.path.exists(os.path.join("cerebellum", f"{action_name}.py")):
        target_path = os.path.join("cerebellum", f"{action_name}.py")
    elif os.path.exists(os.path.join("senses", f"{action_name}.py")):
        target_path = os.path.join("senses", f"{action_name}.py")
    elif os.path.exists(os.path.join("hippocampus", f"{action_name}.py")):
        target_path = os.path.join("hippocampus", f"{action_name}.py")

    if not target_path:
        return f"Action '{action_name}': Failed (Not Found in any known directory)"
        
    try:
        spec = importlib.util.spec_from_file_location(action_name, target_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        res = module.execute(**action_data)
        return f"Action '{action_name}': {res}"
    except Exception as ex:
        return f"Action '{action_name}': Execution failed - {str(ex)}"

#########################################
def run_agentic_loop(chat, current_prompt: str) -> dict:
    """
    Runs the interaction loop with the AI. 
    Collects the execution history and returns it as a dictionary.
    """
    loop_counter = 0
    max_loops = 3 
    interaction_log = []

    while True:
        loop_counter += 1
        if loop_counter > max_loops:
            interaction_log.append({"type": "system", "content": "Agent reached maximum allowed loops."})
            break

        try:
            response = chat.send_message(current_prompt)
            ai_data = json.loads(response.text)
            
            thought = ai_data.get("thought_process", "")
            action_type = ai_data.get("action", "chat")
            chat_text = ai_data.get("chat")
            actions_list = ai_data.get("act", [])

            if thought:
                interaction_log.append({"type": "thought", "content": thought})
            if chat_text:
                interaction_log.append({"type": "chat", "content": chat_text})

            if action_type == "chat" or not actions_list:
                break

            execution_summary = []
            for act_item in actions_list:
                action_name = act_item.get("name")
                action_data = act_item.get("data", {})
                
                # We log that we are starting the action
                interaction_log.append({"type": "system", "content": f"Initiating Action -> {action_name}"})
                
                result_string = execute_single_action(action_name, action_data)
                execution_summary.append(result_string)
                
                interaction_log.append({"type": "action_result", "content": result_string})

            if execution_summary:
                current_prompt = "[System Sensory Feedback]\n" + "\n".join(execution_summary)
            else:
                current_prompt = "[System: Actions resulted in no feedback.]"

        except json.JSONDecodeError:
            err_msg = f"Failed to parse AI response as JSON. Raw response: {response.text}"
            interaction_log.append({"type": "error", "content": err_msg})
            break
        except Exception as e:
            interaction_log.append({"type": "error", "content": f"System Error during agentic loop: {str(e)}"})
            break
            
    return {"status": "completed", "log": interaction_log}