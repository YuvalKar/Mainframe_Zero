import os
import re

# Import utility functions
from core_utils.actions_ops import get_available_actions

# Import memory DB functions for short-term history
from core_utils.attention_ops import create_attention
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
    
def sync_files_to_context(session_context: dict, file_matches:list) -> str:
    """
    This function takes a list of file matches (filenames extracted from user input) and enriches the prompt with their content or summaries.
    It also manages an "active_attention" in the session context to track these files and their metadata for future interactions. 
    """
    
    enriched_prompt = ""

    if file_matches:
        enriched_prompt += "\n\n--- Attached Files ---\n"
        
        # Safely initialize active_attention and working_files if they don't exist
        if "active_attention" not in session_context:
            session_context["active_attention"] = create_attention(name="Auto-Created Attention for File Syncing", required_app=None, tags=["file_sync"])
            
        active_attention = session_context["active_attention"]
        
        if "working_files" not in active_attention:
            active_attention["working_files"] = {}
            
        working_files = active_attention["working_files"]

        for filename in file_matches:
            if os.path.exists(filename):
                try:
                    # Get the current last modified time of the file
                    current_mtime = os.path.getmtime(filename)
                    file_data = working_files.get(filename)
                    
                    # Check if we have a valid long description and the file hasn't been modified
                    has_valid_summary = (
                        file_data is not None and 
                        file_data.get("last_modified") == current_mtime and 
                        file_data.get("long_description")
                    )

                    if has_valid_summary:
                        # Use the cached long description
                        enriched_prompt += f"\n[Summary of {filename}]:\n{file_data['long_description']}\n"
                        enriched_prompt += "-----------------\n"
                    else:
                        # File is new, modified, or missing a summary - read lines safely
                        with open(filename, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            
                        # Check if the file is longer than 20 lines
                        if len(lines) > 20:
                            # Take only the first 20 lines and join them back
                            preview_content = "".join(lines[:20])
                            enriched_prompt += f"\n[Content of {filename} (First 20 lines)]:\n{preview_content}\n...\n[Note: This is how the file starts. Full file is longer.]\n"
                        else:
                            # If it's 20 lines or shorter, just use the whole thing
                            full_content = "".join(lines)
                            enriched_prompt += f"\n[Content of {filename}]:\n{full_content}\n"
                            
                        enriched_prompt += "-----------------\n"
                            
                        # Register or update the file in working_files
                        working_files[filename] = {
                            "path": filename,
                            "last_modified": current_mtime,
                            "short_description": file_data.get("short_description", "") if file_data else "",
                            "long_description": file_data.get("long_description", "") if file_data else ""
                        }
                        
                except Exception as e:
                    # We return the error inside the prompt so the AI knows it failed
                    enriched_prompt += f"\n[System Error: Could not read/process '{filename}': {e}]\n"
                    
        enriched_prompt += "---------- END OF ATTACHED FILES ----------\n\n"

    return enriched_prompt

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

    # 2. Add the current user input at the end of the history to ensure it's fresh in context
    enriched_prompt += f"Current User Input: {user_input}\n"
    
    # 3. add Files mentioned in the user input (using regex to find file patterns like @filename.txt)
    file_matches = re.findall(r'@([\w\.\-\/\\]+)', user_input)
    enriched_prompt += sync_files_to_context(session_context, file_matches)
    
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

    enriched_prompt += "\n\n[System Context: Available Actions]\n"
    if current_skills:
        for name, desc in current_skills.items():
            enriched_prompt += f"- Action Name: '{name}'\n {desc}\n\n"
    
    # 5. Inject Available Senses
    current_senses = get_available_actions("senses") # Scan core directory
    
    # 5.1 Get app-specific senses and merge with core senses if applicable
    if app_name:
        # Scan app-specific directory and merge into current_senses
        app_senses_path = os.path.join("apps", app_name, "senses")
        app_senses = get_available_actions(app_senses_path)
        current_senses.update(app_senses)

    enriched_prompt += "\n"
    if current_senses:
        for name, desc in current_senses.items():
            enriched_prompt += f"- Action Name: '{name}' \n  {desc}\n\n"

    get_API_descriptions = """
    - Before using these actions, you must get the API descriptions for them, call 'get_API_descriptions' with names of the actions you plan to execute.
    Once You got the API description for an action, you can call the action directly by its name and passing the required parameters.

    NAME: get_API_descriptions
    - INPUT: action_names (list): A list of action names (SKILLS / SENSES) for which to retrieve their APIdescriptions.
    - OUTPUTS:
        - success (bool): Indicates whether the operation was successful.
        - message (str): A descriptive message about the operation's outcome.
        - descriptions: If successful, action names and their corresponding descriptions (docstrings). If fails, may be omitted or set to None.        
    """
    enriched_prompt += "\n\n[System Context: Special SYS Action - get_API_descriptions]\n"
    enriched_prompt += get_API_descriptions + "\n\n"

    return enriched_prompt