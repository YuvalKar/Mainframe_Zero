"""
NAME: sense_read_text_file
DESCRIPTION: Reads the content of a specified text file.

Input Arguments:
    filepath (str): The full path to the text file to be read.

Output/Return Value:
    dict: A dictionary containing the status of the operation.
          - 'success' (bool): True if the file was read successfully, False otherwise.
          - 'content' (str, optional): The content of the file if successful.
          - 'message' (str): A descriptive message indicating the outcome,
                             including success confirmation or error details.
"""
import os

def execute(filepath: str) -> dict:
    """
    Executes the file reading operation.

    Args:
        filepath (str): The path to the file to be read.

    Returns:
        dict: Operation status, content, and message.
    """
    if not os.path.exists(filepath):
        return {
            "success": False,
            "message": f"Error: File not found at '{filepath}'."
        }
    if not os.path.isfile(filepath):
        return {
            "success": False,
            "message": f"Error: Path '{filepath}' is not a file."
        }

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return {
            "success": True,
            "content": content,
            "message": f"Successfully read file '{filepath}'."
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error reading file '{filepath}': {str(e)}"
        }
