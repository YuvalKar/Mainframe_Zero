import asyncio
import json
from typing import Callable, Any, List

# Call it like this:
# -------------------------
#     from core_utils.hud_streamer import send_hud_timer
#     send_hud_timer("DB_INIT", 10, "Initializing Database...")

class HUDStreamer:
    """
    A central bus to route messages from any backend component 
    directly to the frontend HUD via WebSocket.
    """
    def __init__(self):
        # List of active WebSocket send functions
        self._subscribers: List[Callable] = []

    def subscribe(self, callback: Callable):
        """Registers a callback to receive HUD updates."""
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable):
        """Removes a registered callback."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    async def send(self, element_id: str, data: Any):
        """
        The core async pipe. Dispatches data to all connected WebSockets.
        """
        payload = {
            "type": "hud_update",
            "id": element_id,
            "data": data
        }
        
        # Create tasks for all subscribers to send in parallel
        if self._subscribers:
            await asyncio.gather(
                *(callback(payload) for callback in self._subscribers),
                return_exceptions=True
            )

# Create a single global instance
hud_bus = HUDStreamer()

def send_hud_message(element_id: str, data: Any):
    """
    A universal helper function to send raw messages to the HUD.
    Safe to call from both synchronous (def) and asynchronous (async def) functions.
    """
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            # If we are in an async context, schedule the task
            loop.create_task(hud_bus.send(element_id, data))
    except RuntimeError:
        # If no loop is running, we can't send (shouldn't happen in FastAPI)
        print(f"[HUD] Warning: No event loop found to send message {element_id}")

# --- WIDGET HELPER FUNCTIONS ---

def send_hud_text(element_id: str, text: str):
    """Sends a basic text widget to the HUD."""
    send_hud_message(element_id, {"type": "TEXT", "value": text})

def send_hud_gauge(element_id: str, percentage: int):
    """Sends a progress gauge widget (0-100) to the HUD."""
    send_hud_message(element_id, {"type": "GAUGE", "value": percentage})

def send_hud_timer(element_id: str, seconds: int, text: str):
    """
    Sends a self-destructing timer widget to the HUD.
    Packages the time and text into a structured dictionary.
    """
    send_hud_message(element_id, {
        "type": "TIMER",
        "value": {
            "time": seconds,
            "text": text
        }
    })