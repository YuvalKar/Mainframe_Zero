"""
MODULE: io_operations
DESCRIPTION: Handles all importing and exporting of 3D assets in Blender.
"""

import bpy
import os

def import_fbx(filepath: str) -> dict:
    """
    NAME: import_fbx
    DESCRIPTION: Imports an FBX file into the current Blender scene.
    
    INPUTS:
        filepath (str): The absolute path to the .fbx file to be imported.
        
    OUTPUT:
        dict: A dictionary containing 'success' (bool), 'message' (str), and optionally 'data' (any).
    """
    # Check if the path was actually provided
    if not filepath:
        return {"success": False, "message": "No filepath provided."}
        
    # Check if the file exists on the drive before trying to import
    if os.path.exists(filepath):
        try:
            # Execute the standard Blender import operator
            bpy.ops.import_scene.fbx(filepath=filepath)
            
            return {"success": True, "message": f"Successfully imported FBX from {filepath}"}
            
        except Exception as e:
            # Catch any Blender-specific errors during the import process
            return {"success": False, "message": f"Failed to import: {e}"}
    else:
        # File was not found at the specified location
        return {"success": False, "message": f"File not found: {filepath}"}