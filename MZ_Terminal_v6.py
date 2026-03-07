import os
import ast
import json
import importlib.util
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv

# ייבוא ה-Sense החדש וה-Skill Loader
from senses.python_runner_sense import sense_python_function_execution
from core_utils.actions_scanner import get_available_skills

###################################################################################
def enrich_prompt(user_input: str) -> str:
    """
    Main orchestrator for prompt enrichment. 
    Injects attached files, available Skills, and available Senses.
    """
    # 1. Handle @file attachments
    file_matches = re.findall(r'@([\w\.\-\/]+)', user_input)
    enriched_prompt = user_input
    
    if file_matches:
        enriched_prompt += "\n\n--- Attached Files Context ---\n"
        for filename in file_matches:
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        enriched_prompt += f"\n[Content of {filename}]:\n{f.read()}\n"
                    print(f"[System: Attached '{filename}']")
                except Exception as e:
                    print(f"[System Error: Could not read '{filename}': {e}]")
        enriched_prompt += "------------------------------\n"

    # 2. Inject Cerebellum Skills
    current_skills = get_available_skills("cerebellum")
    enriched_prompt += "\n\n[System Context: Current Available Skills in Cerebellum]\n"
    if current_skills:
        for name, desc in current_skills.items():
            enriched_prompt += f"- Skill Name: '{name}'\n  Description & API: {desc}\n\n"
    else:
        enriched_prompt += "No skills available.\n"

    # 3. Inject Senses (Static for now, but listed for the AI)
    enriched_prompt += "\n[System Context: Available Senses]\n"
    enriched_prompt += "- Sense Name: 'sense_python_function_execution'\n"
    enriched_prompt += "  Description: Executes a specific function in a file and returns the result.\n"
    enriched_prompt += "  API: filepath (str), function_name (str), args (list), kwargs (dict)\n"
    
    return enriched_prompt

#########################################################################
def passes_syntax_qa(code_string: str) -> bool:
    try:
        ast.parse(code_string)
        print("[System: QA Passed - Valid Python syntax.]")
        return True
    except SyntaxError:
        return False

###############################################################
load_dotenv()
client = genai.Client()

def terminal_chat():
    try:
        with open("system_prompt.md", "r", encoding="utf-8") as f:
            system_rules = f.read()
    except FileNotFoundError:
        print("[System Error: system_prompt.md not found!]")
        return

    def create_new_chat():
        print("\n[System: Resetting Brain... Memory wiped.]")
        return client.chats.create(
            model='gemini-2.5-flash',
            config=types.GenerateContentConfig(
                system_instruction=system_rules,
                temperature=0.1,
                response_mime_type="application/json",
            )
        )

    chat = create_new_chat()

    print("\n================================================")
    print(" Mainframe Zero Terminal (v6 - Sense & Skill Integration)")
    print("================================================\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() in ['exit', 'quit']: break
        if user_input.lower() == 'reset':
            chat = create_new_chat()
            continue
        if not user_input.strip(): continue

        try:
            # Enrich the prompt with Files, Skills, and Senses
            final_prompt = enrich_prompt(user_input)

            response = chat.send_message(final_prompt)
            ai_data = json.loads(response.text)

            # Extract fields
            thought = ai_data.get("thought_process", "")
            action = ai_data.get("action", "chat")
            content = ai_data.get("content", "")
            
            # Action specific parameters
            skill_name = ai_data.get("skill_name")
            skill_kwargs = ai_data.get("skill_kwargs", {})
            sense_kwargs = ai_data.get("sense_kwargs", {})

            print(f"\n[AI Thought]: {thought}")
            print(f"--- Action: {action} ---")
            if content: print(content)

            # --- ROUTER ---

            # 1. SENSE: Python Function Execution
            if action == "sense_python":
                print(f"[System: Invoking Sense -> sense_python_function_execution]")
                result = sense_python_function_execution(**sense_kwargs)
                
                print(f"Sense Result: {result}\n")
                chat.send_message(f"[Sense Feedback] Result: {json.dumps(result)}")

            # 2. SKILL: Use Cerebellum Skill
            elif action == "use_skill":
                skill_path = os.path.join("cerebellum", f"{skill_name}.py")
                if os.path.exists(skill_path):
                    spec = importlib.util.spec_from_file_location(skill_name, skill_path)
                    skill_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(skill_module)
                    
                    # Human in the loop for skills
                    if input(f"Execute Skill '{skill_name}'? (y/n): ").lower() == 'y':
                        res = skill_module.execute(**skill_kwargs)
                        print(f"Skill Output: {res}\n")
                        chat.send_message(f"[Skill Feedback] {skill_name} Success: {res.get('success')}, Msg: {res.get('message')}")
                else:
                    chat.send_message(f"[Error] Skill '{skill_name}' not found.")

            # 3. LEGACY/DIRECT: Python (Still supported for raw scripts)
            elif action == "python":
                if passes_syntax_qa(content):
                    filename = ai_data.get("target_filename", "generated_script.py")
                    if input(f"Save and run {filename}? (y/n): ").lower() == 'y':
                        with open(filename, "w", encoding="utf-8") as f: f.write(content)
                        # We still use the sense here for consistency
                        res = sense_python_function_execution(filename, "main") if "def main" in content else {"success": True, "msg": "Script saved."}
                        chat.send_message(f"[Execution Feedback] {res}")

        except Exception as e:
            print(f"\n[System Error: {e}]\n")

if __name__ == "__main__":
    terminal_chat()