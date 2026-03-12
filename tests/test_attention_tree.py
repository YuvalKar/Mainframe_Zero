import sys
import os
import json

# Add the root directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from attention_manager import AttentionManager

def run_tree_test():
    print("=== Starting AttentionManager LOD Tree Test ===\n")
    
    manager = AttentionManager()

    # 1. Create Root Attention (The Project)
    print("[1] Creating Root Attention (LOD 2 - Grandparent/Parent level)...")
    root_node = manager.create_attention(
        name="UEFN Verse Development",
        required_app="uefn_env",
        tags=["epic", "verse"],
        short_summary="Main project for UEFN Verse mechanics.",
        detailed_summary="Setting up the core game loop and player spawning mechanics in Verse.",
        working_files=["main_game_loop.verse"]
    )
    print(f"✅ Created Root: {root_node['name']} (ID: {root_node['id']})")

    # 2. Create Child Attention (The Specific Task)
    print("\n[2] Creating Child Attention (LOD 0 - Active Focus)...")
    child_node = manager.create_attention(
        name="Player Health UI",
        required_app="uefn_env",
        parent_id=root_node['id'],
        tags=["ui", "verse"],
        short_summary="Updating the canvas UI for player health.",
        detailed_summary="We need to bind the player health events to the progress bar widget.",
        working_files=["ui_manager.verse", "assets/health_bar.png"]
    )
    print(f"✅ Created Child: {child_node['name']} (ID: {child_node['id']})")

    # 3. Fetch the LOD Tree from the perspective of the Child
    print("\n[3] Fetching LOD Context Tree for the Child...")
    tree = manager.get_lod_context(child_node['id'])
    
    # 4. Print the result beautifully
    print("\n" + "="*50)
    print("🌳 THE AI CONTEXT (LOD TREE) 🌳")
    print("="*50)
    print(json.dumps(tree, indent=4, ensure_ascii=False))
    print("="*50)
    
    print("\n🎉 SUCCESS: If you see the tree above with all files and summaries, the database is perfect!")

if __name__ == "__main__":
    run_tree_test()