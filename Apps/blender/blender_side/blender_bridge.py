import socket
import json

def ask_blender(script_content: str) -> dict:
    """
    Sends raw Python code to the Blender socket server on port 9999.
    Waits for a response and returns a standard skill outcome dictionary.
    """
    try:
        # Create a socket and connect to our Blender server
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('127.0.0.1', 9999))
        
        # Format the command with our EXECUTE_CODE prefix
        command = "EXECUTE_CODE:\n" + script_content
        
        # Send the command encoded as bytes
        client_socket.send(command.encode('utf-8'))
        
        # --- THE NEW MAGIC: Wait for Blender to send data back ---
        # Receive up to 4096 bytes of response data
        response_data = client_socket.recv(4096).decode('utf-8')
        
        # Close the connection neatly
        client_socket.close()
        
        # Try to parse the response as JSON (perfect for our SENSE skills)
        try:
            return json.loads(response_data)
        except json.JSONDecodeError:
            # If it's not valid JSON, just return it as a raw message (fallback)
            return {
                "success": True,
                "message": response_data,
                "data": {}
            }
        
    except ConnectionRefusedError:
        # This happens if Blender is closed or the server script isn't running
        return {
            "success": False,
            "message": "Error: Could not connect to Blender. Is it open and listening on port 9999?",
            "data": {}
        }
    except Exception as e:
        # Catch any other unexpected network hiccups
        return {
            "success": False,
            "message": f"An unexpected communication error occurred: {e}",
            "data": {}
        }