"""
NAME: sense_blender_get_selected_data
DESCRIPTION: Detects all currently selected objects in Blender and retrieves their details.

WHEN TO USE:
- When you need to know which objects the user is currently working on.
- Before applying modifiers, materials, or transformations to ensure you have the correct targets.

INPUTS:
- None required.

OUTPUT: 
dict: A dictionary containing the status of the operation and the retrieved data.
- 'success' (bool): True if objects were selected and data retrieved successfully, False otherwise.
- 'message' (str): A descriptive message indicating the outcome and the number of objects found.
- 'data' (list): A list of dictionaries, where each dictionary contains the properties (name, type, location, rotation, scale, dimensions) of a selected object.
"""

import sys
import os

# Get the absolute path of the parent directory (blender_for_uefn)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Add the parent directory to Python's path so it can find 'blender_side'
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from blender_side import blender_bridge

def execute() -> dict:
    blender_script = """
import sys
import json
import importlib

# add lib path
scripts_path = r"C:\\Users\\yuval\\Documents\\NBAYA_projects\\Mainframe_Zero\\apps\\blender_for_uefn\\blender_side"
if scripts_path not in sys.path:
    sys.path.append(scripts_path)

import get_selected_data
importlib.reload(get_selected_data)

result = json.dumps(get_selected_data.get_selected_data())
"""
    return blender_bridge.ask_blender(blender_script)