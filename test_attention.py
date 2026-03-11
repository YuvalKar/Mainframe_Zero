import pprint
from attention_manager import AttentionManager

def run_tests():
    print("--- Starting AttentionManager Tests ---\n")
    
    # Initialize the manager
    manager = AttentionManager()
    
    # 1. Create a few dummy attentions
    print("1. Creating new attentions...")
    attn1 = manager.create_attention(
        name="Rusty Metal Texture",
        target_app="blender_for_uefn",
        tags=["texture", "materials", "rusty"]
    )
    print(f" -> Created: {attn1['name']} [{attn1['id']}]")
    
    attn2 = manager.create_attention(
        name="Review Ministry Tender",
        target_app="tender_reviewer",
        tags=["finance", "urgent"]
    )
    print(f" -> Created: {attn2['name']} [{attn2['id']}]")
    
    attn3 = manager.create_attention(
        name="Capacitor 3D Model",
        target_app="blender_for_uefn",
        tags=["modeling", "components", "urgent"]
    )
    print(f" -> Created: {attn3['name']} [{attn3['id']}]\n")
    
    # 2. Test search by App
    print("2. Searching for 'blender_for_uefn' tasks...")
    blender_tasks = manager.search_attentions(app_filter="blender_for_uefn")
    print(f" -> Found {len(blender_tasks)} Blender tasks.")
    for t in blender_tasks:
        print(f"    - {t['name']}")
        
    # 3. Test search by Tag
    print("\n3. Searching for tag 'urgent'...")
    urgent_tasks = manager.search_attentions(tag_filter="urgent")
    print(f" -> Found {len(urgent_tasks)} urgent tasks.")
    for t in urgent_tasks:
        print(f"    - {t['name']}")
        
    # 4. Test loading a specific attention
    print(f"\n4. Loading specific attention by ID: {attn1['id']}")
    loaded_attn = manager.load_attention(attn1['id'])
    
    if loaded_attn:
        print(" -> Successfully loaded! Here is the data:")
        pprint.pprint(loaded_attn)
    else:
        print(" -> Failed to load! Something went wrong.")

if __name__ == "__main__":
    run_tests()