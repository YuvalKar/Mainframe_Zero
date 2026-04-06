import subprocess
import time
import urllib.request
import urllib.error

def wait_for_service(url, name, timeout=30):
    # Generic wait function for both Backend and Frontend
    print(f"Waiting for {name} at {url}", end="")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            # Try to reach the server
            urllib.request.urlopen(url)
            print(f"\n{name} is ready!")
            return True
        except urllib.error.HTTPError:
            # If we get a 404 or any HTTP error, the server IS running!
            print(f"\n{name} is ready (responded with HTTP error)!")
            return True
        except urllib.error.URLError:
            # Connection refused - server is not up yet
            print(".", end="", flush=True)
            time.sleep(1)
            
    print(f"\n{name} timeout!")
    return False

if __name__ == "__main__":
    # 1. Start the Backend (Mainframe Zero Core)
    print("Starting Backend...")
    backend_process = subprocess.Popen("uvicorn mz_server:app --reload", shell=True)
    frontend_process = None
    electron_process = None
    
    try:
        if wait_for_service("http://127.0.0.1:8000", "Backend"):
            # 2. Start the Frontend (React App)
            print("Starting Frontend Dev Server...")
            frontend_process = subprocess.Popen("npm run dev --prefix mz_frontend", shell=True)
            
            # 3. Wait for Frontend to be ready (usually port 5173 for Vite)
            if wait_for_service("http://localhost:5173", "Frontend"):
                print("Everything is up! Launching Electron Overlay...")
                
                # 4. Launch Electron FROM the frontend directory
                electron_cmd = "npx electron electron-main.js"
                electron_process = subprocess.Popen(electron_cmd, shell=True, cwd="mz_frontend")

                # Wait for Electron to close naturally
                electron_process.wait() 
            else:
                print("Frontend failed to start.")
        else:
            print("Backend failed to start.")
            
    except KeyboardInterrupt:
        # User pressed Ctrl+C
        print("\nKeyboard interrupt detected...")
        
    finally:
        # This block always runs at the end, cleaning up everything
        print("\nShutting down Mainframe Zero processes...")
        if backend_process and backend_process.poll() is None:
            backend_process.terminate()
        if frontend_process and frontend_process.poll() is None:
            frontend_process.terminate()
        if electron_process and electron_process.poll() is None:
            electron_process.terminate()
        print("Shutdown complete.")