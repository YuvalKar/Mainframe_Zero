import json
import asyncio

from dotenv import load_dotenv

from core_utils.hud_streamer import send_hud_error

# Import utility functions
from core_utils.context_builder import get_system_prompt
from core_utils.actions_ops import execute_single_action
from core_utils.session_manager import log_pipeline_step

# Import memory DB functions for short-term history
from database.db_chat_history import save_chat_history_turn

# Workers
from workers.summarizer_agent import SummarizerAgent
from workers.summarize_doc_agent import SummarizeDocAgent
from workers.attention_worker import AttentionWorker

# Load environment variables where the core actually needs them
load_dotenv()

from llm_router import generate_ai_response

# ==========================================
# BACKGROUND WORKERS INITIALIZATION
# ==========================================
# Keeping references to workers and background tasks to prevent garbage collection
from workers.worker_registry import active_workers, worker_tasks

async def init_workers():
    """
    Initializes all background agents, injects dependencies, and starts their queues.
    Ensures that the `active_workers` registry is populated with worker instances.
    """ 
    print("[Core] Initializing background workers...")
    
    # 1. Initialize the shared summarizer ONCE
    shared_summarizer = SummarizerAgent()
    
    # 2. Initialize other workers with dependency injection (passing the shared summarizer)
    doc_agent = SummarizeDocAgent(summarizer=shared_summarizer)
    attention_worker = AttentionWorker(summarizer=shared_summarizer)
    
    # 3. Store worker instances in the shared active_workers registry
    active_workers["summarizer"] = shared_summarizer
    active_workers["doc_agent"] = doc_agent
    active_workers["attention"] = attention_worker
    
    # 4. Turn them on (start the background queue loops)
    worker_tasks.append(asyncio.create_task(shared_summarizer.start()))
    worker_tasks.append(asyncio.create_task(doc_agent.start()))
    worker_tasks.append(asyncio.create_task(attention_worker.start()))
    
    print("[Core] All background workers are online and listening.")
    
#########################################
async def run_agentic_loop(session_context: dict, current_prompt: str, raw_user_input: str = "", emit_callback=None) -> dict:
    """
    Runs the interaction loop statelessly. 
    It receives the session context (where to log, what model to use) and the prompt.
    """
    # Extract session variables
    log_file = session_context.get("log_file")
    system_rules = get_system_prompt()
    
    loop_counter = 0
    max_loops = 3 
    interaction_log = []
    
    # We will accumulate all actions and sensory feedback across the loops for this single user turn
    turn_actions_log = []

    async def log_and_emit(item_type: str, content: str):
        item = {"type": item_type, "content": content}
        interaction_log.append(item)
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

            # Call the new unified LLM router
            ai_response_text = await generate_ai_response(
                session_context=session_context, 
                prompt=current_prompt, 
                system_rules=system_rules
            )

            # --- NEW SAFETY CHECK ---
            if not ai_response_text:
                await log_and_emit("error", "Received an empty response from the AI engine.")
                log_pipeline_step(log_file, "backend_error", "ai_response_text was empty or None.")
                break

            log_pipeline_step(log_file, "backend_api_response_raw", {"loop": loop_counter, "raw_text": ai_response_text})

            # Parse the string returned by the router into a dictionary
            ai_data = json.loads(ai_response_text)
            
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
                
                # Save the complete turn to the PostgreSQL database before exiting
                if raw_user_input:
                    session_id = session_context.get("session_id")
                    save_chat_history_turn(
                        session_id=session_id, 
                        user_input=raw_user_input, 
                        actions=turn_actions_log, 
                        ai_response=chat_text or ""
                    )
                break   

            execution_summary = []
            for act_item in actions_list:
                action_name = act_item.get("name")
                action_data = act_item.get("data", {})
                
                await log_and_emit("system", f"Initiating Action -> {action_name}")
                
                result_string = execute_single_action(session_context, action_name, action_data)
                execution_summary.append(result_string)
                
                await log_and_emit("action_result", result_string)
                
                # Record the specific action and its sensory feedback
                turn_actions_log.append({
                    "action": action_name,
                    "result": result_string
                })

            if execution_summary:
                # add to prompt for the next loop so the AI can reflect on the results of its actions
                current_prompt += "\n\n[System Sensory Feedback]\n" + "\n".join(execution_summary)
                current_prompt += "\n\n[System Directive: Continue executing or respond to the user based on the original request.]"
            else:
                current_prompt += "\n\n[System: Actions resulted in no feedback.]"


        except json.JSONDecodeError:
            await log_and_emit("error", f"Failed to parse AI response as JSON. Raw response: {ai_response_text}")
            send_hud_error("mz_core_error", "Failed to parse AI response. Check logs for details.")
            break
        except Exception as e:
            await log_and_emit("error", f"System Error during agentic loop: {str(e)}")
            send_hud_error("mz_core_error", "An unexpected error occurred. Check logs for details.")
            break
            
    log_pipeline_step(log_file, "backend_loop_completed", {"total_loops": loop_counter})
    
    return {"status": "completed", "log": interaction_log}