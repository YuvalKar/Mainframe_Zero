"""
NAME: sense_get_directory_tree
DESCRIPTION: Scans a local directory and generates a hierarchical tree structure of its contents.
         
WHEN TO USE: 
- When the system needs to understand the file structure of a specific folder or workspace.
- To populate the UI file explorer with the user's local files.
- DO NOT use this to read the actual contents of the files, only their names and paths.

INPUTS:
- root_path (str): The path to the directory to scan. Default is '.' (current directory).
- allowed_extensions (list, optional): A list of file extensions to include. Default is ['.md', '.py'].
OUTPUTS:
- success (bool): Indicates whether the operation was successful.
- message (str): A descriptive message about the operation's outcome.
- data (list, optional): If successful, a list of dictionaries representing the directory tree. Each dictionary has the following structure:
    {
        "name": "filename_or_foldername",
        "type": "file" or "directory",
        "path": "full_path_to_item",
        "children": [ ... ] # Only for directories, a list of child items with the same structure
    }
"""
import os
import fnmatch

def _parse_mzignore(root_path: str) -> list:
    # Look for .mzignore in the root path and parse its lines into a list of patterns
    # We add some default safe ignores to prevent scanning massive unneeded folders
    ignore_patterns = [".git", "__pycache__", ".attentions", ".logs", "node_modules"] 
    mzignore_path = os.path.join(root_path, ".mzignore")
    
    if os.path.exists(mzignore_path):
        try:
            with open(mzignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        ignore_patterns.append(line)

            print(f'Loaded .mzignore with patterns: {ignore_patterns}')
        except Exception:
            print('cant load .mzignore')
            pass # Silently fail and use defaults if we can't read the ignore file
            
    return ignore_patterns

def _should_ignore(name: str, ignore_patterns: list) -> bool:
    # Check if a file or folder name matches any of the ignore patterns
    for pattern in ignore_patterns:
        if fnmatch.fnmatch(name, pattern):
            return True
    return False

def _build_tree(current_path: str, allowed_extensions: list, ignore_patterns: list) -> list:
    # Recursively build the directory tree as a list of dictionaries
    tree = []
    try:
        with os.scandir(current_path) as it:
            for entry in it:
                if _should_ignore(entry.name, ignore_patterns):
                    continue
                
                if entry.is_dir():
                    children = _build_tree(entry.path, allowed_extensions, ignore_patterns)
                    # Optional: Only add folders if they contain valid files/subfolders
                    if children: 
                        tree.append({
                            "name": entry.name,
                            "type": "directory",
                            "path": entry.path,
                            "children": children
                        })
                elif entry.is_file():
                    _, ext = os.path.splitext(entry.name)
                    # If allowed_extensions is empty, allow all. Otherwise, check extension.
                    if not allowed_extensions or ext in allowed_extensions:
                        tree.append({
                            "name": entry.name,
                            "type": "file",
                            "path": entry.path
                        })
    except PermissionError:
        pass # Skip folders we don't have OS permission to read
        
    # Sort the results: Directories first, then files, alphabetically
    tree.sort(key=lambda x: (x['type'] != 'directory', x['name'].lower()))
    return tree

def execute(root_path: str = ".", allowed_extensions: list = None) -> dict:
    # 1. Validate inputs and set defaults
    if allowed_extensions is None:
        allowed_extensions = ['.md', '.py']
        
    if not os.path.exists(root_path):
        return {"success": False, "message": f"Path not found: {root_path}"}

    try:
        # 2. Perform the logic
        ignore_patterns = _parse_mzignore(root_path)
        tree_data = _build_tree(root_path, allowed_extensions, ignore_patterns)
        
        # 3. Return a standardized dictionary
        return {
            "success": True,
            "message": "Directory tree generated successfully.",
            "data": tree_data
        }

    except Exception as e:
        # 4. Catch errors gracefully so the AI agent doesn't crash
        return {"success": False, "message": f"Failed to generate tree: {str(e)}"}