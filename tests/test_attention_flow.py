import asyncio
import os
import sys

import os
from database.db_attention import init_attentions_db
# Import your actual functions here
from core_utils.attention_ops import update_session_attention

def run_isolated_test():
    print("=== Starting Isolated Attention Flow Test ===")
    
    # 1. Clean slate - wipe the DB for the test
    init_attentions_db()
    
    # 2. Create dummy files to ensure we have real absolute paths
    file_a = os.path.abspath("dummy_test_file_a.py")
    file_b = os.path.abspath("dummy_test_file_b.py")
    
    with open(file_a, "w") as f: f.write("# File A content")
    with open(file_b, "w") as f: f.write("# File B content")
    
    # This acts as our mock application state
    session_context = {}
    
    try:
        print("\n[Step 1] Initializing focus on File A")
        update_session_attention(session_context, active_file=file_a, context_files=[file_b])
        attn_1 = session_context.get("active_attention", {})
        id_1 = attn_1.get("id")
        print(f"Current ID: {id_1} | Focus: {attn_1.get('focus')}")
        
        print("\n[Step 2] User clicks on File B (Context Switch)")
        update_session_attention(session_context, active_file=file_b, context_files=[file_a])
        attn_2 = session_context.get("active_attention", {})
        id_2 = attn_2.get("id")
        print(f"Current ID: {id_2} | Focus: {attn_2.get('focus')}")
        
        print("\n[Step 3] User returns to File A (The real test!)")
        update_session_attention(session_context, active_file=file_a, context_files=[file_b])
        attn_3 = session_context.get("active_attention", {})
        id_3 = attn_3.get("id")
        print(f"Current ID: {id_3} | Focus: {attn_3.get('focus')}")
        
        print("\n=== Test Results ===")
        # If the DB logic and update_session_attention work, id_1 and id_3 should match
        if id_1 and id_1 == id_3:
            print("✅ Success! The system remembered the historical focus and resumed the ID.")
        elif id_1 == id_2:
            print("❌ Failed: The ID didn't change at all between files. Context switch ignored.")
        else:
            print(f"❌ Failed: Created a new ID instead of loading history. (ID 1: {id_1} != ID 3: {id_3})")
            
    finally:
        # Cleanup dummy files
        if os.path.exists(file_a): os.remove(file_a)
        if os.path.exists(file_b): os.remove(file_b)

if __name__ == "__main__":
    run_isolated_test()