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

#########################################
def get_system_prompt() -> str:
    # Load system rules from file for each stateless request
    try:
        with open("system_prompt.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print("[Core Warning: system_prompt.md not found]")
        return "You are a helpful AI."

#########################################
def init_session(model_name: str = 'gemini-2.5-flash') -> dict:
    """
    Initializes a session context dictionary instead of a stateful chat object.
    """
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(".logs", exist_ok=True)
    
    log_file = os.path.join(".logs", f"session_{session_id}_{model_name}.jsonl")
    print(f"[Core] Started new session log: {log_file}")

    # Pass the specific log_file to our logger
    log_pipeline_step(log_file, "system", f"Session initialized with model '{model_name}'.")

    # Return a context dictionary instead of a Gemini Chat object
    return {
        "session_id": session_id,
        "model_name": model_name,
        "log_file": log_file
    }

#########################################
def log_pipeline_step(log_file: str, step_type: str, content: any):
    """
    Appends a raw interaction step to the specified session's JSONL log file.
    """
    if not log_file:
        return 
        
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "step_type": step_type,
        "content": content
    }
    
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[Core Warning] Failed to write to pipeline log: {e}")

########################################
def enrich_prompt(user_input: str) -> str:
    """
    Orchestrates the context injection: Files (@), Skills, and Senses dynamically.
    Returns the enriched string without printing anything to the console.
    """
    # 1. Bring in the global attention state to know which app is running
    global _active_attention 
    
    file_matches = re.findall(r'@([\w\.\-\/\\]+)', user_input)
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

    #TBD YUVAL - inject skills only once in attention shift, not on every prompt enrichment. We can keep track of this in the attention state.!!!!!
    
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
    Checks app-specific directories first, then falls back to core directories.
    Returns the execution result as a string (no direct prints).
    """
    global _active_attention
    target_path = None
    app_name = None

    if _active_attention:
        app_name = _active_attention.get("required_app")

    # 1. Define the possible directory paths to search
    search_paths = []

    # App-specific paths get priority (specialized skills over general ones)
    if app_name:
        search_paths.extend([
            os.path.join("apps", app_name, "cerebellum"),
            os.path.join("apps", app_name, "senses"),
            # os.path.join("apps", app_name, "hippocampus")
        ])

    # Core paths as fallback
    search_paths.extend([
        "cerebellum",
        "senses",
        # "hippocampus"
    ])

    # 2. Search for the action file in the defined paths
    for base_path in search_paths:
        potential_path = os.path.join(base_path, f"{action_name}.py")
        if os.path.exists(potential_path):
            target_path = potential_path
            break # Found the file, stop searching

    if not target_path:
        return f"Action '{action_name}': Failed (Not Found in any known directory)"
        
    try:
        # 3. Dynamically load and execute the module
        spec = importlib.util.spec_from_file_location(action_name, target_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        res = module.execute(**action_data)
        return f"Action '{action_name}': {res}"
    except Exception as ex:
        return f"Action '{action_name}': Execution failed - {str(ex)}"
    
############################################
def execute_direct(action_name: str, action_data: dict) -> dict:
    """
    Sister function to execute_single_action.
    Executes a sense/skill and returns the RAW dictionary result.
    Perfect for UI requests via WebSocket.
    """
    global _active_attention
    target_path = None
    app_name = None

    # 1. Check if there's an active app based on current attention
    if _active_attention:
        app_name = _active_attention.get("required_app")

    # 2. Define the search paths (App specific first, then core)
    search_paths = []
    if app_name:
        search_paths.extend([
            os.path.join("apps", app_name, "cerebellum"),
            os.path.join("apps", app_name, "senses"),
        ])

    search_paths.extend(["cerebellum", "senses"])

    # 3. Search for the action file
    for base_path in search_paths:
        potential_path = os.path.join(base_path, f"{action_name}.py")
        if os.path.exists(potential_path):
            target_path = potential_path
            break 

    if not target_path:
        return {"success": False, "message": f"Action '{action_name}' Not Found."}
        
    try:
        # 4. Dynamically load and execute
        spec = importlib.util.spec_from_file_location(action_name, target_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 5. Return the raw data directly (No string wrapping!)
        return module.execute(**action_data)
        
    except Exception as ex:
        return {"success": False, "message": f"Execution failed: {str(ex)}"}
    
#########################################
async def run_agentic_loop(session_context: dict, current_prompt: str, emit_callback=None) -> dict:
    """
    Runs the interaction loop statelessly. 
    It receives the session context (where to log, what model to use) and the prompt.
    """
    # Extract session variables
    model_name = session_context.get("model_name", "gemini-2.5-flash")
    log_file = session_context.get("log_file")
    system_rules = get_system_prompt()
    
    loop_counter = 0
    max_loops = 3 
    interaction_log = []

    async def log_and_emit(item_type: str, content: str):
        item = {"type": item_type, "content": content}
        interaction_log.append(item)
        
        # Pass the log_file explicitly
        log_pipeline_step(log_file, f"ui_emit_{item_type}", content)
        
        if emit_callback:
            await emit_callback(item)

    log_pipeline_step(log_file, "backend_enriched_prompt", current_prompt)

    while True:
        loop_counter += 1
        if loop_counter > max_loops:
            await log_and_emit("system", "Agent reached maximum allowed loops.")
            break

        try:
            log_pipeline_step(log_file, "backend_api_request", {"loop": loop_counter, "prompt": current_prompt})

            # THE ENGINE SWAP: Stateless call instead of chat.send_message
            def _call_gemini():
                return _client.models.generate_content(
                    model=model_name,
                    contents=current_prompt, # Sending ONLY the current prompt (Stateless!)
                    config=types.GenerateContentConfig(
                        system_instruction=system_rules,
                        temperature=0.1,
                        response_mime_type="application/json",
                    )
                )

            # Run the blocking call in a separate thread
            response = await asyncio.to_thread(_call_gemini)
            
            log_pipeline_step(log_file, "backend_api_response_raw", {"loop": loop_counter, "raw_text": response.text})

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
                log_pipeline_step(log_file, "backend_loop_exit", "Action type is 'chat' or no actions provided. Exiting loop.")
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
            
    log_pipeline_step(log_file, "backend_loop_completed", {"total_loops": loop_counter})
    
    return {"status": "completed", "log": interaction_log}