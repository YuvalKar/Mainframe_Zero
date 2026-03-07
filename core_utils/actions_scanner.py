import os
import ast # <-- Safe parsing library

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