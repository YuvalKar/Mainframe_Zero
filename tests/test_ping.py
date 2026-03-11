import sys
import os
import asyncio

# Add the parent directory (project root) to sys.path so Python can find mz_core
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import mz_core

async def run_test():
    print("--- Starting Mainframe Zero Architecture Test ---")

    # 1. Create a dummy attention for testing purposes
    print("\n[Step 1] Creating Attention Context...")
    attn_data = mz_core._attention_manager.create_attention(
        name="Test Blender Ping",
        target_app="blender_for_uefn",
        tags=["test", "ping"]
    )
    attn_id = attn_data["id"]

    # 2. Shift attention to mount the app and prepare dynamic paths
    print(f"\n[Step 2] Shifting Attention to {attn_id}...")
    success = mz_core.shift_attention(attn_id)
    if not success:
        print("Failed to shift attention. Stopping test.")
        return

    # 3. Create an AI chat session
    print("\n[Step 3] Initializing AI Session...")
    chat = mz_core.create_chat_session(model_name='gemini-2.5-flash')

    # 4. Define a callback function to stream the agent's internal process to the console
    async def print_emit(item):
        item_type = item.get("type", "unknown")
        content = item.get("content", "")
        
        if item_type == "thought":
            print(f"\n[AI THOUGHT] {content}")
        elif item_type == "action_result":
            print(f"\n[SYSTEM RESULT] {content}")
        elif item_type == "chat":
            print(f"\n[AI SAYS] {content}")
        elif item_type == "system":
            print(f"\n[SYSTEM LOG] {content}")
        else:
            print(f"\n[{item_type.upper()}] {content}")

    # 5. Formulate the prompt and execute the agentic loop
    prompt = "Please use your available senses to ping the Blender app and tell me if it is awake."
    print(f"\n[Step 4] Sending Prompt: '{prompt}'")
    
    # Quick sanity check to see if the scanner found our new sense
    enriched = mz_core.enrich_prompt(prompt)
    print("\n--- Enriched Prompt Check ---")
    if "sense_ping" in enriched:
        print("SUCCESS: 'sense_ping' was successfully injected into the prompt's context!")
    else:
        print("WARNING: 'sense_ping' is missing from the prompt context. Check your paths.")
    print("-----------------------------\n")

    # Run the actual asynchronous loop
    await mz_core.run_agentic_loop(chat, enriched, emit_callback=print_emit)    
    print("\n--- Test Complete ---")

if __name__ == "__main__":
    # Execute the async main function
    asyncio.run(run_test())