import bpy
import socket

server_socket = None

def start_server():
    global server_socket
    
    # Close existing socket if it exists to avoid port conflicts during reloads
    if server_socket:
        try:
            server_socket.close()
        except:
            pass
            
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('127.0.0.1', 9999))
    server_socket.listen(1)
    server_socket.setblocking(False)
    print("nBaya Two-Way Server is listening...")

def listen_for_commands():
    global server_socket
    
    # Safety check just in case the server isn't up
    if server_socket is None:
        return None

    try:
        conn, addr = server_socket.accept()
        
        # Make this specific connection wait patiently for the data to arrive
        conn.setblocking(True) 
        
        data = conn.recv(1024).decode('utf-8')
        command = data.strip()
        
        if command == "DO BOX":
            bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
            conn.send("Box created!".encode('utf-8'))

        if command.startswith("EXECUTE_FILE:"):
            # Extract the file path
            filepath = command.split("EXECUTE_FILE:")[1].strip()
            
            # Open the file, read its contents, and execute it right here
            with open(filepath, 'r') as file:
                exec(file.read())

        if command == "GET_LOCATION":
            # Bypass context, ask the database directly
            selected_objs = [o for o in bpy.data.objects if o.select_get()]
            
            if selected_objs:
                obj = selected_objs[0]
                loc = f"X:{obj.location.x:.2f}, Y:{obj.location.y:.2f}, Z:{obj.location.z:.2f}"
                conn.send(loc.encode('utf-8'))
            else:
                conn.send("No object selected".encode('utf-8'))
                
        conn.close()
        
    except BlockingIOError:
        # We removed the print here so it doesn't spam your console 10 times a second
        pass
    except Exception as e:
        # Catching other random errors so the timer doesn't crash completely
        print(f"Server error: {e}")
        
    # Return the interval for the next execution
    return 0.1

def register():
    # This runs when Blender starts and loads the script
    start_server()
    if bpy.app.timers.is_registered(listen_for_commands):
        bpy.app.timers.unregister(listen_for_commands)
    bpy.app.timers.register(listen_for_commands)

def unregister():
    # This runs for cleanup when closing Blender or disabling the script
    global server_socket
    if bpy.app.timers.is_registered(listen_for_commands):
        bpy.app.timers.unregister(listen_for_commands)
    if server_socket:
        server_socket.close()
        server_socket = None
        print("nBaya Server closed.")

# This is needed so the script can run from the text editor as well
if __name__ == "__main__":
    register()