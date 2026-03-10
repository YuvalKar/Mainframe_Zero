from fastapi import WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# The server only knows about the core, nothing about the AI engine
import mz_core

# Global variable to hold our active chat session
mz_chat_session = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global mz_chat_session
    print("[Server] Initializing Mainframe Zero Brain via Core...")
    
    try:
        # The server just asks the core to initialize itself
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

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[Server] Client connected to WebSocket.")
    
    # This is the callback we pass to the core to stream data back
    async def stream_to_frontend(log_item: dict):
        await websocket.send_json(log_item)
        
    try:
        while True:
            user_input = await websocket.receive_text()
            print(f"[Server] Received input: {user_input}")
            
            # Step 1: Enrich the prompt
            final_prompt = mz_core.enrich_prompt(user_input)
            
            # Step 2: Run loop and stream results live to the React UI!
            await mz_core.run_agentic_loop(
                mz_chat_session, 
                final_prompt, 
                emit_callback=stream_to_frontend
            )
            
    except WebSocketDisconnect:
        print("[Server] Client disconnected.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)