import socket

def send_execute_command(filepath):
    try:
        # Create a socket and connect to our Blender server
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('127.0.0.1', 9999))
        
        # Format the command exactly as our server expects it
        command = f"EXECUTE_FILE:{filepath}"
        
        # Send the command encoded as bytes
        client_socket.send(command.encode('utf-8'))
        print(f"Command sent successfully: {command}")
        
        # Close the connection
        client_socket.close()
        
    except ConnectionRefusedError:
        print("Error: Could not connect. Is Blender open and the server listening?")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # IMPORTANT: Replace this path with the actual location of your create_cylinder.py file
    # Using 'r' before the string helps Windows read the backslashes correctly
    file_to_run = r"C:\Users\yuval\Documents\NBAYA_projects\Mainframe_Zero\tests\create_cylinder.py" 
    
    send_execute_command(file_to_run)