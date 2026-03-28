from llama_cpp import Llama
import time
import gc

# --- Configuration ---
MODEL_PATH = r"C:\LocalAI\Models\BlenderLLM.Q4_K_M.gguf"

# The prompt (in English, as the model prefers)
user_prompt = "Create a Blender Python script that generates a rocket. The rocket should be 10 meters tall and stand upright on its rear fins."

# --- Step 1: Load the model to RTX 5070 ---
print("Initializing model on GPU...")
start_time = time.time()
# Set verbose=False for a cleaner output now that we know it works
llm = Llama(model_path=MODEL_PATH, n_gpu_layers=-1, n_ctx=2048, verbose=False)
print(f"Model loaded in {time.time() - start_time:.2f} seconds.")


# --- Step 2: Generate the code ---
print(f"\nSending prompt: '{user_prompt}'")
print("Generating script (this might take a few seconds)...")
start_time = time.time()

# This is where the magic happens
# We use 'create_chat_completion' to match the chat template of the model
response = llm.create_chat_completion(
    messages=[
        {
            "role": "user",
            "content": user_prompt
        }
    ],
    temperature=0.1,  # Keep it deterministic and precise for code
    max_tokens=1024,  # Allow enough room for a complex script
)

generation_time = time.time() - start_time
print(f"Generation finished in {generation_time:.2f} seconds.\n")


# --- Step 3: Extract and Print the result ---
# The response object has a specific structure, we extract just the text content
generated_code = response['choices'][0]['message']['content']

print("--------------------------------------------------")
print("--- GENERATED BLENDER PYTHON SCRIPT ---")
print("--------------------------------------------------")
print(generated_code)
print("--------------------------------------------------")


# --- Step 4: Cleanup VRAM ---
print("\nCleaning up VRAM...")
del llm
gc.collect()
print("Done. VRAM is free.")