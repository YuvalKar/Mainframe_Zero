import os
import re

# Import utility functions
from core_utils.actions_ops import get_available_actions

# Import memory DB functions for short-term history
from database.db_chat_history import get_recent_chat_history

#########################################
def get_system_prompt() -> str:
    # Load system rules from file for each stateless request
    try:
        with open("system_prompt.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print("[Core Warning: system_prompt.md not found]")
        return "You are a helpful AI."
    

#########################################
def enrich_prompt(session_context: dict, user_input: str) -> str:
    
    enriched_prompt = ""
    
    # Extract the session_id safely from the context dictionary
    session_id = session_context.get("session_id")
    
    # 1. Fetch Recent History directly from PostgreSQL
    history = get_recent_chat_history(session_id, limit=5)
    if history:
        enriched_prompt += "[System Context: Recent Conversation History]\n"
        for turn in history:
            enriched_prompt += f"User: {turn['user']}\n"
            
            # Print actions and their results if they occurred during this turn
            if turn.get('actions'):
                enriched_prompt += "System Actions Taken:\n"
                for act in turn['actions']:
                    enriched_prompt += f"- [{act['action']}]: {act['result']}\n"
                    
            enriched_prompt += f"AI: {turn['ai']}\n"
        enriched_prompt += "-----------------------------------\n\n"

    # 1.1 Add the current user input at the end of the history to ensure it's fresh in context
    enriched_prompt += f"Current User Input: {user_input}\n"
    
    # 2. add current user input
    file_matches = re.findall(r'@([\w\.\-\/\\]+)', user_input)
    
    # 3. If there are file references, read their content and inject into the prompt
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
    
    # 4. Inject Available Actions (Skills from Cerebellum)

    #4.1 Get app name
    active_attention = session_context.get("active_attention")
    app_name = active_attention.get("required_app") if active_attention else None

    # 4.2 Get core skills and merge with app-specific skills if applicable
    current_skills = get_available_actions("cerebellum") # Scan core directory
    
    # 4.3 Get app-specific skills and merge with app-specific skills if applicable
    if app_name:
        # Scan app-specific directory and merge into current_skills
        app_skills_path = os.path.join("apps", app_name, "cerebellum")
        app_skills = get_available_actions(app_skills_path)
        current_skills.update(app_skills) 

    enriched_prompt += "\n\n[System Context: Available Actions in Cerebellum]\n"
    if current_skills:
        for name, desc in current_skills.items():
            enriched_prompt += f"- Action Name: '{name}' (Skill)\n  API: {desc}\n\n"
    else:
        enriched_prompt += "No skills available.\n\n"
    
    # 5. Inject Available Senses
    current_senses = get_available_actions("senses") # Scan core directory
    
    # 5.1 Get app-specific senses and merge with core senses if applicable
    if app_name:
        # Scan app-specific directory and merge into current_senses
        app_senses_path = os.path.join("apps", app_name, "senses")
        app_senses = get_available_actions(app_senses_path)
        current_senses.update(app_senses)

    enriched_prompt += "[System Context: Available Senses]\n"
    if current_senses:
        for name, desc in current_senses.items():
            enriched_prompt += f"- Action Name: '{name}' (Sense)\n  API: {desc}\n\n"
    else:
        enriched_prompt += "No senses available.\n\n"

    return enriched_prompt