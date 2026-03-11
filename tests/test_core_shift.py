import sys
import os

# Add the parent directory (Mainframe_Zero) to the Python path
# so we can import our core modules from inside the 'tests' folder
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import mz_core
from attention_manager import AttentionManager

def run_integration_test():
    print("--- Starting Core <-> App Integration Test ---\n")
    
    # 1. Create a fresh Attention for Blender
    manager = AttentionManager()
    print("1. Creating a fresh Attention task...")
    new_attn = manager.create_attention(
        name="Build Castle Wall (Test)",
        target_app="blender_for_uefn",
        tags=["test", "modeling"]
    )
    attention_id = new_attn['id']
    print(f" -> Created Task: '{new_attn['name']}' with ID: {attention_id}\n")
    
    # 2. Tell the Core to shift attention to this new task
    print("2. Asking mz_core to shift attention...")
    success = mz_core.shift_attention(attention_id)
    
    # 3. Check the result
    print("\n--- Test Results ---")
    if success:
        print("✅ SUCCESS: The Core successfully loaded the app and ran register_to_core!")
    else:
        print("❌ FAILED: The Core could not shift attention. Check the errors above.")

if __name__ == "__main__":
    run_integration_test()