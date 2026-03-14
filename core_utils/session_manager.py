import json
from datetime import datetime
import os

#########################################
def init_session(model_name: str = 'gemini-2.5-flash') -> dict:
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(".logs", exist_ok=True)
    
    log_file = os.path.join(".logs", f"session_{session_id}_{model_name}.jsonl")
    print(f"[Core] Started new session log: {log_file}")

    log_pipeline_step(log_file, "system", f"Session initialized with model '{model_name}'.")

    return {
        "session_id": session_id,
        "model_name": model_name,
        "log_file": log_file,
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