# MZ_APPNAME Docstring Standard
This document defines the strict formatting rules for writing Python docstrings in the MZ_APPNAME architecture. Both the AI and human developers must follow this exact structure to ensure functions are properly indexed and executed.
mz_APPNAME refers to scripts that are app specific, for examle: mz_blender, mz_uefn, etc.


## 1. Module Level (File Head)
Every `.py` file inside the `mz_APPNAME` directories must begin with a module-level docstring. This tells the indexer what "family" of tools lives inside this file.

**Format:**
```
"""
MODULE: <module_name>
DESCRIPTION: <A short, one-line description of what the tools in this file generally do.>
"""
```
**Example:**
```
"""
MODULE: io_operations
DESCRIPTION: Handles all importing and exporting of 3D assets in Blender.
"""

import bpy
import os
# ... rest of the file ...
```

## 2. Function Level (Function Head)

Every callable function must have a docstring immediately following the def statement. This is the exact "ID card" the AI will read to understand how to use the tool.

**Format Rules:**

- **NAME:** Must exactly match the python function name.
- **DESCRIPTION:** Clear explanation of what the tool does.
- **INPUTS:** List of parameters. Must include the expected type (e.g., str, int, list, dict) and a short explanation. If there are no inputs, write None.
- **OUTPUT:** What the function returns. In our architecture, this is always a dict containing at least success and message.

**Format:**
```
    """
    NAME: <function_name>
    DESCRIPTION: <What does this do and when should the AI use it?>
    
    INPUTS:
        <param_name> (<type>): <What is this parameter?>
        <param_name> (<type>): <What is this parameter?> (Optional - default is X)
        
    OUTPUT:
        dict: A dictionary containing 'success' (bool), 'message' (str), and optionally 'data' (any).
    """
```

**Example:**
```
def import_fbx(filepath: str) -> dict:
    """
    NAME: import_fbx
    DESCRIPTION: Imports an FBX file into the current Blender scene.
    
    INPUTS:
        filepath (str): The absolute path to the .fbx file to be imported.
        
    OUTPUT:
        dict: A dictionary containing 'success' and 'message'.
    """
    # Function logic goes here
    pass
```    