"""
AI INSTRUCTIONS & MODULE CONTEXT
File: llm_router.py
Purpose: This module acts as the central switchboard (router) for all LLM calls.
It is designed to keep the main agentic loop in mz_core.py clean and stateless.

Key Responsibilities:
1. Routing: Direct requests to either cloud APIs (e.g., Gemini) or local 
   models (e.g., GGUF via llama.cpp) based on 'model_family' in session_context.
2. Resource Management: Local models are kept loaded in memory for performance 
   during the conversation loop. VRAM cleanup (using del and gc.collect()) 
   is triggered ONLY when switching to a different local model or upon 
   system shutdown.
3. Unified Output: Ensure all responses return as a standardized text string, 
   ideally a valid JSON format, so the main loop can parse it consistently.

Future AIs modifying this file: Keep model-specific imports (like llama_cpp) 
scoped to their specific functions if possible, to avoid unnecessary memory 
overhead when using lightweight cloud APIs.
"""
from google import genai
from google.genai import types
from dotenv import load_dotenv
from core_utils.hud_streamer import send_hud_gauge, send_hud_text, send_hud_error


import asyncio
import gc

load_dotenv()

_client = genai.Client()

# Global variables to manage local model state and prevent reloading
_current_local_model_path = None
_current_local_llm = None


# Key: The name used by the front side
AVAILABLE_MODELS = {
    "Gemini 2.5 Flash": {     # The first is the defoult model
        "family": "gemini",
        "name": "gemini-2.5-flash",
        "description" : "best for quick chat",
        "max_tokens": 50000
    },
    "Gemini 2.5 Flash Lite": {
        "family": "gemini",
        "name": "gemini-2.5-flash-lite",
        "description" : "for quick chat",
        "max_tokens": 50000

    },
    "Gemini 2.5 Pro": {
        "family": "gemini",
        "name": "gemini-2.5-pro",
        "description" : "best for code",
        "max_tokens": 100000
    },
    "Blender Local LLM": {
        "family": "local",
        "name": "BlenderLLM.Q4_K_M",
        "path": r"C:\LocalAI\Models\BlenderLLM.Q4_K_M.gguf",
        "description" : "best Blender script generator",
        "max_tokens": 4096
    }
    # You can add more models here in the future
}

#############################################
def get_available_models():
    return AVAILABLE_MODELS


###############################################
async def generate_ai_response(session_context: dict, prompt: str, system_rules: str) -> str:
    """
    Main entry point for generating AI responses.
    Routes the request to the appropriate LLM handler based on the AVAILABLE_MODELS dictionary.
    """
    # We now only need the key from the session context
    model_key = session_context.get("model_name", "gemini-2.5-flash")
    
    # Fetch the model's configuration from our local dictionary
    model_config = AVAILABLE_MODELS.get(model_key)
    
    if not model_config:
        raise ValueError(f"[Router Error] Unknown model key requested: {model_key}")
        
    model_family = model_config["family"]

    # Route based on the family, passing the actual path/name to the handlers
    if model_family == "gemini":
        return await _call_gemini_api(model_config, prompt, system_rules)
    elif model_family == "local":
        return await _call_local_llama(model_config, prompt, system_rules)
    else:
        send_hud_error("ROUTER_ERROR", f"Unknown model family: {model_family} for key: {model_key}")
        raise ValueError(f"[Router Error] Unknown model_family: {model_family} for key: {model_key}")
    

########################################
async def _call_gemini_api(model_config: dict, prompt: str, system_rules: str) -> str:
    """
    Handles communication with Google's Gemini API.
    Uses the existing globally initialized client if possible.
    """
    model_name = model_config.get("name")

    def _call_gemini():
        return _client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_rules,
                temperature=0.1,
                response_mime_type="application/json",
            )
        )

    response = await asyncio.to_thread(_call_gemini)    

    # Extract and print token usage details safely
    if response and hasattr(response, 'usage_metadata') and response.usage_metadata:
        prompt_tokens = response.usage_metadata.prompt_token_count

        # Calculate and print the usage percentage based on the model's safe limit
        max_tokens = model_config.get("max_tokens")
        usage_percent = (prompt_tokens / max_tokens) * 100
        # print(f"Capacity Used: {usage_percent:.2f}% (Safe Limit: {max_tokens})")
            
        send_hud_gauge("PROMPT", usage_percent, "Prompt Tokens")

    # Ensure we return only the text, not the entire response object
    if not response or not response.text:
        send_hud_text("ROUTER_WARNING", "Received empty response from Gemini API.",level="error")
        return ""
    return response.text

############################################
async def _call_local_llama(model_config: dict, prompt: str, system_rules: str) -> str:
    """
    Handles loading and generating text with local GGUF models via llama.cpp.
    Keeps the model in memory until the requested model_name (path) changes.
    """
    global _current_local_model_path, _current_local_llm
    
    # Import locally to save resources if only using cloud APIs
    from llama_cpp import Llama

    model_path = model_config.get("path")
    
    # Check if we need to load a new model
    if _current_local_model_path != model_path:
        print(f"[Router] Loading local model from: {model_path}")
        
        # Clear existing model from VRAM if one exists
        if _current_local_llm is not None:
            del _current_local_llm
            gc.collect()
            
        # Load the new model
        # Note: model_name here functions as the full file path to the GGUF file
        _current_local_llm = Llama(
            model_path=model_path,
            n_gpu_layers=-1,  # Offload all to GPU
            n_ctx=4096,       # Increased context window for code generation
            verbose=False     # Keep the console clean
        )
        _current_local_model_path = model_path

    # Prepare the messages payload
    messages = [
        {"role": "system", "content": system_rules},
        {"role": "user", "content": prompt}
    ]

    # Run the generation in a separate thread so we don't block the async event loop
    # we have an option to enforce agent_response_schema, we are not implimenting yet
    def _generate_local():
        return _current_local_llm.create_chat_completion(
            messages=messages,
            temperature=0.1,
            max_tokens=1024,
            response_format={"type": "json_object"}
            # "schema": agent_response_schema
        )

    response = await asyncio.to_thread(_generate_local)

    # Extract token usage from the local model's response dict
    if response and isinstance(response, dict) and "usage" in response:
        usage_data = response["usage"]
        prompt_tokens = usage_data.get("prompt_tokens", 0)

        # Calculate and update HUD based on the model's safe limit
        max_tokens = model_config.get("max_tokens")
        if max_tokens and prompt_tokens > 0:
            usage_percent = (prompt_tokens / max_tokens) * 100
            print(f"Capacity Used (Local): {usage_percent:.2f}% (Safe Limit: {max_tokens})")
            
            send_hud_gauge("PROMPT", usage_percent, "Prompt Tokens")

    # Ensure we extract the text content from the standard choices array
    if isinstance(response, dict) and "choices" in response:
        choices = response["choices"]
        if choices and "message" in choices[0]:
            return choices[0]["message"].get("content", "")
            
    return ""