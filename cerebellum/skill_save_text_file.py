"""
NAME: skill_save_text_file
DESCRIPTION: Save a given string of text content to a specified file_path. It acts as a universal utility for persisting generated code, documentation, or any text-based data to the filesystem.

Input Arguments:
    content (str): The text content string to be saved to the file.
    target_filename (str): The full path and filename where the content should be saved.
                           Example: 'path/to/document.md', 'script.py', or 'data.txt'

Output/Return Value:
    dict: A dictionary containing the status of the operation.
          - 'success' (bool): True if the content was saved successfully, False otherwise.
          - 'message' (str): A descriptive message indicating the outcome, 
                             including success confirmation or error details.
"""

def execute(content: str, target_filename: str) -> dict:
    """Executes the skill to save text content to a file.

    Args:
        content (str): The text content to write.
        target_filename (str): The path and name of the file to save.

    Returns:
        dict: A dictionary with 'success' (bool) and 'message' (str).
    """
    try:
        # Open the file in write mode with UTF-8 encoding
        with open(target_filename, 'w', encoding='utf-8') as f:
            f.write(content)
        # Return success message if file write is successful
        return {
            "success": True,
            "message": f"File successfully saved to {target_filename}"
        }
    except IOError as e:
        # Catch any IOError during file operations and return an error message
        return {
            "success": False,
            "message": f"Error saving file to {target_filename}: {e}"
        }
    except Exception as e:
        # Catch any other unexpected errors
        return {
            "success": False,
            "message": f"An unexpected error occurred while saving to {target_filename}: {e}"
        }