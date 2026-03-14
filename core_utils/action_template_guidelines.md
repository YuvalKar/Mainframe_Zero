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
SKILL / SENSE: <skill_name>
PURPOSE: <A clear, 1-2 sentence description of what this tool achieves. Explain the 'Why'>
         
WHEN TO USE: 
- <Specific scenario 1 where the AI should call this tool>
- <Specific scenario 2>
- DO NOT use this when... <optional negative constraint to prevent misuse>

INPUTS:
- <param_name> (<type>): <Description of the parameter>. Default is <X> if applicable.
- <param_name> (<type>, optional): <Description>.
"""