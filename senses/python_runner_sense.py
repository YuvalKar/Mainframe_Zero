import subprocess
import os

def run_and_sense(filepath: str) -> dict:
    """
    Executes a Python script at the given filepath and captures its output and errors.
    This function acts as a 'Sense' for Python execution, providing feedback
    on success (reward) or failure (pain).

    Args:
        filepath (str): The absolute or relative path to the Python script to execute.

    Returns:
        dict: A dictionary containing:
            'success' (bool): True if the script executed with a return code of 0, False otherwise.
            'output' (str): The captured standard output of the script.
            'error' (str): The captured standard error of the script.
    """
    # Ensure the file exists before attempting to run it
    if not os.path.exists(filepath):
        return {
            'success': False,
            'output': '',
            'error': f"Error: File not found at '{filepath}'"
        }
    
    # Use subprocess.run to execute the Python script
    # capture_output=True captures stdout and stderr
    # text=True decodes stdout and stderr as strings
    # check=False prevents an exception for non-zero exit codes, allowing us to read stderr
    try:
        result = subprocess.run(
            ['python', filepath],
            capture_output=True,
            text=True,
            check=False
        )

        # Determine success based on the return code
        is_success = result.returncode == 0

        return {
            'success': is_success,
            'output': result.stdout.strip(),
            'error': result.stderr.strip()
        }
    except Exception as e:
        # Catch any exceptions that might occur during subprocess execution itself
        return {
            'success': False,
            'output': '',
            'error': f"An unexpected error occurred during execution: {e}"
        }

# Example usage (for testing purposes, not part of the core sense logic)
if __name__ == '__main__':
    # Create a dummy successful script
    with open('test_success.py', 'w') as f:
        f.write("print('Hello from success!')\nimport sys\nsys.exit(0)")

    # Create a dummy failing script
    with open('test_failure.py', 'w') as f:
        f.write("import sys\nprint('Error message to stderr', file=sys.stderr)\nsys.exit(1)")

    # Create a dummy script with an exception
    with open('test_exception.py', 'w') as f:
        f.write("raise ValueError('This is an intentional error')")

    # Test successful execution
    print("\n--- Testing successful script ---")
    success_result = run_and_sense('test_success.py')
    print(f"Success: {success_result['success']}")
    print(f"Output: '{success_result['output']}'")
    print(f"Error: '{success_result['error']}'")

    # Test failing execution
    print("\n--- Testing failing script ---")
    failure_result = run_and_sense('test_failure.py')
    print(f"Success: {failure_result['success']}")
    print(f"Output: '{failure_result['output']}'")
    print(f"Error: '{failure_result['error']}'")

    # Test script with an exception
    print("\n--- Testing script with exception ---")
    exception_result = run_and_sense('test_exception.py')
    print(f"Success: {exception_result['success']}")
    print(f"Output: '{exception_result['output']}'")
    print(f"Error: '{exception_result['error']}'")

    # Test non-existent file
    print("\n--- Testing non-existent file ---")
    non_existent_result = run_and_sense('non_existent_script.py')
    print(f"Success: {non_existent_result['success']}")
    print(f"Output: '{non_existent_result['output']}'")
    print(f"Error: '{non_existent_result['error']}'")

    # Clean up dummy files
    os.remove('test_success.py')
    os.remove('test_failure.py')
    os.remove('test_exception.py')
