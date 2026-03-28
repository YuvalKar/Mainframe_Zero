# apps/blender_for_uefn/__init__.py

def register_to_core(core_system, attention_data):
    """
    The main entry point for the Blender UEFN app.
    This function is called by the Core when Attention shifts to this app.
    """
    app_name = "blender"  # Using a unique character to ensure distinctiveness in logs
    task_name = attention_data.get("name", "Unknown Task")
    workspace_dir = attention_data.get("attention_dir", "Unknown Path")
    
    print(f"\n[{app_name}] Waking up...")
    print(f"[{app_name}] Focusing on task: '{task_name}'")
    print(f"[{app_name}] Workspace mounted at: {workspace_dir}")

    # Tools (Senses and Motor Skills) are automatically discovered by the Core's
        
    # Return True to signal successful loading
    return True