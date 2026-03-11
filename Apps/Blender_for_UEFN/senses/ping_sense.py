"""
SENSE: ping_blender_sense
PURPOSE: A basic sense to check if the blender_for_uefn app is alive and responding, acting as a simple connection verification.
         
WHEN TO USE: 
- When the core initializes the app to verify basic communication.
- Before executing complex Blender operations to ensure the environment is awake.

INPUTS:
- None required.
"""

def execute() -> dict:
    # 1. No inputs to validate for a simple ping
    
    try:
        # 2. Perform the logic
        # For a ping, the logic is simply acknowledging existence.
        # This acts as a 'reward' signal for the AI, confirming successful interaction.
        result_data = "Ping successful. Senses are active."
        
        # 3. Return a standardized dictionary
        return {
            "success": True, 
            "message": "I exist successfully! The Blender app is awake.",
            "data": result_data
        }

    except Exception as e:
        # 4. Catch errors gracefully so the AI agent doesn't crash
        # This acts as a 'pain' signal, indicating a systemic failure.
        return {"success": False, "message": f"Failed to execute ping sense: {str(e)}"}