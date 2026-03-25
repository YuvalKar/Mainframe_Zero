import socket
import json

def ask_uefn(script_content: str) -> dict:
    """
    Sends raw Python code to the UEFN socket server on port 9998.
    Waits for a response and returns a standard skill outcome dictionary.
    """
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('127.0.0.1', 9998))
        
        command = "EXECUTE_CODE:\n" + script_content
        client_socket.send(command.encode('utf-8'))
        
        # Wait for UEFN to send data back
        response_data = client_socket.recv(4096).decode('utf-8')
        client_socket.close()
        
        try:
            return json.loads(response_data)
        except json.JSONDecodeError:
            return {
                "success": True,
                "message": response_data,
                "data": []
            }
            
    except ConnectionRefusedError:
        return {
            "success": False,
            "message": "Error: Could not connect to UEFN. Is it open on port 9998?",
            "data": []
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"An unexpected communication error occurred: {e}",
            "data": []
        }