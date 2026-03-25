"""
NAME: skill_name_of_the_skill_or_sense (e.g., "sense_weather_report" if the file is sense_weather_report.py)
DESCRIPTION: A brief, concise description of the skill or sense.
         
WHEN TO USE:
- When to use this skill or sense.
         
INPUTS:
- param_one (str): The first required parameter.
- param_two (int, optional): An optional number parameter. Default is 5.

OUTPUT: dict: A dictionary containing the status of the operation, optional - data
- 'success' (bool): True if the content was saved successfully, False otherwise.
- 'message' (str): A descriptive message indicating the outcome, including success confirmation or error details.
- 'data' (dict): the data retrived
"""

def execute(param_one: str, param_two: int = 5) -> dict:
    # 1. Validate inputs (The AI might sometimes hallucinate or miss parameters)
    if not param_one:
        return {"success": False, "message": "Missing required input: param_one."}

    try:
        # 2. Perform the logic
        result_data = f"Processed {param_one} with {param_two}"
        
        # 3. Return a standardized dictionary
        return {
            "success": True, 
            "message": f"Skill executed successfully.",
            "data": result_data
        }

    except Exception as e:
        # 4. Catch errors gracefully so the AI agent doesn't crash
        return {"success": False, "message": f"Failed to execute skill: {str(e)}"}