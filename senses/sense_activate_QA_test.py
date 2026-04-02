"""
NAME: sense_activate_QA_test
DESCRIPTION: Activates a predifined test in the application.
         
WHEN TO USE: 
- When requested to run a specific QA test, specifing the test name in the input.
         
INPUTS:
- test_name (str): The name of the test to activate. 
    - valid test names include:
        "HUD_TEST"
OUTPUTS:
- success (bool): Indicates whether the operation was successful.
- message (str): A descriptive message about the operation's outcome.
- data (dict, optional): If successful, a structured dictionary containing the test results and any relevant information. If the operation fails, this field may be omitted or set to None.
"""
from time import sleep

# Import the helper functions from your HUD streamer module
# Adjust the import path if needed (e.g., from core_utils.hud_streamer import ...)
from core_utils.hud_streamer import (
    send_hud_text, send_hud_gauge, send_hud_worker,
    send_hud_timer, send_hud_error, remove_hud_widget
)

def execute(test_name: str) -> dict:

    try:

        if test_name == "HUD_TEST":
            run_hud_test_sequence()
        else:
            return {"success": False, "message": f"Test '{test_name}' not recognized.", "data": None}

        return {"success": True, "message": f"Test '{test_name}' executed successfully.", "data": None}

    except Exception as e:
        return {"success": False, "message": f"An error occurred while executing test '{test_name}': {str(e)}", "data": None}   

# activate QA test "HUD_TEST"
def run_hud_test_sequence():
    """
    Broadcasts a sequence of real HUD updates with a 1-second delay between each.
    This relies on an active event loop to schedule the tasks.
    """
    
    # 1. TEXT Widgets
    send_hud_text("TXT_001", "TXT Initiating connection sequence...", level="info")
    sleep(0.4)
    send_hud_text("TXT_002", "TXT Warning: High latency detected", level="warning")
    sleep(0.4)
    send_hud_text("TXT_003", "TXT System boot complete", level="success")
    sleep(0.4)

    # 2. GAUGE Widgets
    send_hud_gauge("GAUGE_001", 25, label="GAUGE CPU Load")
    sleep(0.4)
    send_hud_gauge("GAUGE_002", 85, label="GAUGE Memory Usage")
    sleep(0.4)
    # Update an existing gauge
    send_hud_gauge("GAUGE_001", 60, label="CPU Load")
    sleep(0.4)

    # 3. TIMER Widgets
    send_hud_timer("TIMER_001", 50, "TIMER Connecting to Database")
    sleep(0.4)
    send_hud_timer("TIMER_002", 600, "TIMER Syncing User Assets")
    sleep(0.4)

    # 4. ERROR Widgets
    send_hud_error("ERR_001", "ERR Connection to Mainframe Zero lost", code=503)
    sleep(0.4)
    send_hud_error("ERR_002", "ERR Authentication failure", code=401)
    sleep(0.4)

    # 5. WORKER Widgets
    send_hud_worker("WORKER_001", 75, label="WORKER Data Processing")
    sleep(0.4)
    send_hud_worker("WORKER_002", 75, label="WORKER Data eating")
    sleep(0.4)
    send_hud_worker("WORKER_003", 0, label="WORKER Data cleaning")
    sleep(0.4)

    # 5. REMOVE Widgets
    # remove_hud_widget("TXT_001")
    # sleep(0.4)
    # remove_hud_widget("GAUGE_002")