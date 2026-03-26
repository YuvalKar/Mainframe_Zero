import pickle
from docutils import nodes
from sphinx import addnodes

def parse_blender_doctree(file_path):
    """
    Parse a Sphinx doctree file and extract structured data for methods, attributes, and data.
    Returns a list of dictionaries representing the extracted objects.
    """
    extracted_data = []

    try:
        with open(file_path, 'rb') as f:
            document = pickle.load(f)
            
        print(f"[System: Parsing {file_path}...]")

        # Iterate over all documented objects
        for node in document.findall(addnodes.desc):
            obj_type = node.attributes.get('objtype', 'unknown')
            
            # Skip the main 'class' wrapper to avoid duplicating the content
            if obj_type == 'class':
                continue

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
                
                # Try to isolate just the pure name (without arguments/prefixes)
                for name_node in sig.findall(addnodes.desc_name):
                    item_data['name'] = name_node.astext()


            # 2. Parse Content (Docstrings, Params, Returns)
            description_parts = []
            
            for child in node.findall(addnodes.desc_content):
                # Iterate over direct children only to avoid grabbing nested paragraphs
                for element in child.children:
                    if isinstance(element, nodes.paragraph):
                        description_parts.append(element.astext().replace('\n', ' '))
                    
                    elif isinstance(element, nodes.field_list):
                        # Extract detailed fields (Parameters, Returns, Type)
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

            extracted_data.append(item_data)

        return extracted_data

    except Exception as e:
        print(f"[Error: Failed to extract data - {e}]")
        return []

def format_to_markdown(item):
    """
    Convert the extracted dictionary into a clean, LLM-friendly Markdown format.
    Optimized for token efficiency and semantic search.
    """
    # Start with the exact function/attribute name as a header
    md = f"### `{item['name']}`\n\n"
    
    # Add basic metadata
    md += f"**Type:** {item['type'].capitalize()}\n"
    md += f"**Signature:** `{item['signature']}`\n\n"
    
    # Add the summary/description
    if item['description']:
        md += f"**Summary:**\n{item['description']}\n\n"
        
    # Add parameters if they exist
    if item['parameters']:
        md += "**Parameters:**\n"
        for param in item['parameters']:
            md += f"- {param}\n"
        md += "\n"
        
    # Add returns if they exist
    if item['returns'] or item['return_type']:
        md += "**Returns:**\n"
        if item['return_type']:
            md += f"- **Type:** `{item['return_type']}`\n"
        if item['returns']:
            md += f"- **Description:** {item['returns']}\n"
        md += "\n"
        
    return md.strip()

# ---------------------------------------------------------
# Testing the extractor
# ---------------------------------------------------------
# if __name__ == "__main__":
#     file_to_parse = 'bpy.types.Strip.doctree'
#     parsed_objects = parse_blender_doctree(file_to_parse)
    
#     print("\n[System: Testing Markdown generation for a method...]")
#     print("-" * 60)
    
#     # Let's find a method to print (so we can see params and returns)
#     for obj in parsed_objects:
#         if obj['type'] == 'method' and obj['parameters']:
#             print(format_to_markdown(obj))
#             break # Just print one and stop