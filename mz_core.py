import os
import json
import importlib.util
import re
import asyncio
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Import utility functions
from core_utils.actions_scanner import get_available_actions

# Load environment variables where the core actually needs them
load_dotenv()

# We can keep a single client instance for the core to use
_client = genai.Client()

def create_chat_session():
    """
    Initializes and returns a new chat session with the specific engine (Gemini).
    The server/terminal don't need to know the implementation details.
    """
    try:
        with open("system_prompt.md", "r", encoding="utf-8") as f:
            system_rules = f.read()
    except FileNotFoundError:
        system_rules = "You are a helpful AI."
        print("[Core Warning: system_prompt.md not found]")

    return _client.chats.create(
        model='gemini-2.5-flash',
        config=types.GenerateContentConfig(
            system_instruction=system_rules,
            temperature=0.1,
            response_mime_type="application/json",
        )
    )

def enrich_prompt(user_input: str) -> str:
    """
    Orchestrates the context injection: Files (@), Skills, and Senses dynamically.
    Returns the enriched string without printing anything to the console.
    """
    file_matches = re.findall(r'@([\w\.\-\/]+)', user_input)
    enriched_prompt = user_input
    
    if file_matches:
        enriched_prompt += "\n\n--- Attached Files Context ---\n"
        for filename in file_matches:
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        enriched_prompt += f"\n[Content of {filename}]:\n{f.read()}\n"
                except Exception as e:
                    # We return the error inside the prompt so the AI knows it failed
                    enriched_prompt += f"\n[System Error: Could not read '{filename}': {e}]\n"
        enriched_prompt += "------------------------------\n"

    # Inject Available Actions (Skills from Cerebellum)
    current_skills = get_available_actions("cerebellum")
    enriched_prompt += "\n\n[System Context: Available Actions in Cerebellum]\n"
    if current_skills:
        for name, desc in current_skills.items():
            enriched_prompt += f"- Action Name: '{name}' (Skill)\n  API: {desc}\n\n"
    else:
        enriched_prompt += "No skills available.\n\n"
    
    # Inject Available Senses
    current_senses = get_available_actions("senses")
    enriched_prompt += "[System Context: Available Senses]\n"
    if current_senses:
        for name, desc in current_senses.items():
            enriched_prompt += f"- Action Name: '{name}' (Sense)\n  API: {desc}\n\n"
    else:
        enriched_prompt += "No senses available.\n\n"

    return enriched_prompt

################################### 
def execute_single_action(action_name: str, action_data: dict) -> str:
    """
    Locates the action file and executes it dynamically. 
    Returns the execution result as a string (no direct prints).
    """
    target_path = None
    
    if os.path.exists(os.path.join("cerebellum", f"{action_name}.py")):
        target_path = os.path.join("cerebellum", f"{action_name}.py")
    elif os.path.exists(os.path.join("senses", f"{action_name}.py")):
        target_path = os.path.join("senses", f"{action_name}.py")
    elif os.path.exists(os.path.join("hippocampus", f"{action_name}.py")):
        target_path = os.path.join("hippocampus", f"{action_name}.py")

    if not target_path:
        return f"Action '{action_name}': Failed (Not Found in any known directory)"
        
    try:
        spec = importlib.util.spec_from_file_location(action_name, target_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        res = module.execute(**action_data)
        return f"Action '{action_name}': {res}"
    except Exception as ex:
        return f"Action '{action_name}': Execution failed - {str(ex)}"

#########################################
async def run_agentic_loop(chat, current_prompt: str, emit_callback=None) -> dict:
    """
    Runs the interaction loop with the AI asynchronously.
    Calls emit_callback(dict) if provided to stream logs in real-time.
    """
    loop_counter = 0
    max_loops = 3 
    interaction_log = []

    # Helper function to log internally and emit to the outside world immediately
    async def log_and_emit(item_type: str, content: str):
        item = {"type": item_type, "content": content}
        interaction_log.append(item)
        if emit_callback:
            await emit_callback(item)

    while True:
        loop_counter += 1
        if loop_counter > max_loops:
            await log_and_emit("system", "Agent reached maximum allowed loops.")
            break

        try:
            # Run the blocking Gemini call in a separate thread so we don't block the WebSocket
            response = await asyncio.to_thread(chat.send_message, current_prompt)
            ai_data = json.loads(response.text)
            
            thought = ai_data.get("thought_process", "")
            action_type = ai_data.get("action", "chat")
            chat_text = ai_data.get("chat")
            actions_list = ai_data.get("act", [])

            if thought:
                await log_and_emit("thought", thought)
            if chat_text:
                await log_and_emit("chat", chat_text)

            if action_type == "chat" or not actions_list:
                break

            execution_summary = []
            for act_item in actions_list:
                action_name = act_item.get("name")
                action_data = act_item.get("data", {})
                
                await log_and_emit("system", f"Initiating Action -> {action_name}")
                
                result_string = execute_single_action(action_name, action_data)
                execution_summary.append(result_string)
                
                await log_and_emit("action_result", result_string)

            if execution_summary:
                current_prompt = "[System Sensory Feedback]\n" + "\n".join(execution_summary)
            else:
                current_prompt = "[System: Actions resulted in no feedback.]"

        except json.JSONDecodeError:
            await log_and_emit("error", f"Failed to parse AI response as JSON. Raw response: {response.text}")
            break
        except Exception as e:
            await log_and_emit("error", f"System Error during agentic loop: {str(e)}")
            break
            
    return {"status": "completed", "log": interaction_log}