import json
import sense_get_directory_tree

# Define the path to test and the allowed extensions
test_path = "."
extensions = [".md", ".py", ".json", ".jsx"]

print(f"Testing sense_get_directory_tree on path: '{test_path}'\n")

# Execute the sense
result = sense_get_directory_tree.execute(root_path=test_path, allowed_extensions=extensions)

# Print the result in a readable JSON format
print(json.dumps(result, indent=4, ensure_ascii=False))