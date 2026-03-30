import asyncio
import json
from typing import Callable, Any, List

# Call it like this:
# -------------------------
#     from core_utils.hud_streamer import send_hud_message
#     send_hud_message("HUD_ID_NAME", "DATA... enrich_prompt called, fetching context and updating attention...")

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
    A universal helper function to send messages to the HUD.
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