import pickle
import sys
from pathlib import Path
from docutils import nodes
from sphinx import addnodes

# Get the absolute path of the current file
current_file = Path(__file__).resolve()

# Go up 4 levels to reach the Mainframe_Zero root directory
project_root = current_file.parents[3] 

# Add the root directory to sys.path
sys.path.insert(0, str(project_root))

from database.db_wernicke_semantic_cortex import inject_to_semantic_cortex

def format_to_markdown(item):
    """
    Convert the extracted dictionary into a clean, LLM-friendly Markdown format.
    Handles classes (with their attributes) and methods separately.
    """
    md = f"### `{item['name']}`\n\n"
    md += f"**Type:** {item['type'].capitalize()}\n"
    md += f"**Signature:** `{item['signature']}`\n\n"
    
    if item['description']:
        md += f"**Summary:**\n{item['description']}\n\n"
        
    # If this is a class, list all its attributes and properties
    if item.get('attributes'):
        md += "**Attributes & Properties:**\n"
        for attr in item['attributes']:
            md += f"- **`{attr['name']}`**: {attr['description']}\n"
        md += "\n"
        
    # If this is a method, list its parameters
    if item.get('parameters'):
        md += "**Parameters:**\n"
        for param in item['parameters']:
            md += f"- {param}\n"
        md += "\n"
        
    # Return values for methods
    if item.get('returns') or item.get('return_type'):
        md += "**Returns:**\n"
        if item.get('return_type'):
            md += f"- **Type:** `{item['return_type']}`\n"
        if item.get('returns'):
            md += f"- **Description:** {item['returns']}\n"
        md += "\n"
        
    return md.strip()

def parse_blender_doctree(file_path):
    """
    Parse a Sphinx doctree file by looking ONLY at direct children to avoid
    overwriting parent data with nested attribute/method data.
    """
    file_stem = Path(file_path).name.replace('.doctree', '')
    
    # Pre-build our main class container
    main_class = {
        'type': 'class',
        'name': file_stem,
        'signature': f"class {file_stem}",
        'description': '',
        'attributes': [],
        'parameters': [],
        'returns': '',
        'return_type': ''
    }
    
    extracted_methods = []

    try:
        with open(file_path, 'rb') as f:
            document = pickle.load(f)
            
        print(f"[System: Parsing {file_path} with strict child isolation...]")

        for node in document.findall(addnodes.desc):
            obj_type = node.attributes.get('objtype', 'unknown')

            # 1. Parse Signature (STRICTLY direct children only)
            signatures = [child for child in node.children if isinstance(child, addnodes.desc_signature)]
            if not signatures:
                continue
            
            # Take only the first immediate signature node
            primary_sig = signatures[0]
            item_signature = primary_sig.astext().replace('\n', ' ')
            
            item_name = ""
            for name_node in primary_sig.findall(addnodes.desc_name):
                item_name += name_node.astext()
            
            # Fallback if name is empty
            if not item_name:
                item_name = item_signature.split('(')[0].strip()

            # 2. Parse Content (STRICTLY direct children only)
            contents = [child for child in node.children if isinstance(child, addnodes.desc_content)]
            item_description_parts = []
            item_parameters = []
            item_returns = ''
            item_return_type = ''
            
            if contents:
                content_node = contents[0]
                # Look only at the immediate paragraphs/lists of this specific content block
                for element in content_node.children:
                    if isinstance(element, nodes.paragraph):
                        item_description_parts.append(element.astext().replace('\n', ' '))
                    elif isinstance(element, nodes.field_list):
                        for field in element.findall(nodes.field):
                            field_name = field[0].astext().lower() 
                            field_body = field[1].astext().replace('\n', ' ')

                            if 'parameter' in field_name or 'param' in field_name:
                                item_parameters.append(field_body)
                            elif 'return type' in field_name or 'rtype' in field_name:
                                item_return_type = field_body
                            elif 'return' in field_name:
                                item_returns = field_body

            item_description = ' '.join(item_description_parts)

            # Build the atomic item data
            item_data = {
                'type': obj_type,
                'name': item_name,
                'signature': item_signature,
                'description': item_description,
                'parameters': item_parameters,
                'returns': item_returns,
                'return_type': item_return_type
            }

            # 3. ROUTING
            if obj_type == 'class' and not main_class['description']:
                # We found the main class definition. Lock it in.
                main_class['signature'] = item_data['signature']
                main_class['description'] = item_data['description']
                
            elif obj_type in ['attribute', 'data', 'property']:
                # Attributes go directly into the main class container
                main_class['attributes'].append(item_data)
                
            elif obj_type in ['method', 'classmethod', 'staticmethod']:
                # Methods get their own independent record with the fully qualified name
                clean_name = item_data['name'].split('.')[-1]
                item_data['name'] = f"{file_stem}.{clean_name}"
                extracted_methods.append(item_data)

        # Final assembly: Exactly 1 Main Class + N independent Methods
        final_items = [main_class] + extracted_methods
        
        # Package for the Database Injector
        db_ready_data = []
        for item in final_items:
            md_content = format_to_markdown(item)
            db_ready_data.append({
                'element_path': item['name'],
                'element_type': item['type'],
                'content_markdown': md_content,
                'metadata': {
                    'language': 'Python',
                    'module': file_stem.rsplit('.', 1)[0] # e.g., 'bpy.types'
                }
            })

        return db_ready_data

    except Exception as e:
        print(f"[Error: Failed to extract data - {e}]")
        return []

# ---------------------------------------------------------
# Execution block - Batch processing all .doctree files
# ---------------------------------------------------------
if __name__ == "__main__":
    
    # Define the directory path
    semantic_dir = Path(".semantic")
    
    print(f"[System: Starting batch extraction from '{semantic_dir}'...]")
    
    # Verify the directory exists
    if not semantic_dir.exists() or not semantic_dir.is_dir():
        print(f"[Error: Directory '{semantic_dir}' not found.]")
        sys.exit(1)

    # Gather all doctree files in the folder
    doctree_files = list(semantic_dir.glob("*.doctree"))
    total_files = len(doctree_files)
    
    if total_files == 0:
        print("[System: No .doctree files found in the directory.]")
        sys.exit(0)
        
    print(f"[System: Found {total_files} files. Beginning parsing and injection...]")
    
    successful_files = 0
    
    # Iterate through each file
    for i, file_path in enumerate(doctree_files, 1):
        print(f"\n--- Processing File {i}/{total_files}: {file_path.name} ---")
        
        # Parse the current file
        parsed_objects = parse_blender_doctree(str(file_path))
        
        if parsed_objects:
            # Inject to database
            result = inject_to_semantic_cortex(parsed_objects, semantic="blender")
            
            if result.get('success'):
                successful_files += 1
                print(f"[Result: {result['message']}]")
            else:
                print(f"[Error: Failed to inject {file_path.name} - {result.get('message')}]")
        else:
            print(f"[System: Skipped {file_path.name} - No objects found or parsing failed.]")
            
    # Final summary
    print(f"\n[System: Batch process complete! Successfully indexed {successful_files} out of {total_files} files.]")