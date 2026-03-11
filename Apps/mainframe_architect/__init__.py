# apps/mainframe_architect/__init__.py

def register_to_core(core_system, attention_data):
    """
    The main entry point for the Mainframe Architect app.
    This app has special meta-privileges to modify the Mainframe_Zero source code.
    """
    app_name = "Mainframe_Architect"
    task_name = attention_data.get("name", "Unknown Task")
    
    # Notice: We might still have an isolated workspace for logs/temp files, 
    # but the tools themselves will know how to target the root directory.
    workspace_dir = attention_data.get("attention_dir", "Unknown Path")
    
    print(f"\n[{app_name}] System Override: Waking up...")
    print(f"[{app_name}] Focusing on meta-task: '{task_name}'")
    print(f"[{app_name}] WARNING: Operating with root access to Mainframe_Zero system files.")
    
    # TODO: Register meta-senses (e.g., scan_core_files, read_python_ast)
    # TODO: Register meta-motor skills (e.g., generate_app_boilerplate, modify_core_logic)
    
    print(f"[{app_name}] Architect tools registered. Ready to build.\n")
    
    # Return True to signal successful loading
    return True