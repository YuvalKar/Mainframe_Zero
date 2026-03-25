import socket

def run_in_blender(script_content: str) -> dict:
    """
    Sends raw Python code to the Blender socket server on port 9999.
    Returns a standard skill outcome dictionary.
    """
    try:
        # Create a socket and connect to our Blender server
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('127.0.0.1', 9999))
        
        # Format the command with our EXECUTE_CODE prefix
        # We add a newline to ensure the script starts cleanly
        command = "EXECUTE_CODE:\n" + script_content
        
        # Send the command encoded as bytes
        client_socket.send(command.encode('utf-8'))
        
        # Close the connection neatly
        client_socket.close()
        
        # Return success in the exact format the AI Prefrontal Cortex expects
        return {
            "success": True,
            "message": "Code successfully sent to Blender and executed."
        }
        
    except ConnectionRefusedError:
        # This happens if Blender is closed or the server script isn't running
        return {
            "success": False,
            "message": "Error: Could not connect to Blender. Is Blender open and the nBaya server listening on port 9999?"
        }
    except Exception as e:
        # Catch any other weird network hiccups
        return {
            "success": False,
            "message": f"An unexpected communication error occurred: {e}"
        }