"""
NAME: sense_uefn_get_selected_data
DESCRIPTION: Detects all currently selected objects (actors) in UEFN and retrieves their details.

WHEN TO USE:
- When you need to know which objects the user is currently selecting in the UEFN level.

INPUTS:
- None required.

OUTPUT: 
dict: A dictionary containing the status of the operation and the retrieved data.
"""

import sys
import os

# Dynamically add the parent directory to the path so we can import uefn_bridge
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from uefn_side import uefn_bridge

def execute() -> dict:
    uefn_script = """
import sys
import json
import importlib

# Add the UEFN side scripts path (Update this if your path differs)
scripts_path = r"C:\\Users\\yuval\\Documents\\NBAYA_projects\\Mainframe_Zero\\apps\\uefn\\uefn_side"
if scripts_path not in sys.path:
    sys.path.append(scripts_path)

import uefn_get_selected_data
importlib.reload(uefn_get_selected_data)

result = json.dumps(uefn_get_selected_data.get_selected_data())
"""
    return uefn_bridge.ask_uefn(uefn_script)