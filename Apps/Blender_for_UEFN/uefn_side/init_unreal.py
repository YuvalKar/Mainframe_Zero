import unreal
import socket

server_socket = None
tick_handle = None

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
    
    # Using port 9998 so it won't fight with Blender
    server_socket.bind(('127.0.0.1', 9998))
    server_socket.listen(1)
    server_socket.setblocking(False)
    
    # We use unreal.log instead of print to show it properly in UEFN's Output Log
    unreal.log("nBaya UEFN Server is listening on port 9998...")

def listen_for_commands(delta_time):
    # Notice that Unreal passes 'delta_time' to the tick function, we just accept it
    global server_socket
    
    if server_socket is None:
        return

    try:
        conn, addr = server_socket.accept()
        conn.setblocking(True) 
        
        data = conn.recv(4096).decode('utf-8')
        command = data.strip()

        if command.startswith("EXECUTE_CODE:"):
            script_content = command[len("EXECUTE_CODE:"):].strip()
            try:
                # Execute the raw python string in Unreal's environment
                exec(script_content)
            except Exception as e:
                # Log errors in red inside UEFN's Output Log
                unreal.log_error(f"Error executing raw AI code: {e}")
                
        conn.close()
        
    except BlockingIOError:
        pass
    except Exception as e:
        unreal.log_warning(f"Server error: {e}")

def register():
    global tick_handle
    start_server()
    
    # Clean up the old tick handle if we are reloading the script
    if tick_handle:
        try:
            unreal.unregister_slate_post_tick_callback(tick_handle)
        except:
            pass
            
    # This hooks our function to run every frame in the Unreal Editor
    tick_handle = unreal.register_slate_post_tick_callback(listen_for_commands)

if __name__ == "__main__":
    register()