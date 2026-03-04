import os
import ast # <-- Safe parsing library

def get_available_skills(cerebellum_path: str = "cerebellum") -> dict:
    """
    Scans the directory for Python skill modules and extracts their names and docstrings safely.
    """
    available_skills = {}
    if not os.path.isdir(cerebellum_path):
        print(f"Warning: Cerebellum path '{cerebellum_path}' not found.")
        return available_skills

    for filename in os.listdir(cerebellum_path):
        if filename.endswith(".py") and filename != "__init__.py":
            skill_name = filename[:-3]  # Remove .py extension
            file_path = os.path.join(cerebellum_path, filename)

            try:
                # Read the file purely as text
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                # Parse the abstract syntax tree SAFELY (no execution)
                parsed_tree = ast.parse(file_content)
                
                # Extract the module docstring
                description = ast.get_docstring(parsed_tree)
                
                available_skills[skill_name] = description.strip() if description else 'No description provided.'
                
            except Exception as e:
                available_skills[skill_name] = f'Error parsing description safely: {e}'

    return available_skills

if __name__ == '__main__':
    # Example usage (for testing purposes)
    test_dir = 'cerebellum_test_temp'
    os.makedirs(test_dir, exist_ok=True)
    
    try:
        with open(os.path.join(test_dir, 'test_skill.py'), 'w') as f:
            f.write('"""This is a test skill module."""\ndef execute():\n    print("Test skill executed!")')
        with open(os.path.join(test_dir, 'another_skill.py'), 'w') as f:
            f.write('"""Another skill for demonstration."""\ndef run():\n    print("Another skill running!")')

        print("Scanning for skills...")
        skills = get_available_skills(test_dir)
        for name, desc in skills.items():
            print(f"Skill: {name}\n  Description: {desc}\n")

    finally:
        # Clean up dummy files/directory using os
        if os.path.exists(test_dir):
            for file in os.listdir(test_dir):
                os.remove(os.path.join(test_dir, file))
            os.rmdir(test_dir)
            print(f"Cleaned up test directory: {test_dir}")