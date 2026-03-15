import asyncio

import mz_core
from core_utils import session_manager
from core_utils import context_builder

def terminal_chat():
    """
    The main user-facing terminal loop.
    Now supports async streaming from the stateless core.
    """
    print("\n[System: Initializing Mainframe Zero Brain via Core...]")
    try:
        # Ask the core to handle the engine initialization (returns a context dict)
        session_ctx = session_manager.init_session()
    except Exception as e:
        print(f"[System Error: Failed to initialize session - {e}]")
        return

    print("\n========================================================")
    print(" Mainframe Zero Terminal (v13 - Stateless Edition)")
    print("========================================================\n")

    async def run_chat():
        
        # --- NEW: Initialize background workers before starting the loop ---
        try:
            await mz_core.init_workers()
        except Exception as e:
            print(f"[System Error: Failed to initialize background workers - {e}]")
            return

        while True:
            # PRO TIP: Using to_thread prevents input() from blocking the background workers!
            user_input = await asyncio.to_thread(input, "You: ")
            
            if user_input.lower() in ['exit', 'quit']: 
                break
            if user_input.lower() == 'reset':
                print("\n[System: Resetting Mainframe Zero Session...]")
                nonlocal session_ctx
                session_ctx = session_manager.init_session()
                continue
            if not user_input.strip(): 
                continue

            # Step 1: Enrich the user prompt via core
            final_prompt = context_builder.enrich_prompt(session_ctx, user_input)

            # Callback to print immediately to the terminal
            async def print_stream(item):
                item_type = item.get("type")
                content = item.get("content")
                if item_type == "thought": 
                    print(f"\n[AI Thought]: {content}")
                elif item_type == "chat": 
                    print(f"\n[AI Chat]: {content}")
                elif item_type == "action_result": 
                    print(f"[Action Outcome]: {content}")
                elif item_type == "error": 
                    print(f"\n[System Error]: {content}")
                elif item_type == "system": 
                    print(f"\n[System]: {content}")

            # Step 2: Run the stateless loop (now passing the raw user_input too)
            await mz_core.run_agentic_loop(session_ctx, final_prompt, raw_user_input=user_input, emit_callback=print_stream)

    # Boot up the async loop
    asyncio.run(run_chat())

if __name__ == "__main__":
    terminal_chat()