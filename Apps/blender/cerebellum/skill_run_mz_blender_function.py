"""
NAME: skill_run_mz_blender_function
DESCRIPTION: Executes a predefined function from the mz_blender package directly inside Blender.

INPUTS:
    module_path (str): The Python dot-notation path to the module (e.g., 'mz_blender.actions.io_operations').
    function_name (str): The name of the function to execute (e.g., 'import_fbx').
    kwargs (dict): A dictionary of arguments to pass to the function. Use an empty dictionary {} if no arguments are needed.

OUTPUT:
    dict: A dictionary containing 'success' (bool), 'message' (str), and optionally 'data' (any).
"""
import sys
import os
import json

# Get the absolute path of the parent directory (blender)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Add the parent directory to Python's path so it can find 'blender_side'
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from blender_side import blender_bridge

def execute(module_path: str, function_name: str, kwargs: dict) -> dict:
    
    # Convert kwargs to a JSON string so we can safely inject it into the f-string
    # without worrying about single/double quote conflicts in Python
    kwargs_json = json.dumps(kwargs)
    
    # The scripts path to be added to sys.path inside Blender
    scripts_path = r"C:\Users\yuval\Documents\NBAYA_projects\Mainframe_Zero\apps\blender\blender_side"

    # Construct the python script to run inside Blender
    blender_script = f"""
import sys
import json
import importlib

# Add the main scripts path to Blender's environment
scripts_path = r"{scripts_path}"
if scripts_path not in sys.path:
    sys.path.append(scripts_path)

try:
    # Dynamically import the specific module using the provided path
    target_module = importlib.import_module("{module_path}")
    importlib.reload(target_module)
    
    # Fetch the specific function from the module
    func = getattr(target_module, "{function_name}")
    
    # Safely load the kwargs back into a dictionary inside Blender
    kwargs_dict = json.loads(r'''{kwargs_json}''')
    
    # Execute the function, unpacking the arguments dictionary
    data = func(**kwargs_dict)
    
    # We assume the new tools already return our standard dictionary 
    # (with 'success', 'message', etc.), so we just dump it to JSON
    result = json.dumps(data)
    
except Exception as e:
    # Catch any errors in loading or execution and return a safe error dict
    result = json.dumps({{"success": False, "message": f"Execution error in {{'{module_path}'}}: {{str(e)}}"}})
"""

    # Return the response from Blender via the bridge
    return blender_bridge.ask_blender(blender_script)