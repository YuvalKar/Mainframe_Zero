import asyncio
import json
import os
import sys


# Add the parent directory to Python's path so it can find 'workers'
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)


# Adjust the import paths based on your actual project structure
from core_utils.attention_ops import create_attention, load_attention
from workers.attention_worker import AttentionWorker

async def run_test():
    print("--- Starting Attention Worker Test ---")
    
    # 1. Create a dummy attention
    print("\n1. Creating dummy attention...")
    dummy_attn = create_attention(
        name="Weekend Ride Planning",
        tags=["motorcycle", "planning"],
        short_summary="Initial thought about a weekend trip."
    )
    
    if not dummy_attn:
        print("Failed to create attention! Check your DB connection.")
        return
        
    attn_id = dummy_attn['id']
    print(f"Created Attention: {attn_id} - {dummy_attn['name']}")
    
    # 2. Initialize the worker
    print("\n2. Initializing Attention Worker...")
    worker = AttentionWorker()
    
    # Start the worker in the background
    worker_task = asyncio.create_task(worker.start())
    
    # 3. Send an update task
    print("\n3. Sending update task to worker...")
    # Creating a text longer than 200 chars to trigger the SummarizerAgent
    new_text_data = (
        "I'm thinking of riding up north this weekend, maybe towards the Golan Heights. "
        "Need to check the oil and tire pressure before heading out. "
        "Also, maybe find a good place for coffee on the way, somewhere around the Sea of Galilee. "
        "Weather is supposed to be perfect, not too hot. "
        "I should probably pack some light rain gear just in case, you never know with the weather up there. "
        "Will leave early morning to avoid the traffic."
    )
    
    task_data = {
        "attention_id": attn_id,
        "new_data": new_text_data,
        "metadata": {
            "status": "in_progress",
            "tags": ["motorcycle", "planning", "north", "weekend"]
        }
    }
    
    # Add task to the queue
    await worker.add_task(task_data)
    
    # 4. Wait for processing 
    # Giving it 15 seconds to allow the API call to Gemini to complete. 
    # In a real app, you wouldn't sleep, but for a linear test script we need to wait.
    print("\n4. Waiting for worker to process (and call Gemini)...")
    await asyncio.sleep(15) 
    
    # 5. Check the result
    print("\n5. Checking the updated attention in DB...")
    # load_attention will also bump the updated_at timestamp
    updated_attn = load_attention(attn_id)
    
    if updated_attn:
        print("\n--- RESULTS ---")
        print(f"Status: {updated_attn.get('status')}")
        print(f"Tags: {updated_attn.get('tags')}")
        print(f"Short Summary (200 chars expected):\n{updated_attn.get('short_summary')}")
        print(f"Detailed Summary (600 chars expected):\n{updated_attn.get('detailed_summary')}")
    else:
        print("Could not load updated attention.")
    
    # 6. Cleanup
    print("\n6. Shutting down worker...")
    worker.is_running = False
    worker_task.cancel()
    
    try:
        await worker_task
    except asyncio.CancelledError:
        pass
        
    print("\n--- Test Complete ---")

if __name__ == "__main__":
    # Run the async event loop
    asyncio.run(run_test())