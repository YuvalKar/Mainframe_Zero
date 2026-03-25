"""
NAME: skill_uefn_run_script
DESCRIPTION: Get a python sctipt as string of text and run a function in it directly in and imidiatly in UEFN editor 

WHEN TO USE:
- When you need to run a python function in UEFN editor directly
    - the function can not get params, it need to be coded in the script itself
- When you need to make actions in UEFN editor or to collect data from UEFN editor

INPUTS:
    script_text (str): The text content string to be used as python script.
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

# Get the absolute path of the parent directory (blender_for_uefn)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Add the parent directory to Python's path so it can find 'uefn_side'
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from uefn_side import uefn_bridge


def execute(script_text: str, function_name: str) -> dict:

    # make sure "import unreal" is included in the script
    if "import unreal" not in script_text:
        script_text = "import unreal\n" + script_text

    # Save the script to temp file (never deleted)
    scripts_path = r"C:\\Users\\yuval\\Documents\\NBAYA_projects\\Mainframe_Zero\\apps\\blender_for_uefn\\uefn_side\\.tmp"

    # create name for the script, the function_name + timestamp
    module_name = f"uefn_script_{function_name}_{int(time.time())}"
    target_filename = f"{module_name}.py"

    # save the file
    with open(os.path.join(scripts_path, target_filename), "w") as file:
        file.write(script_text)

    # run the script
    uefn_script = f"""
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

    return uefn_bridge.ask_uefn(uefn_script)
