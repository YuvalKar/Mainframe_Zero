import sys
import os
import time

# Add the root directory to sys.path so we can import our modules easily
# even if the script is run directly from inside the 'tests' folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from attention_manager import AttentionManager

def run_tests():
    print("=== Starting AttentionManager DB Tests ===\n")
    
    # 1. Initialize the manager
    manager = AttentionManager()
    print("[1] Manager initialized.")

    # 2. Create a Root Attention (Parent)
    print("\n[2] Creating Root Attention...")
    root_node = manager.create_attention(
        name="Mainframe Zero Architecture",
        required_app="python_env",
        tags=["architecture", "planning"]
    )
    
    if not root_node:
        print("❌ Failed to create Root Attention. Check DB connection.")
        return
        
    print(f"✅ Created Root: {root_node['name']} (ID: {root_node['id']})")

    # 3. Create a Child Attention (Sub-task)
    print("\n[3] Creating Child Attention...")
    child_node = manager.create_attention(
        name="Database Migration to PostgreSQL",
        required_app="python_env",
        parent_id=root_node['id'], # Link it to the root!
        tags=["database", "sql"]
    )
    
    print(f"✅ Created Child: {child_node['name']} (ID: {child_node['id']})")
    print(f"   Child's Parent ID: {child_node['parent_id']}")

    # 4. Search and check order (Child should be first because it was created last)
    print("\n[4] Searching all attentions (Checking default order)...")
    results_before = manager.search_attentions()
    print("Current order (Top 2):")
    for idx, res in enumerate(results_before[:2]):
        print(f"  {idx + 1}. {res['name']} (Updated: {res['updated_at']})")

    # 5. Simulate time passing and loading the Root (The BUMP test)
    print("\n[5] Simulating a coffee break (2 seconds)...")
    time.sleep(2)
    
    print(f"Loading Root Attention to trigger 'bump' on: {root_node['name']}")
    loaded_root = manager.load_attention(root_node['id'])
    print(f"✅ Loaded Root. New updated_at: {loaded_root['updated_at']}")

    # 6. Search again to verify the Root bumped to the top
    print("\n[6] Searching again to verify the 'Bump' worked...")
    results_after = manager.search_attentions()
    print("New order (Top 2):")
    for idx, res in enumerate(results_after[:2]):
        print(f"  {idx + 1}. {res['name']} (Updated: {res['updated_at']})")

    if results_after[0]['id'] == root_node['id']:
        print("\n🎉 SUCCESS: The Root Attention successfully bumped to the top!")
    else:
        print("\n❌ FAILED: The Root Attention did not bump to the top.")

if __name__ == "__main__":
    run_tests()