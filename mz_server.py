from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from google import genai
from google.genai import types

# Import our core logic (The Prefrontal Cortex)
import MZ_Terminal

# Global variables to hold our client AND active chat session
mz_client = None
mz_chat_session = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI.
    Code before 'yield' runs on server startup.
    Code after 'yield' runs on server shutdown.
    """
    global mz_client, mz_chat_session
    print("[Server] Initializing Mainframe Zero Brain...")
    
    try:
        with open("system_prompt.md", "r", encoding="utf-8") as f:
            system_rules = f.read()
            
        # Keep the client connection alive globally
        mz_client = genai.Client()
        mz_chat_session = mz_client.chats.create(
            model='gemini-2.5-flash',
            config=types.GenerateContentConfig(
                system_instruction=system_rules,
                temperature=0.1,
                response_mime_type="application/json",
            )
        )
        print("[Server] Brain initialized successfully.")
    except Exception as e:
        print(f"[Server Error] Failed to initialize brain: {e}")
        
    # This is where the server actually runs and handles requests
    yield
    
    # Anything down here happens when you hit Ctrl+C to stop the server
    print("[Server] Shutting down Mainframe Zero...")
    mz_client = None
    mz_chat_session = None

# Initialize FastAPI with the lifespan manager
app = FastAPI(title="Mainframe Zero API", lifespan=lifespan)

# Allow the React frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # React's default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class UserRequest(BaseModel):
    user_input: str

@app.post("/chat")
async def chat_endpoint(request: UserRequest):
    """
    Receives input from the UI, passes it to the core,
    and returns the JSON log containing thoughts and actions.
    """
    global mz_chat_session
    
    if not mz_chat_session:
        return {"error": "Chat session is not initialized."}
    
    # Step 1: Enrich the prompt using the core logic
    final_prompt = MZ_Terminal.enrich_prompt(request.user_input)
    
    # Step 2: Run the agentic loop and get the log
    result_log = MZ_Terminal.run_agentic_loop(mz_chat_session, final_prompt)
    
    # Return the full log to the frontend
    return result_log

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)