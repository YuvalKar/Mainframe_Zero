# apps/blender_for_uefn/__init__.py

# Import the newly created ping sense
from .senses import ping_sense

def register_to_core(core_system, attention_data):
    """
    The main entry point for the Blender UEFN app.
    This function is called by the Core when Attention shifts to this app.
    """
    app_name = "נlender_for_uefn"  # Using a unique character to ensure distinctiveness in logs
    task_name = attention_data.get("name", "Unknown Task")
    workspace_dir = attention_data.get("attention_dir", "Unknown Path")
    
    print(f"\n[{app_name}] Waking up...")
    print(f"[{app_name}] Focusing on task: '{task_name}'")
    print(f"[{app_name}] Workspace mounted at: {workspace_dir}")
    
    # Register the ping sense to the core
    # We assume the core_system has a way to store these, like a dictionary or a register method
    if hasattr(core_system, 'register_tool'):
        core_system.register_tool(
            tool_name="ping_blender_sense",
            tool_function=ping_sense.execute,
            tool_docstring=ping_sense.__doc__
        )
        print(f"[{app_name}] Registered SENSE: ping_blender_sense")
    else:
        # A fallback just in case the core isn't ready yet
        print(f"[{app_name}] WARNING: core_system does not have a 'register_tool' method yet.")
    
    # TODO: Automate the loading of all senses and motor skills from their respective directories for scalability
    
    print(f"[{app_name}] Registration complete. Ready for action.\n")
    
    # Return True to signal successful loading
    return True