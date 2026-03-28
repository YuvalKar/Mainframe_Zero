"""
NAME: sense_get_installed_apps
DESCRIPTION: return Apps installed in system

INPUTS:
- None
OUTPUTS:dict
- success (bool): Indicates whether the operation was successful.
- message (str): A descriptive message about the operation's outcome.
- data (dict, optional): If successful, Apps names and description
"""
import os
import json

def execute() -> dict:

    try:
        # The 'senses' folder is inside the project root. We need to go one level up to find the 'apps' folder.
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        app_folder = os.path.join(project_root, "apps")

        if not os.path.isdir(app_folder):
            return {
                "success": False,
                "message": f"Error: 'apps' directory not found at expected path '{app_folder}'."
            }

        # Get all subdirectories in the 'apps' folder
        app_names = [name for name in os.listdir(app_folder) if os.path.isdir(os.path.join(app_folder, name))]

        apps_data = {}
        for app_name in app_names:
            settings_path = os.path.join(app_folder, app_name, 'settings.json')

            # If a settings file doesn't exist for this app, skip it.
            if not os.path.isfile(settings_path):
                continue

            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    apps_data[app_name] = json.load(f)
            except (IOError, json.JSONDecodeError):
                # If the file exists but is unreadable or not valid JSON, skip it.
                continue

        return {
            "success": True,
            "message": f"Successfully retrieved settings for {len(apps_data)} installed apps.",
            "data": apps_data
        }
    except Exception as e:
        return {"success": False, "message": f"An error occurred: {str(e)}"}