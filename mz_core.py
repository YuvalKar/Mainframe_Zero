import os
import json
import importlib.util
import re
import asyncio
from google import genai
from google.genai import types
from dotenv import load_dotenv
from datetime import datetime
from attention_manager import AttentionManager
import sys

# Import utility functions
from core_utils.actions_scanner import get_available_actions

# Load environment variables where the core actually needs them
load_dotenv()

# We can keep a single client instance for the core to use
_client = genai.Client()

# Global variable to hold the current session's log file path
_current_log_file = None

# Initialize the Attention Manager and state variables
_attention_manager = AttentionManager()
_active_attention = None
_active_app_module = None

def shift_attention(attention_id: str) -> bool:
    """
    Loads an Attention context and dynamically mounts its required App.
    """
    global _active_attention, _active_app_module
    
    # 1. Load the attention metadata
    attn_data = _attention_manager.load_attention(attention_id)
    if not attn_data:
        print(f"[Core Error] Attention ID '{attention_id}' not found.")
        return False
        
    _active_attention = attn_data
    app_name = attn_data.get("required_app")
    
    print(f"\n[Core] Shifting attention to: '{attn_data.get('name')}'")
    print(f"[Core] Required App: {app_name}")
    
    # 2. Dynamically import the app module
    try:
        # We assume apps are located in the 'apps' directory
        module_path = f"apps.{app_name}"
        app_module = importlib.import_module(module_path)
        
        # 3. Call the app's contract function to register it
        if hasattr(app_module, 'register_to_core'):
            # Pass the current core module (sys.modules[__name__]) and the context
            current_core = sys.modules[__name__]
            success = app_module.register_to_core(current_core, attn_data)
            
            if success:
                _active_app_module = app_module
                return True
            else:
                print(f"[Core Error] App '{app_name}' failed during registration.")
                return False
        else:
            print(f"[Core Error] App '{app_name}' is missing the 'register_to_core' function.")
            return False
            
    except ImportError as e:
        print(f"[Core Error] Could not load app '{app_name}'. Is it in the 'apps' folder? Error: {e}")
        return False

def create_chat_session(model_name: str = 'gemini-2.5-flash'):
    global _current_log_file
    
    try:
        with open("system_prompt.md", "r", encoding="utf-8") as f:
            system_rules = f.read()
    except FileNotFoundError:
        system_rules = "You are a helpful AI."
        print("[Core Warning: system_prompt.md not found]")

    # Generate a unique ID for this specific session based on time
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(".logs", exist_ok=True)
    
    # Set the log file name for this specific chat instance
    _current_log_file = os.path.join(".logs", f"session_{session_id}_{model_name}.jsonl")
    print(f"[Core] Started new session log: {_current_log_file}")

    log_pipeline_step("system", f"Chat session initialized with model '{model_name}' and system rules loaded.")

    return _client.chats.create(
        model=model_name,
        config=types.GenerateContentConfig(
            system_instruction=system_rules,
            temperature=0.1,
            response_mime_type="application/json",
        )
    )

def log_pipeline_step(step_type: str, content: any):
    """
    Appends a raw interaction step to the active session's JSONL log file.
    """
    if not _current_log_file:
        return # Safety check: don't log if session isn't initialized
        
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "step_type": step_type,
        "content": content
    }
    
    try:
        with open(_current_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[Core Warning] Failed to write to pipeline log: {e}")


def enrich_prompt(user_input: str) -> str:
    """
    Orchestrates the context injection: Files (@), Skills, and Senses dynamically.
    Returns the enriched string without printing anything to the console.
    """
    # 1. Bring in the global attention state to know which app is running
    global _active_attention 
    
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

    # 2. Determine the active app name to build dynamic paths
    app_name = None
    if _active_attention:
        app_name = _active_attention.get("required_app")

    # 3. Inject Available Actions (Skills from Cerebellum)
    current_skills = get_available_actions("cerebellum") # Scan core directory
    
    if app_name:
        # Scan app-specific directory and merge into current_skills
        app_skills_path = os.path.join("apps", app_name, "cerebellum")
        app_skills = get_available_actions(app_skills_path)
        current_skills.update(app_skills) 

    enriched_prompt += "\n\n[System Context: Available Actions in Cerebellum]\n"
    if current_skills:
        for name, desc in current_skills.items():
            enriched_prompt += f"- Action Name: '{name}' (Skill)\n  API: {desc}\n\n"
    else:
        enriched_prompt += "No skills available.\n\n"
    
    # 4. Inject Available Senses
    current_senses = get_available_actions("senses") # Scan core directory
    
    if app_name:
        # Scan app-specific directory and merge into current_senses
        app_senses_path = os.path.join("apps", app_name, "senses")
        app_senses = get_available_actions(app_senses_path)
        current_senses.update(app_senses)

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
    Now deeply logs all backend activity and frontend emits to the JSONL file.
    """
    loop_counter = 0
    max_loops = 3 
    interaction_log = []

    # Helper function to log internally, save to JSONL, and emit to the outside world
    async def log_and_emit(item_type: str, content: str):
        item = {"type": item_type, "content": content}
        interaction_log.append(item)
        
        # Save to our pipeline log file so we have a permanent record
        log_pipeline_step(f"ui_emit_{item_type}", content)
        
        if emit_callback:
            await emit_callback(item)

    # Log the full enriched prompt before we even enter the loop
    log_pipeline_step("backend_enriched_prompt", current_prompt)

    while True:
        loop_counter += 1
        if loop_counter > max_loops:
            await log_and_emit("system", "Agent reached maximum allowed loops.")
            break

        try:
            # Log the exact prompt being sent to the AI API in this iteration
            log_pipeline_step("backend_api_request", {"loop": loop_counter, "prompt": current_prompt})

            # Run the blocking Gemini call in a separate thread so we don't block the WebSocket
            response = await asyncio.to_thread(chat.send_message, current_prompt)
            
            # Log the raw string response straight from the AI, before any JSON parsing
            log_pipeline_step("backend_api_response_raw", {"loop": loop_counter, "raw_text": response.text})

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
                log_pipeline_step("backend_loop_exit", "Action type is 'chat' or no actions provided. Exiting loop.")
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
            
    log_pipeline_step("backend_loop_completed", {"total_loops": loop_counter})
    
    return {"status": "completed", "log": interaction_log}