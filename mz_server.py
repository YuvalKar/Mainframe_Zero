import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

# The server only knows about the core, nothing about the AI engine
import mz_core

# Global variable to hold our active chat session
mz_chat_session = None


# ==========================================
# ACTION HANDLERS
# Currently sitting here, can be moved to a separate file later
# ==========================================

async def handle_chat(payload: dict, websocket: WebSocket, stream_callback):
    """
    Handles standard chat messages intended for the AI engine.
    """
    user_input = payload.get("content", "")
    print(f"[Server] Processing chat input: {user_input}")
    
    # Step 1: Enrich the prompt
    final_prompt = mz_core.enrich_prompt(user_input)
    
    # Step 2: Run loop and stream results live to the React UI
    await mz_core.run_agentic_loop(
        mz_chat_session, 
        final_prompt, 
        emit_callback=stream_callback
    )

async def handle_change_model(payload: dict, websocket: WebSocket, stream_callback):
    """
    Handles switching the AI model and resetting the chat session.
    """
    global mz_chat_session
    new_model = payload.get("model", "gemini-2.5-flash") # Fallback to flash
    print(f"[Server] Switching model to: {new_model}")
    
    # Re-initialize the brain with the new model
    mz_chat_session = mz_core.create_chat_session(new_model)
    
    # Notify the frontend that the switch was successful
    await stream_callback({
        "type": "system", 
        "content": f"System: Successfully switched model to {new_model} and restarted session."
    })


# ==========================================
# ROUTER DICTIONARY
# Maps string actions from the frontend to their python functions
# ==========================================
ACTION_HANDLERS = {
    "chat": handle_chat,
    "change_model": handle_change_model
}


# ==========================================
# SERVER LIFESPAN & SETUP
# ==========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    global mz_chat_session
    print("[Server] Initializing Mainframe Zero Brain via Core...")
    
    try:
        # Initializing with default model
        mz_chat_session = mz_core.create_chat_session()
        print("[Server] Brain initialized successfully.")
    except Exception as e:
        print(f"[Server Error] Failed to initialize brain: {e}")
        
    yield
    
    print("[Server] Shutting down Mainframe Zero...")
    mz_chat_session = None

app = FastAPI(title="Mainframe Zero API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# WEBSOCKET ENDPOINT (The "Dumb" Dispatcher)
# ==========================================

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[Server] Client connected to WebSocket.")
    
    # This is the callback we pass to handlers to stream data back
    async def stream_to_frontend(log_item: dict):
        await websocket.send_json(log_item)
        
    try:
        while True:
            raw_input = await websocket.receive_text()
            
            try:
                # Expecting a JSON structure like: {"action": "chat", "content": "hello"}
                # or {"action": "change_model", "model": "gemini-2.5-pro"}
                data = json.loads(raw_input)
                action = data.get("action")
                
                # Route the request to the appropriate handler
                if action in ACTION_HANDLERS:
                    await ACTION_HANDLERS[action](data, websocket, stream_to_frontend)
                else:
                    print(f"[Server Warning] Unknown action received: {action}")
                    await stream_to_frontend({
                        "type": "error",
                        "content": f"System Error: Unknown action '{action}'"
                    })
                    
            except json.JSONDecodeError:
                # Temporary fallback: if raw text is sent, assume it's a chat message
                print(f"[Server] Received non-JSON string, falling back to chat handler.")
                fallback_payload = {"action": "chat", "content": raw_input}
                await handle_chat(fallback_payload, websocket, stream_to_frontend)
                
    except WebSocketDisconnect:
        print("[Server] Client disconnected.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)