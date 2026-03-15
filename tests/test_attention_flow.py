import asyncio
import os
import sys
from dotenv import load_dotenv
from core_utils.context_builder import enrich_prompt
from workers.worker_registry import active_workers
from workers.summarize_doc_agent import SummarizeDocAgent
from workers.summarizer_agent import SummarizerAgent

# Load environment variables so the SummarizerAgent has the Gemini API Key
load_dotenv()

def get_mock_session(file_path):
    return {
        "session_id": "test_session_123",
        "model_name": "gemini-2.0-flash",
        "client_context": {
            "activeDocument": file_path,
            "attentionShelf": []
        }
    }

async def run_test(target_file):
    if not os.path.exists(target_file):
        print(f"[Test] Error: File '{target_file}' does not exist.")
        return

    print("[Test] Initializing Workers...")
    shared_sum = SummarizerAgent()
    doc_agent = SummarizeDocAgent(summarizer=shared_sum)
    active_workers["doc_agent"] = doc_agent
    
    # FIX: We must start the background loops for BOTH agents
    sum_task = asyncio.create_task(shared_sum.start())
    doc_task = asyncio.create_task(doc_agent.start())
    
    # Give the loops a split second to spin up
    await asyncio.sleep(0.1)

    session = get_mock_session(target_file)

    # --- FIRST RUN ---
    print("\n" + "="*50)
    print(f"[Test] FIRST RUN: Processing {target_file}")
    
    prompt_1 = enrich_prompt(session, f"Check this file @{target_file}")
    
    print("\n--- Resulting Prompt 1 (Partial) ---")
    context_start = prompt_1.find("--- Context")
    context_end = prompt_1.find("---------- END")
    if context_start != -1:
        print(prompt_1[context_start:context_end])
    
    print("\n[Test] Yielding to let workers pick up tasks...")
    # This sleep is crucial to let loop.create_task inside attention_ops enqueue the item
    await asyncio.sleep(0.5) 
    
    print("[Test] Waiting for Document Agent to finish its queue...")
    await doc_agent.queue.join()
    
    print("[Test] Waiting for Summarizer Agent to finish its queue (API calls)...")
    await shared_sum.queue.join()
    
    print("[Test] All workers finished. DB should be updated now.")

    # --- SECOND RUN ---
    print("\n" + "="*50)
    print("[Test] SECOND RUN: Checking DB Cache...")
    
    # Clear the working_files from the session cache to force it to read from DB (Layer 2)
    session["active_attention"]["working_files"] = {}
    
    prompt_2 = enrich_prompt(session, "Show me the file again.")
    
    print("\n--- Resulting Prompt 2 (Partial) ---")
    context_start = prompt_2.find("--- Context")
    context_end = prompt_2.find("---------- END")
    if context_start != -1:
        print(prompt_2[context_start:context_end])

    # Cleanup
    sum_task.cancel()
    doc_task.cancel()
    print("\n[Test] Completed.")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "core_utils/context_builder.py"
    asyncio.run(run_test(target))