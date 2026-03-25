import json

# Import the sense skill you just created
# (Assuming the file is named sense_blender_get_selected_data.py)
import sense_blender_get_selected_data

def run_test():
    print("Initiating test...")
    print("Asking Blender for selected objects data...\n")
    
    # Execute the sense skill
    response = sense_blender_get_selected_data.execute()
    
    # Print the result nicely formatted
    print("--- RAW RESPONSE FROM BLENDER ---")
    print(json.dumps(response, indent=4, ensure_ascii=False))
    print("---------------------------------")
    
    # Check if we actually got a successful read
    if response.get("success"):
        objects = response.get("data", [])
        print(f"\nSuccess! Found {len(objects)} object(s).")
    else:
        print(f"\nFailed or empty: {response.get('message')}")

if __name__ == "__main__":
    run_test()