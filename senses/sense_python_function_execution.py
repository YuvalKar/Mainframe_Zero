"""
NAME: sense_python_function_execution
DESCRIPTION: Executes a specific function within a Python file and captures its return value or errors.

INPUTS:
    - filepath (str): Path to the .py file.
    - function_name (str): The name of the function to call.
    - args (list, optional): Positional arguments to pass to the function.
    - kwargs (dict, optional): Keyword arguments to pass to the function.
OUTPUT:
    - success (bool): Indicates if the function executed successfully.
    - result: The return value of the function if successful, or None if an error occurred.
    - error (str, optional): Error message if the execution failed, otherwise None.
"""

import subprocess
import json
import os

def execute(filepath: str, function_name: str, args: list = None, kwargs: dict = None) -> dict:
    """
    Acts as a 'Sense' for Mainframe Zero, providing direct feedback (Pain/Reward) 
    from executing specific logic within a file.
    """
    
    # Validation: Ensure the file exists
    if not os.path.exists(filepath):
        return {
            'success': False,
            'result': None,
            'error': f"Error: File not found at '{filepath}'"
        }

    # Prepare arguments for the Python call
    args = args or []
    kwargs = kwargs or {}
    
    # Construct a wrapper command to import the file and run the function
    # We use json.dumps to safely pass and return complex data structures
    module_name = os.path.splitext(os.path.basename(filepath))[0]
    directory = os.path.dirname(filepath) or "."
    
    python_code = f"""
import sys
import json
import importlib.util

# Add the file's directory to sys.path to allow imports
sys.path.append(r'{directory}')

try:
    spec = importlib.util.spec_from_file_location("{module_name}", r"{filepath}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    func = getattr(module, "{function_name}")
    res = func(*{args}, **{kwargs})
    
    # Output the result wrapped in a special tag for easy parsing
    print(f"RESULT_START{{json.dumps(res)}}RESULT_END")
except Exception as e:
    print(f"ERROR_START{{str(e)}}ERROR_END", file=sys.stderr)
    sys.exit(1)
"""

    try:
        # Execute the constructed code via subprocess
        result = subprocess.run(
            ['python', '-c', python_code],
            capture_output=True,
            text=True,
            check=False
        )

        is_success = result.returncode == 0
        output = result.stdout
        error_output = result.stderr

        # Extract result from the stdout
        final_result = None
        if "RESULT_START" in output:
            try:
                final_result = json.loads(output.split("RESULT_START")[1].split("RESULT_END")[0])
            except:
                final_result = output.strip()

        # Extract error from stderr if exists
        err_msg = ""
        if "ERROR_START" in error_output:
            err_msg = error_output.split("ERROR_START")[1].split("ERROR_END")[0]
        elif not is_success:
            err_msg = error_output.strip() or "Unknown execution error."

        return {
            'success': is_success,
            'result': final_result,
            'error': err_msg if err_msg else None
        }

    except Exception as e:
        return {
            'success': False,
            'result': None,
            'error': f"Sensing Process Failed: {str(e)}"
        }

# Example usage for self-test
if __name__ == "__main__":
    # Create a dummy file to test
    with open("temp_math.py", "w") as f:
        f.write("def add(a, b): return a + b")

    print("Testing Sense...")
    feedback = execute("temp_math.py", "add", args=[10, 5])
    print(f"Feedback: {feedback}")
    
    os.remove("temp_math.py")