"""
NAME: skill_blender_run_script
DESCRIPTION: Get a python sctipt as string of text and run a function in it directly in and imidiatly in Blender 

WHEN TO USE:
- When you need to run a python function in blender directly
    - the function can not get params, it need to be coded in the script itself
- When you need to make actions in Blender or to collect data from Blender

INPUTS:
    script_text (str): The text content string to be used as python script. Make sure you include all needed modules and imports in the script text. The script will be saved as a temporary .py file and then executed in Blender.
    function_name (str): The name of the function to be executed from the script provided.

OUTPUT: 
dict: A dictionary containing the status of the operation and the retrieved data.
- 'success' (bool): True if objects were selected and data retrieved successfully, False otherwise.
- 'message' (str): A descriptive message indicating the outcome and the number of objects found.
- 'data': the return data suplied by the function.
"""
import sys
import os
import time

# Get the absolute path of the parent directory (blender)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Add the parent directory to Python's path so it can find 'blender_side'
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from blender_side import blender_bridge


def execute(script_text: str, function_name: str) -> dict:

    # make sure "import bpy" is included in the script
    if "import bpy" not in script_text:
        script_text = "import bpy\n" + script_text

    # Save the script to temp file (never deleted)
    scripts_path = r"C:\\Users\\yuval\\Documents\\NBAYA_projects\\Mainframe_Zero\\apps\\blender\\blender_side\\.tmp"

    # create name for the script, the function_name + timestamp
    module_name = f"blender_script_{function_name}_{int(time.time())}"
    target_filename = f"{module_name}.py"

    # save the file
    with open(os.path.join(scripts_path, target_filename), "w") as file:
        file.write(script_text)

    # run the script
    blender_script = f"""
import sys
import json
import importlib

# add lib path
scripts_path = r"{scripts_path}"
if scripts_path not in sys.path:
    sys.path.append(scripts_path)

import {module_name}
importlib.reload({module_name})

try:
    data = {module_name}.{function_name}()
    result = json.dumps({{"success": True, "message": "Code executed successfully.", "data": data}})
except Exception as e:
    result = json.dumps({{"success": False, "message": f"Execution error: {{e}}", "data": None}})
    """

    return blender_bridge.ask_blender(blender_script)
