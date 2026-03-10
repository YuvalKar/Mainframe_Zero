import os
import asyncio

# Import our encapsulated core logic module
import mz_core

def terminal_chat():
    """
    The main user-facing terminal loop.
    Now supports async streaming from the core.
    """
    print("\n[System: Initializing Mainframe Zero Brain via Core...]")
    try:
        # Ask the core to handle the engine initialization
        chat = mz_core.create_chat_session()
    except Exception as e:
        print(f"[System Error: Failed to initialize chat session - {e}]")
        return

    print("\n========================================================")
    print(" Mainframe Zero Terminal (v12 - Async Streaming)")
    print("========================================================\n")

    async def run_chat():
        while True:
            user_input = input("You: ")

            if user_input.lower() in ['exit', 'quit']: 
                break
            if user_input.lower() == 'reset':
                print("\n[System: Resetting Mainframe Zero Brain via Core...]")
                nonlocal chat
                chat = mz_core.create_chat_session()
                continue
            if not user_input.strip(): 
                continue

            # Step 1: Enrich the user prompt via core
            final_prompt = mz_core.enrich_prompt(user_input)

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

            # Step 2: Run the loop and watch it print in real-time
            await mz_core.run_agentic_loop(chat, final_prompt, emit_callback=print_stream)

    # Boot up the async loop
    asyncio.run(run_chat())

if __name__ == "__main__":
    terminal_chat()