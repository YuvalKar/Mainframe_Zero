import asyncio
import json
from typing import Callable, Any, List, Optional

# Call it like this:
# -------------------------
#     from core_utils.hud_streamer import send_hud_timer, remove_hud_widget
#     send_hud_timer("DB_INIT", 10, "Initializing Database...")
#     remove_hud_widget("DB_INIT") # If you need to stop it early

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

    async def send(self, element_id: str, action: str, widget_type: Optional[str], level: str, payload: Any):
        """
        Builds the flattened payload and dispatches it to all connected WebSockets.
        """
        message = {
            "type": "hud_update",
            "id": element_id,
            "action": action, # 'upsert' (update/insert) or 'delete'
        }
        
        # Add widget data only if we are creating or updating
        if action == "upsert":
            message["widget_type"] = widget_type
            message["level"] = level
            message["payload"] = payload
            
        # Create tasks for all subscribers to send in parallel
        if self._subscribers:
            await asyncio.gather(
                *(callback(message) for callback in self._subscribers),
                return_exceptions=True
            )

# Create a single global instance
hud_bus = HUDStreamer()

def send_hud_message(element_id: str, action: str = "upsert", widget_type: str = "TEXT", level: str = "info", payload: Any = None):
    """
    A universal helper function to send raw messages to the HUD.
    Safe to call from both synchronous (def) and asynchronous (async def) functions.
    """
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            # If we are in an async context, schedule the task
            loop.create_task(hud_bus.send(element_id, action, widget_type, level, payload))
    except RuntimeError:
        # If no loop is running, we can't send (shouldn't happen in FastAPI)
        print(f"[HUD] Warning: No event loop found to send message {element_id}")

# --- WIDGET HELPER FUNCTIONS ---

def send_hud_text(element_id: str, text: str, level: str = "info"):
    """Sends or updates a basic text widget."""
    send_hud_message(
        element_id=element_id, 
        action="upsert", 
        widget_type="TEXT", 
        level=level, 
        payload={"value": text}
    )

def send_hud_gauge(element_id: str, percentage: int, label: str = "LOD"):
    """Sends or updates a progress gauge widget (0-100)."""
    send_hud_message(
        element_id=element_id, 
        action="upsert", 
        widget_type="GAUGE", 
        level="info", 
        payload={"value": percentage, "label": label}
    )

def send_hud_timer(element_id: str, seconds: int, text: str):
    """Sends a self-destructing timer widget to the HUD."""
    send_hud_message(
        element_id=element_id, 
        action="upsert", 
        widget_type="TIMER", 
        level="info", 
        payload={"value": seconds, "label": text}
    )

def send_hud_error(element_id: str, error_message: str, code: Optional[int] = None):
    """Sends an explicit error widget."""
    send_hud_message(
        element_id=element_id, 
        action="upsert", 
        widget_type="ERROR", 
        level="error", 
        payload={"value": error_message, "code": code}
    )

def send_hud_worker(element_id: str, percentage: int, label: str = "WORKER"):
    """Sends or updates a worker status widget (0-100)."""
    send_hud_message(
        element_id=element_id, 
        action="upsert", 
        widget_type="WORKER", 
        level="info", 
        payload={"value": percentage, "label": label}
    )
    
def remove_hud_widget(element_id: str):
    """Explicitly removes a widget from the screen by its ID."""
    send_hud_message(
        element_id=element_id, 
        action="delete"
    )