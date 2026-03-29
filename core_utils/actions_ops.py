import os
import ast # <-- Safe parsing library
import importlib.util
from core_utils.attention_ops import shift_attention
from database.db_wernicke_semantic_cortex import query_semantic_cortex
from senses.sense_get_installed_apps import execute as get_installed_apps

from llm_router import get_available_models

################################### 
def execute_single_action(session_context: dict, action_name: str, action_data: dict) -> str:    
    """
    Locates the action file and executes it dynamically. 
    Checks app-specific directories first, then falls back to core directories.
    Returns the execution result as a string (no direct prints).
    """
    # SYS action first, as it's a special case that doesn't require searching for a file
    if (action_name == 'get_API_descriptions'):
        res = get_API_descriptions(**action_data,  session_context=session_context)
        return f"Action '{action_name}': {res}"

    if (action_name == 'get_senantic_RAG'):
        res = get_senantic_RAG(**action_data,  session_context=session_context)
        return f"Action '{action_name}': {res}"

    target_path = fined_single_action(session_context, action_name)

    if not target_path:
        return f"Action '{action_name}': Failed (Not Found in any known directory)"
        
    try:
        # 3. Dynamically load and execute the module
        spec = importlib.util.spec_from_file_location(action_name, target_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        res = module.execute(**action_data)

        API_warning = ''
        if res.get("success") == False:
            API_description = get_API_descriptions(action_name,  session_context=session_context)
            API_description_data = API_description.get("data", {}).get(action_name, "No description available.")
            API_warning += f"USE THE API FOR '{action_name}' --> {API_description_data}': {res}"
            
        return f"Action '{action_name}': {res}" + API_warning
        
    except Exception as ex:
        return f"Action '{action_name}': Execution failed - {str(ex)}"
    
############################################
def execute_direct(action_name: str, action_data: dict, session_context: dict) -> dict:
    """
    Sister function to execute_single_action.
    Executes a sense/skill and returns the RAW dictionary result.
    Perfect for UI requests via WebSocket.
    """

    # SYS action first, as it's a special case that doesn't require searching for a file
    if (action_name == 'get_API_descriptions'):
        res = get_API_descriptions(**action_data,  session_context=session_context)
        return res

    if (action_name == 'get_senantic_RAG'):
        res = get_senantic_RAG(**action_data,  session_context=session_context)
        return f"Action '{action_name}': {res}"
        
    # Only from direct!
    if (action_name == 'switch_apps'):
        res = switch_apps(**action_data,  session_context=session_context)
        return res
    
    if (action_name == 'get_available_ai_models'):
        ai_models = get_available_models()
        return {
            "success": True,
            "message": f"Successfully retrieved settings for {len(ai_models)} AI models.",
            "data": ai_models,
        }
    
    # Back to main track
    target_path = fined_single_action(session_context, action_name)

    if not target_path:
        return {"success": False, "message": f"Action '{action_name}' Not Found."}
        
    try:
        # 4. Dynamically load and execute
        spec = importlib.util.spec_from_file_location(action_name, target_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 5. Return the raw data directly (No string wrapping!)
        return module.execute(**action_data)
        
    except Exception as ex:
        return {"success": False, "message": f"Execution failed: {str(ex)}"}
    

####################################
def get_available_actions(directory_path: str) -> dict:
    """
    Scans a specified directory for Python modules and extracts their names and docstrings safely.
    """
    available_actions = {}
    
    # Check if the provided directory exists
    if not os.path.isdir(directory_path):
        print(f"Warning: Directory path '{directory_path}' not found.")
        return available_actions

    for filename in os.listdir(directory_path):
        # Process only Python files and ignore the __init__.py file
        if filename.endswith(".py") and filename != "__init__.py":
            action_name = filename[:-3]  # Remove .py extension
            file_path = os.path.join(directory_path, filename)

            try:
                # Read the file purely as text
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                # Parse the abstract syntax tree SAFELY (no execution)
                parsed_tree = ast.parse(file_content)
                
                # Extract the module docstring
                description = ast.get_docstring(parsed_tree)

                # take only the NAME add DESCRIPTION (first 2 lines), ignore the rest of the docstring if it has multiple lines
                if description:
                    description_lines = description.strip().splitlines()
                    description = "\n".join(description_lines[:2])  # Keep only the first 2 lines of the docstring 
                                
                # Save the description or a fallback message
                available_actions[action_name] = description.strip() if description else 'No description provided.'
                
            except Exception as e:
                available_actions[action_name] = f'Error parsing description safely: {e}'

    return available_actions

#######################################################
def get_senantic_RAG(task_description: str, session_context: dict, limit: int = 5) -> dict:
    
    active_attention = session_context.get("active_attention")

    app_name = active_attention.get("required_app") if active_attention else None
    
    if not app_name:
        return {
            "success": False, 
            "message": "No active app found in session context. Cannot perform semantic RAG query without an app context."
        }

    apps = get_installed_apps()

    semantics = []

    if apps["success"]:
        apps = apps["data"]
        if app_name in apps:
            if "semantics" in apps[app_name]:
                semantics = apps[app_name]["semantics"]

    # Input validation
    if not task_description or not semantics:
        return {
            "success": False, 
            "message": "Task_description and app semantics are required."
        }
        
    try:
        # Ask the database using the updated function that accepts a list of semantics
        results = query_semantic_cortex(
            user_query=task_description, 
            semantics=semantics, 
            limit=limit
        )
        
        # Check if we got any hits
        if results:
            return {
                "success": True, 
                "message": f"Found {len(results)} relevant resoults in contexts: {app_name} - {semantics}.", 
                "data": results
            }
        else:
            return {
                "success": True, 
                "message": f"No relevant resoults found for this task in the specified contexts: {app_name} - {semantics}.", 
                "data": []
            }
            
    except Exception as e:
        # Catch errors gracefully so the AI doesn't crash the main loop
        return {
            "success": False, 
            "message": f"Failed to query Wernicke Cortex: {str(e)}"
        }

#######################################################
def get_API_descriptions(action_names: list, session_context: dict) -> dict:

    if not isinstance(action_names, list) or not all(isinstance(name, str) for name in action_names):
        return {"success": False, "message": "Invalid input: 'action_names' must be a list of strings."}
    
    descriptions = {}
    
    for action_name in action_names:
        action_path = fined_single_action(session_context, action_name)
        description = get_detailed_actions(action_path)
        descriptions[action_name] = description

    return {
        "success": True,
        "message": f"Successfully retrieved API descriptions for {len(descriptions)} actions. You may call them directly using their names.",
        "data": descriptions
    }

#######################################################
def switch_apps(app_name: str, session_context: dict) -> dict:

    # Get current attention
    active_attention = session_context.get("active_attention")

    # Get app from attention, If we are on the requested app already, do nothin
    if active_attention.get("required_app", None) == app_name:
        return {"success": True, "message": f"Already on app '{app_name}'.", "data": {}}

    # make sure the app is a valid app and we have the folder for it
    if not os.path.exists(os.path.join("apps", app_name)):
        return {"success": False, "message": f"App '{app_name}' not found.", "data": {}}

    # if all is OK Switch attention to new app
    new_focus = {}
    shift_attention(session_context, new_focus, app_name=app_name)

    return {
        "success": True,
        "message": f"Successfully switched to app '{app_name}'.",
        "data": {}
    }

#######################################################
def get_detailed_actions(action_path: str) -> dict:
    """
    returns a specific action full docstring
    """
    try:
        # Read the file purely as text
        with open(action_path, 'r', encoding='utf-8') as f:
            file_content = f.read()

        # Parse the abstract syntax tree SAFELY (no execution)
        parsed_tree = ast.parse(file_content)
        
        # Extract the module docstring
        description = ast.get_docstring(parsed_tree)

        # return the full docstring or a fallback message
        return description.strip() if description else 'No docstring provided.'
        
    except Exception as e:
        return f'Error parsing docstring safely: {e}'

##########################################
def fined_single_action(session_context: dict, action_name: str) -> str:    
    """
    Locates the action file and returns its full path.
    Checks app-specific directories first, then falls back to core directories.
    """
    target_path = None

    # Extract app name from the session
    active_attention = session_context.get("active_attention")
    app_name = active_attention.get("required_app") if active_attention else None

    # 1. Define the possible directory paths to search
    search_paths = []

    # App-specific paths get priority (specialized skills over general ones)
    if app_name:
        search_paths.extend([
            os.path.join("apps", app_name, "cerebellum"),
            os.path.join("apps", app_name, "senses"),
            # os.path.join("apps", app_name, "hippocampus")
        ])

    # Core paths as fallback
    search_paths.extend([
        "cerebellum",
        "senses",
        # "hippocampus"
    ])

    # 2. Search for the action file in the defined paths
    for base_path in search_paths:
        potential_path = os.path.join(base_path, f"{action_name}.py")
        if os.path.exists(potential_path):
            target_path = potential_path
            break # Found the file, stop searching

    if not target_path:
        print(f"Action '{action_name}': Failed (Not Found in any known directory)")
    
    return target_path