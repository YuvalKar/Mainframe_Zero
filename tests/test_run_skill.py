import skill_run_mz_blender_function

def run_test():

    print("Starting test for skill_run_mz_blender_function...")
    # Define the exact path to our module inside Blender's environment
    target_module = "mz_blender.actions.io_operations"
    
    # Define the function we want to run
    target_function = "import_fbx"
    
    # Define the arguments. Notice the 'r' before the string to handle Windows slashes
    arguments = {
        "filepath": r"C:\Users\yuval\Documents\NBAYA_projects\Mainframe_Zero\apps\cc_bridge\SM_Resistor_V_QA.fbx"
    }
    
    print(f"Testing execution of {target_module}.{target_function}...")
    
    # Execute the skill
    result = skill_run_mz_blender_function.execute(
        module_path=target_module,
        function_name=target_function,
        kwargs=arguments
    )
    
    # Print the raw result we got back from Blender
    print("\n--- Result from Blender ---")
    print(result)

if __name__ == "__main__":
    run_test()