# locate at: C:\Users\yuval\AppData\Roaming\Blender Foundation\Blender\5.1\scripts\startup
import bpy
import socket

server_socket = None

def start_server():
    global server_socket
    
    # Close existing socket if it exists to avoid port conflicts
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
    
    # Safety check
    if server_socket is None:
        return None

    try:
        conn, addr = server_socket.accept()
        conn.setblocking(True) 
        
        # Increased buffer size to 4096 to handle larger code blocks gracefully
        data = conn.recv(4096).decode('utf-8')
        command = data.strip()
        
        if command == "DO BOX":
            bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
            conn.send("Box created!".encode('utf-8'))

        # Keep the old file execution capability just in case
        if command.startswith("EXECUTE_FILE:"):
            filepath = command.split("EXECUTE_FILE:")[1].strip()
            with open(filepath, 'r') as file:
                exec(file.read())

        # --- THE NEW MAGIC: Execute raw code directly from memory ---
        if command.startswith("EXECUTE_CODE:"):
            # Extract everything after the prefix
            script_content = command[len("EXECUTE_CODE:"):].strip()
            
            try:
                # Execute the raw python string in Blender's current environment
                exec(script_content)
                # We can send a silent success back if needed, but for now we just run it
            except Exception as e:
                # Print the error to Blender's console so we can debug our generated scripts
                print(f"Error executing raw AI code: {e}")

        if command == "GET_LOCATION":
            selected_objs = [o for o in bpy.data.objects if o.select_get()]
            if selected_objs:
                obj = selected_objs[0]
                loc = f"X:{obj.location.x:.2f}, Y:{obj.location.y:.2f}, Z:{obj.location.z:.2f}"
                conn.send(loc.encode('utf-8'))
            else:
                conn.send("No object selected".encode('utf-8'))
                
        conn.close()
        
    except BlockingIOError:
        pass
    except Exception as e:
        print(f"Server error: {e}")
        
    return 0.1

def register():
    start_server()
    if bpy.app.timers.is_registered(listen_for_commands):
        bpy.app.timers.unregister(listen_for_commands)
    bpy.app.timers.register(listen_for_commands)

def unregister():
    global server_socket
    if bpy.app.timers.is_registered(listen_for_commands):
        bpy.app.timers.unregister(listen_for_commands)
    if server_socket:
        server_socket.close()
        server_socket = None
        print("nBaya Server closed.")

if __name__ == "__main__":
    register()