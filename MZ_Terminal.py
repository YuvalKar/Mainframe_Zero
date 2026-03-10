from google import genai
from google.genai import types
from dotenv import load_dotenv

# Import our new core logic module
import mz_core

load_dotenv()
client = genai.Client()

def terminal_chat():
    """
    The main user-facing terminal loop.
    Now acting purely as a CLI client using mz_core.
    """
    try:
        with open("system_prompt.md", "r", encoding="utf-8") as f:
            system_rules = f.read()
    except FileNotFoundError:
        print("[System Error: system_prompt.md not found!]")
        return

    def create_new_chat():
        print("\n[System: Resetting Mainframe Zero Brain...]")
        return client.chats.create(
            model='gemini-2.5-flash',
            config=types.GenerateContentConfig(
                system_instruction=system_rules,
                temperature=0.1,
                response_mime_type="application/json",
            )
        )

    chat = create_new_chat()

    print("\n========================================================")
    print(" Mainframe Zero Terminal (v10 - Core Extracted)")
    print("========================================================\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() in ['exit', 'quit']: 
            break
        if user_input.lower() == 'reset':
            chat = create_new_chat()
            continue
        if not user_input.strip(): 
            continue

        # Step 1: Enrich the user prompt via core
        final_prompt = mz_core.enrich_prompt(user_input)

        # Step 2: Run the agentic loop via core and capture the result
        result = mz_core.run_agentic_loop(chat, final_prompt)
        
        # Step 3: Parse and print the returned log to keep the CLI alive and informative
        for item in result.get("log", []):
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


if __name__ == "__main__":
    terminal_chat()