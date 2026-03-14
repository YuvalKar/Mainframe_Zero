import os
import ast # <-- Safe parsing library
import importlib.util

################################### 
def execute_single_action(session_context: dict, action_name: str, action_data: dict) -> str:    
    """
    Locates the action file and executes it dynamically. 
    Checks app-specific directories first, then falls back to core directories.
    Returns the execution result as a string (no direct prints).
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
        return f"Action '{action_name}': Failed (Not Found in any known directory)"
        
    try:
        # 3. Dynamically load and execute the module
        spec = importlib.util.spec_from_file_location(action_name, target_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        res = module.execute(**action_data)
        return f"Action '{action_name}': {res}"
    except Exception as ex:
        return f"Action '{action_name}': Execution failed - {str(ex)}"
    
############################################
def execute_direct(action_name: str, action_data: dict, session_context: dict) -> dict:
    """
    Sister function to execute_single_action.
    Executes a sense/skill and returns the RAW dictionary result.
    Perfect for UI requests via WebSocket.
    """
    target_path = None

    # 1. Check if there's an active app based on current attention
    # Extract app name from the session
    if session_context is None:
        app_name = None
    else:
        active_attention = session_context.get("active_attention")
        app_name = active_attention.get("required_app") if active_attention else None

    # 2. Define the search paths (App specific first, then core)
    search_paths = []
    if app_name:
        search_paths.extend([
            os.path.join("apps", app_name, "cerebellum"),
            os.path.join("apps", app_name, "senses"),
        ])

    search_paths.extend(["cerebellum", "senses"])

    # 3. Search for the action file
    for base_path in search_paths:
        potential_path = os.path.join(base_path, f"{action_name}.py")
        if os.path.exists(potential_path):
            target_path = potential_path
            break 

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
                
                # Save the description or a fallback message
                available_actions[action_name] = description.strip() if description else 'No description provided.'
                
            except Exception as e:
                available_actions[action_name] = f'Error parsing description safely: {e}'

    return available_actions