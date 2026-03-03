import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables from the .env file before doing anything else
load_dotenv()

# Initialize the Gemini client. 
# It automatically looks for the GEMINI_API_KEY environment variable.
client = genai.Client()

def generate_minimal_code(user_request: str) -> str:
    # This is our "System Prompt" - setting the rigid rules for the AI
    system_rules = """
    You are a strictly technical Python code generator. 
    Return ONLY raw, valid Python code.
    Do NOT wrap the code in markdown blocks (like ```python).
    Do NOT add any explanations, greetings, or notes before or after the code.
    """
    
    # We call the model (using flash for fast, straightforward coding tasks)
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=user_request,
        config=types.GenerateContentConfig(
            system_instruction=system_rules,
            temperature=0.1, # Keep it low so the AI doesn't get too "creative" with syntax
        )
    )
    
    return response.text

if __name__ == "__main__":
    print("Sending the spark...")
    
    # Our very first request
    my_prompt = "Write a python script that prints 'Hello Mainframe Zero', and calculates 5 times 5."
    
    try:
        # Get the code from the AI
        ai_generated_code = generate_minimal_code(my_prompt)
        
        print("\n--- AI Output ---")
        print(ai_generated_code)
        print("-----------------\n")
        
        # The slightly crazy/fun part: actually running the string as code
        # WARNING: In a real system, we'd QA this first!
        print("Executing the AI's code:\n")
        exec(ai_generated_code)
        
    except Exception as e:
        print(f"Something broke: {e}")