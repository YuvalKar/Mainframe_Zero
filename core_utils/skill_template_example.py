"""
SKILL_TYPE: skill_name_of_the_skill (e.g., "weather_report" if the file is weather_report.py)
PURPOSE: This is a boilerplate template to demonstrate the structure.
         
WHEN TO USE: 
- When creating a new skill from scratch to ensure structural consistency.
         
INPUTS:
- param_one (str): The first required parameter.
- param_two (int, optional): An optional number parameter. Default is 5.
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