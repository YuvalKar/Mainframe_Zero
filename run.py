import subprocess
import time
import urllib.request
import urllib.error

def wait_for_backend(url="http://127.0.0.1:8000", timeout=30):
    # Loop until the backend responds or timeout is reached
    print("Waiting for backend to wake up", end="")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            # Try to reach the server
            urllib.request.urlopen(url)
            print("\nBackend is ready!")
            return True
        except urllib.error.HTTPError:
            # Server responded with an HTTP error (e.g., 404), which means it IS up!
            print("\nBackend is ready!")
            return True
        except urllib.error.URLError:
            # Connection refused - server is not up yet, wait 1 second
            print(".", end="", flush=True)
            time.sleep(1)
            
    print("\nBackend timeout!")
    return False

if __name__ == "__main__":
    # 1. Start the Backend process
    print("Starting Backend...")
    backend_process = subprocess.Popen("uvicorn mz_server:app --reload", shell=True)
    
    # 2. Wait for the Backend to be ready
    is_ready = wait_for_backend()
    
    if is_ready:
        print("Backend is up! Starting Frontend...")
        
        # 3. Start the Frontend process
        frontend_process = subprocess.Popen("npm run dev --prefix mz_frontend", shell=True)
        
        try:
            # Keep the main script alive and wait for the frontend process
            # This allows us to catch the Ctrl+C (KeyboardInterrupt) gracefully
            frontend_process.wait() 
        except KeyboardInterrupt:
            # Clean up both processes on manual exit so we don't leave zombies behind
            print("\nShutting down servers gracefully...")
            backend_process.terminate()
            frontend_process.terminate()
            print("Servers stopped. Goodbye!")
    else:
        # If the backend failed to start, don't leave it hanging
        print("Failed to start backend. Exiting.")
        backend_process.terminate()