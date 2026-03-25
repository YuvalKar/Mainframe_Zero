# Mainframe Zero: Skill/Sense type Creation Guidelines

This document outlines the standard structure for creating new AI skills (tools, senses, synapses etc.) in the project. Since these files are read and executed by an AI agent, the docstring at the top is not just documentation—it is the **system prompt** for that specific tool. If the description is missing or incomplete, the AI will fail to use the tool correctly.

## 1. The Core Rules
* **The Main Function:** The entry point for every skill MUST be named `execute`.
* **Complete Descriptions:** The AI needs to know exactly *what* the tool does, *when* to trigger it, and *what* inputs it expects. Do not leave out parameters.
* **Error Handling:** Always return a dictionary with a `success` boolean and a descriptive `message` so the AI knows if the action worked or failed.

## 2. The Docstring Template
Every skill file must start with a comprehensive docstring structured exactly like this:

```python
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