from llama_cpp import Llama

# Replace this with the actual path where you saved the BlenderLLM file
MODEL_PATH = r"C:\LocalAI\Models\BlenderLLM.Q4_K_M.gguf"

print("Starting to load the model...")

# Initialize the model
# n_gpu_layers=-1 tells the system to put everything on your RTX 5070
# verbose=True will print diagnostic info so we can verify CUDA is working
llm = Llama(
    model_path=MODEL_PATH,
    n_gpu_layers=-1,
    n_ctx=2048,
    verbose=True
)

print("\n--- Model loaded successfully! ---")