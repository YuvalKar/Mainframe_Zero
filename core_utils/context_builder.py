import json
import os
import re

# Import utility functions
from core_utils.actions_ops import get_available_actions

# Import updated attention ops
from core_utils.attention_ops import update_session_attention
from database.db_chat_history import get_recent_chat_history
from senses.sense_get_installed_apps import execute as get_installed_apps

from core_utils.hud_streamer import send_hud_error, send_hud_text


from jinja2 import Template
import os
from jinja2 import Environment, FileSystemLoader

#########################################
def get_system_prompt() -> str:
    try:
        with open("system_prompt.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        send_hud_error("CONTEXT", "system_prompt.md not found", code=12026)
        print("[Core Warning: system_prompt.md not found]")
        return "You are a helpful AI."

#########################################
def format_attention_to_prompt(session_context: dict) -> str:
    """
    Reads the updated attention from the session and formats it 
    into a clear string for the AI prompt.
    """
    active_attention = session_context.get("active_attention")
    if not active_attention or "working_files" not in active_attention:
        return ""

    enriched_section = "\n\n--- Context & Attached Files ---\n"
    working_files = active_attention["working_files"]

    for path, data in working_files.items():
        prefix = "[ACTIVE DOCUMENT]" if data.get("is_active") else "[CONTEXT FILE]"
        status_note = ""
        
        if data.get("status") == "pending_worker":
            status_note = "(Note: Summary is being processed, showing preview)\n"

        enriched_section += f"\n{prefix}: {path}\n"
        if status_note:
            enriched_section += status_note
            
        enriched_section += f"{data.get('long_summary', 'No content available.')}\n"
        enriched_section += "-----------------\n"

    # Add highlighted text if exists in client_context
    client_context = session_context.get("client_context", {})
    selected_text = client_context.get("selectedText")
    if selected_text:
        enriched_section += f"\n>>> USER HIGHLIGHTED TEXT <<<\n{selected_text}\n>>> END HIGHLIGHT <<<\n"

    enriched_section += "---------- END OF CONTEXT ----------\n\n"
    return enriched_section

#########################################
def enrich_prompt(session_context: dict, user_input: str) -> str:
    enriched_prompt = ""
    session_id = session_context.get("session_id")
    
    # 1. Fetch Recent History
    history = get_recent_chat_history(session_id, limit=5)
    if history:
        enriched_prompt += "[System Context: Recent Conversation History]\n"
        for turn in history:
            enriched_prompt += f"User: {turn['user']}\n"
            if turn.get('actions'):
                enriched_prompt += "System Actions Taken:\n"
                for act in turn['actions']:
                    enriched_prompt += f"- [{act['action']}]: {act['result']}\n"
            enriched_prompt += f"AI: {turn['ai']}\n"
        enriched_prompt += "-----------------------------------\n\n"

    # 2. Extract context info from Input and UI
    # Find files tagged with @
    mentioned_files = re.findall(r'@([\w\.\-\/\\]+)', user_input)
    
    # Extract UI context
    client_context = session_context.get("client_context", {})
    active_doc = client_context.get("activeDocument")
    attention_shelf = client_context.get("attentionShelf", [])

    # 3. Update the centralized Attention System
    # This handles DB checks, mtime, and background workers
    update_session_attention(
        session_context, 
        active_file=active_doc, 
        context_files=list(set(mentioned_files + attention_shelf))
    )

    # 4. Inject the formatted attention into the prompt
    enriched_prompt += f"Current User Input: {user_input}\n"
    enriched_prompt += format_attention_to_prompt(session_context)

    # 5. Inject Available Actions (Skills & Senses)
    active_attention = session_context.get("active_attention")
    app_name = active_attention.get("required_app") if active_attention else None

    # Get skills
    current_skills = get_available_actions("cerebellum")
    if app_name:
        app_skills_path = os.path.join("apps", app_name, "cerebellum")
        current_skills.update(get_available_actions(app_skills_path)) 

    enriched_prompt += "\n\n[System Context: Available Actions]\n"
    for name, desc in current_skills.items():
        enriched_prompt += f"- Action Name: '{name}'\n {desc}\n\n"
    
    # Get senses
    current_senses = get_available_actions("senses")
    if app_name:
        app_senses_path = os.path.join("apps", app_name, "senses")
        current_senses.update(get_available_actions(app_senses_path))

    for name, desc in current_senses.items():
        enriched_prompt += f"- Action Name: '{name}' \n  {desc}\n\n"

    # Inject Special SYS Action
    get_API_descriptions = """
    - Before using these actions, call 'get_API_descriptions' with names of the actions you plan to execute.
    Once You got the API description for an action, you can call the action directly by its name and passing the required parameters.

    NAME: get_API_descriptions
    - INPUT: action_names (list): A list of action names (SKILLS / SENSES) for which to retrieve their APIdescriptions.
    """
    enriched_prompt += "\n\n[System Context: Special SYS Action - get_API_descriptions]\n"
    enriched_prompt += get_API_descriptions + "\n\n"

    if app_name:
        # if avaliable semantics - search by free text to get interface, include RAG query for relevant functions in the semantic cortex
        apps = get_installed_apps()
        if apps["success"]:
            apps = apps["data"]
            if app_name in apps:
                if "semantics" in apps[app_name]:
                    get_senantic_RAG = """For {app_name} you can RAG Query the Semantic Cortex (the AI's long-term memory) to find relevant tools, API documentation, or skills for a given task.
                        call it by using the action 'get_senantic_RAG' with the following inputs:

                        INPUTS:
                        - task_description (str): A natural language description of what you are trying to achieve (e.g., 'How do I import an FBX file?').
                        - limit (int, optional): The maximum number of results to return. Default is 5.

                         WHEN TO USE:
                        - When you need to find specific tools or API documentation to accomplish a task.
                        - Before writing new code or executing an action, to check if a relevant functions already exists in the requested contexts.
                        - When you are unsure how to interact with a specific application (like Blender or UEFN).
                    """.format(app_name = app_name)

                    enriched_prompt += "\n\n[System Context: Special SYS Action - get_senantic_RAG]\n"
                    enriched_prompt += get_senantic_RAG + "\n\n"


    # -------------------------------
    app_role_context = "app_role_context" # TODO: later



    # TODO: optimise, read only once
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
    templates_dir = os.path.join(base_dir, 'prompt_templates')
    
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template('main_prompt.j2')

    conversation_history = json.dumps(history, indent=2, sort_keys=False)
    context_data = session_context.get("client_context", {})

    # Render the template with all our gathered data
    enriched_prompt_with_template = template.render(
            app_role_context=app_role_context,
            available_actions=current_skills,
            context_data=context_data,
            conversation_history=conversation_history,
            user_input=user_input,
        )
    
    # -------------------------------

    # keep the prompt in temp file for debugging in .logs folder
    with open("./.logs/temp_enriched_prompt.md", "w", encoding="utf-8") as f:
        f.write(enriched_prompt_with_template)

    return enriched_prompt_with_template

#########################################