import socket

def test_uefn_connection():
    # The code we want UEFN to execute
    # Using unreal.log to print to the Output Log
    remote_script = """
import unreal
unreal.log("-----------------------------------------")
unreal.log("HELLO FROM AI! The connection is LIVE.")
unreal.log("-----------------------------------------")
"""

    try:
        # Create a socket and connect to our UEFN server (Port 9998)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('127.0.0.1', 9998))
        
        # Format the command with our EXECUTE_CODE prefix
        command = "EXECUTE_CODE:" + remote_script
        
        # Send the command
        client_socket.send(command.encode('utf-8'))
        print("Test command sent to UEFN!")
        
        client_socket.close()
        
    except ConnectionRefusedError:
        print("Error: Could not connect. Is UEFN open and the server listening?")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    test_uefn_connection()