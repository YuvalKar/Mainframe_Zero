"""
NAME: skill_switch_apps
DESCRIPTION: switch attention to another app and load it. Create new session, return needed date

INPUT:
    app_name (str): The name of the app to switch to.

OUTPUT:
    dict: A dictionary containing the status of the operation.
          - 'success' (bool): True if the content was saved successfully, False otherwise.
          - 'message' (str): A descriptive message indicating the outcome, 
                             including success confirmation or error details.
"""

def execute(app_name: str) -> dict:

    # need to get current attention If we are on the requested app already, do nothin

    # make sure the app is a valid app and we have the folder for it

    # if all is OK Switch attention to new app

    pass