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

from database.db_wernicke_semantic_cortex import inject_to_cortex

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
    Parse a Sphinx doctree file and extract structured data.
    Uses the filename as the absolute source of truth for grouping attributes.
    """
    # Extract class name from filename (e.g., 'bpy.types.Strip.doctree' -> 'bpy.types.Strip')
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
            
        print(f"[System: Parsing {file_path} into a unified structure...]")

        for node in document.findall(addnodes.desc):
            obj_type = node.attributes.get('objtype', 'unknown')

            item_data = {
                'type': obj_type,
                'name': '',
                'signature': '',
                'description': '',
                'parameters': [],
                'returns': '',
                'return_type': ''
            }

            # 1. Parse Signature
            for sig in node.findall(addnodes.desc_signature):
                item_data['signature'] = sig.astext().replace('\n', ' ')
                for name_node in sig.findall(addnodes.desc_name):
                    item_data['name'] += name_node.astext()

            # Fallback if name is empty
            if not item_data['name']:
                item_data['name'] = item_data['signature'].split('(')[0].strip()

            # 2. Parse Content (Docstrings, Params, Returns)
            description_parts = []
            for child in node.findall(addnodes.desc_content):
                for element in child.children:
                    if isinstance(element, nodes.paragraph):
                        description_parts.append(element.astext().replace('\n', ' '))
                    elif isinstance(element, nodes.field_list):
                        for field in element.findall(nodes.field):
                            field_name = field[0].astext().lower() 
                            field_body = field[1].astext().replace('\n', ' ')

                            if 'parameter' in field_name or 'param' in field_name:
                                item_data['parameters'].append(field_body)
                            elif 'return type' in field_name or 'rtype' in field_name:
                                item_data['return_type'] = field_body
                            elif 'return' in field_name:
                                item_data['returns'] = field_body

            item_data['description'] = ' '.join(description_parts)

            # 3. BULLETPROOF ROUTING
            if obj_type in ['attribute', 'data', 'property']:
                # All attributes go strictly into the main class container
                main_class['attributes'].append(item_data)
                
            elif obj_type == 'method':
                # Clean up the method name to include the class path
                clean_name = item_data['name'].split('.')[-1] # extract just 'swap'
                item_data['name'] = f"{file_stem}.{clean_name}" # becomes 'bpy.types.Strip.swap'
                extracted_methods.append(item_data)
                
            elif obj_type == 'class':
                # If we find the original class definition, steal its real description and signature
                if not main_class['description']:
                    main_class['description'] = item_data['description']
                    main_class['signature'] = item_data['signature']

        # Final assembly: Exactly 1 Main Class + N independent Methods
        final_items = [main_class] + extracted_methods
        
        # Package for the Database
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
# Execution block
# ---------------------------------------------------------
if __name__ == "__main__":
    path = ".semantic"
    file = 'bpy.types.Strip.doctree'

    print("[System: Starting the extraction and grouping process...]")
    
    file_to_parse = f"{path}\\{file}"
    parsed_objects = parse_blender_doctree(file_to_parse)
    
    if parsed_objects:
        # Pass the correctly structured data to the database
        result = inject_to_cortex(parsed_objects, semantic="blender")
        print(f"\n[Result: {result['message']}]")
    else:
        print("[System: No objects found to inject. Check the scraper.]")