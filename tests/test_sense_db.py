import json
import sys
import os

# Add the current directory to the path so it can find 'senses' and 'core_utils'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from senses import sense_db_schema

def run_test():
    print("Testing 'sense_db_schema'...\n")
    
    # Execute the sense exactly how the AI would call it
    result = sense_db_schema.execute()
    
    # Print the raw output formatted nicely
    print("--- SENSE OUTPUT ---")
    print(json.dumps(result, indent=4))
    print("--------------------\n")
    
    # Check if the operation was successful
    if result.get("success"):
        print("✅ Test Passed: Successfully connected to DB and retrieved schema.")
        
        # Optional: Print the specific tables found
        tables = result.get("data", {}).keys()
        if tables:
            print(f"Tables found: {', '.join(tables)}")
        else:
            print("No tables found in the public schema.")
            
    else:
        print("❌ Test Failed: Something went wrong.")

if __name__ == "__main__":
    run_test()