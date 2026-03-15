import asyncio
import os
import sys  

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workers.summarizer_agent import SummarizerAgent
from workers.summarize_doc_agent import SummarizeDocAgent

async def run_lab_test():
    # 1. Check if a file path was passed as an argument in the terminal
    if len(sys.argv) < 2:
        print("[Lab Test] Error: Please provide a file path.")
        print("[Lab Test] Usage: python test_workers_lab.py <path_to_file>")
        return
        
    # 2. Get the file path from the command line argument
    target_file_path = sys.argv[1]
    
    # 3. Verify the file actually exists before we send it to the queue
    if not os.path.exists(target_file_path):
        print(f"[Lab Test] Error: The file '{target_file_path}' does not exist.")
        return

    print(f"\n[Lab Test] Booting up isolated workers for file: {target_file_path}")
    
    # 4. Initialize our shared summarizer and the doc agent
    shared_summarizer = SummarizerAgent()
    doc_agent = SummarizeDocAgent(summarizer=shared_summarizer)
    
    # 5. Start their background queues
    tasks = [
        asyncio.create_task(shared_summarizer.start()),
        asyncio.create_task(doc_agent.start())
    ]
    
    # Give them a tiny fraction of a second to print their "online" messages 
    # before we clutter the console
    await asyncio.sleep(0.1)
    
    print("\n[Lab Test] Submitting task to Doc Agent's queue...")

    try:
        # 6. Throw it into the queue and get the beeper
        beeper = await doc_agent.add_task({"file_path": target_file_path})
        
        print("[Lab Test] Task submitted! Waiting for the beeper to ring...\n")
        
        # 7. Wait for the result
        result = await beeper
        
        print("================ TEST RESULT ================")
        # Using pprint to make the dictionary output easily readable
        print(result, width=100)
        print("=============================================\n")
        print("[Lab Test] Success! The workers processed the task correctly.")

    except Exception as e:
        print(f"\n[Lab Test] Error during execution: {e}")
        
    finally:
        # 8. Clean up: cancel the background tasks to exit gracefully
        print("[Lab Test] Cleaning up the lab...")
        for task in tasks:
            task.cancel()
            
        print("[Lab Test] Test complete. Shutting down.")

if __name__ == "__main__":
    # We wrap the run with a try-except to catch the intentional cancellation 
    # of tasks at the end without throwing an ugly error to the terminal
    try:
        asyncio.run(run_lab_test())
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        print("\n[Lab Test] Process interrupted by user.")