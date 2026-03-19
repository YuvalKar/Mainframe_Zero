import bpy
import socket

server_socket = None

def start_server():
    global server_socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('127.0.0.1', 9999))
    server_socket.listen(1)
    server_socket.setblocking(False)
    print("nBaya Two-Way Server is listening...")

def listen_for_commands():

    global server_socket

    try:
        conn, addr = server_socket.accept()
        
        # --- THE MAGIC FIX ---
        # Make this specific connection wait patiently for the data to arrive
        conn.setblocking(True) 
        
        data = conn.recv(1024).decode('utf-8')
        command = data.strip()
        
        if command == "DO BOX":
            bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
            conn.send("Box created!".encode('utf-8'))

        # Inside our Blender listener loop:
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
        
    return 0.1

# Initialize and start
start_server()

if bpy.app.timers.is_registered(listen_for_commands):
    bpy.app.timers.unregister(listen_for_commands)
bpy.app.timers.register(listen_for_commands)