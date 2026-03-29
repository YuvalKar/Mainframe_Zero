from database.db_connection import get_db_connection, release_db_connection, get_local_model
import json
import os
import ast

############################## Wernicke Semantic Cortex Database Initialization Script ##############################
def init_wernicke_semantic_cortex_db():
    """Initialize the database schema for the language processing memory. Warning: This will drop the existing table!"""
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        
        # Ensure the vector extension is enabled
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # Drop the table if it already exists to start fresh
        cursor.execute("DROP TABLE IF EXISTS wernicke_semantic_cortex;")
        print("[System: Existing 'wernicke_semantic_cortex' table dropped (if it existed).]")
        
        # Create the memory table with the UNIQUE constraint for upserts
        # Note: Using 1024 dimensions to match the hippocampus DB (e.g., for BAAI/bge-m3)
        create_table_query = """
        CREATE TABLE wernicke_semantic_cortex (
            id SERIAL PRIMARY KEY,
            semantic VARCHAR(50) NOT NULL,      -- e.g., 'blender', 'uefn', 'verse'
            element_path VARCHAR(255) NOT NULL, -- e.g., 'bpy.types.Strip.split'
            element_type VARCHAR(50) NOT NULL,  -- e.g., 'class', 'method', 'property'
            content_markdown TEXT NOT NULL,
            metadata JSONB,                     -- e.g., {"language": "Python", "module": "bpy.types"}
            embedding vector(1024),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            
            -- Ensure we never inject the same element path twice for the same software
            CONSTRAINT unique_semantic_element UNIQUE (semantic, element_path)
        );
        """
        cursor.execute(create_table_query)
        
        # Create an index for faster vector similarity search using hnsw
        create_index_query = """
        CREATE INDEX ON wernicke_semantic_cortex USING hnsw (embedding vector_cosine_ops);
        """
        cursor.execute(create_index_query)
        
        conn.commit()
        print("[System: Wernicke Semantic Cortex DB initialized successfully. Fresh table is ready.]")
        
    except Exception as e:
        print(f"[Memory DB Error: Failed to initialize Wernicke schema - {e}]")
        # Rollback the transaction if an error occurs
        if conn:
            conn.rollback()
    finally:
        # Safely close cursor and connection
        if 'cursor' in locals() and cursor:
            cursor.close()
        if conn:
            release_db_connection(conn)

######################################################
def inject_to_semantic_cortex(parsed_items: list, semantic: str = "Blender") -> dict:
    """
    Batch encoder for Wernicke Semantic Cortex.
    Injects prepared dictionaries into the PostgreSQL database.
    """
    if not parsed_items:
        return {"success": False, "message": "No parsed items provided to encode."}

    try:
        # 1. Get the local BAAI/bge-m3 model
        model = get_local_model()
        
        # 2. Connect to the Wernicke DB
        conn = get_db_connection()
        if not conn:
            return {"success": False, "message": "Failed to connect to Wernicke DB."}

        cursor = conn.cursor()
        print(f"\n[System: Beginning batch injection of {len(parsed_items)} items into Cortex...]")

        for i, item in enumerate(parsed_items):
            # The scraper already built the correct dictionary structure for us
            element_path = item.get('element_path', 'unknown')
            element_type = item.get('element_type', 'unknown')
            md_content = item.get('content_markdown', '')
            metadata = item.get('metadata', {})
            
            # Convert metadata dict to JSON string for Postgres JSONB column
            meta_json = json.dumps(metadata)

            # Generate embedding
            embedding_array = model.encode(md_content)
            embedding = embedding_array.tolist()

            # Insert query with UPSERT logic (Insert or Update if exists)
            insert_query = """
                INSERT INTO wernicke_semantic_cortex 
                (semantic, element_path, element_type, content_markdown, metadata, embedding)
                VALUES (%s, %s, %s, %s, %s, %s::vector)
                ON CONFLICT (semantic, element_path) 
                DO UPDATE SET 
                    element_type = EXCLUDED.element_type,
                    content_markdown = EXCLUDED.content_markdown,
                    metadata = EXCLUDED.metadata,
                    embedding = EXCLUDED.embedding,
                    created_at = CURRENT_TIMESTAMP
            """

            cursor.execute(insert_query, (semantic, element_path, element_type, md_content, meta_json, embedding))
            
            # Print progress
            if (i + 1) % 10 == 0:
                print(f"  -> Injected {i + 1}/{len(parsed_items)} items...")

        conn.commit()
        cursor.close()
        release_db_connection(conn)

        return {
            "success": True, 
            "message": f"Successfully encoded {len(parsed_items)} items into the Wernicke Semantic Cortex."
        }

    except Exception as e:
        return {"success": False, "message": f"Failed to encode documentation: {str(e)}"}

#########################################################################################
def query_semantic_cortex(user_query: str, semantics: list, limit: int = 5, max_chars: int = 6000) -> list:
    """
    Search the Wernicke Semantic Cortex for the most relevant documentation and skills.
    Accepts a list of semantic namespaces (e.g., ['blender', 'mz_blender']).
    """
    if not user_query:
        print("[Error: Empty query provided.]")
        return []

    # Fallback just in case someone passes a single string instead of a list
    if isinstance(semantics, str):
        semantics = [semantics]

    try:
        # 1. Load the model and embed the user's free-text query
        model = get_local_model()
        query_embedding = model.encode(user_query).tolist()

        # 2. Connect to the database
        conn = get_db_connection()
        if not conn:
            print("[Error: Failed to connect to Wernicke DB.]")
            return []

        cursor = conn.cursor()

        # 3. Perform Vector Similarity Search
        # Notice the change in the WHERE clause: semantic = ANY(%s)
        search_query = """
            SELECT element_path, element_type, content_markdown,
                   1 - (embedding <=> %s::vector) AS similarity_score
            FROM wernicke_semantic_cortex
            WHERE semantic = ANY(%s)
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
        """
        
        # Pass the 'semantics' list directly to psycopg2
        cursor.execute(search_query, (query_embedding, semantics, query_embedding, limit))
        results = cursor.fetchall()
        
        # 4. Package the results (rest of your original code remains the same)
        formatted_results = []
        current_char_count = 0
        
        for row in results:
            content_text = row[2]
            content_length = len(content_text)
            
            if current_char_count + content_length > max_chars:
                print(f"[System: Context size limit reached. Stopped at {len(formatted_results)} results.]")
                break
                
            formatted_results.append({
                'element_path': row[0],
                'element_type': row[1],
                'content': content_text,
                'score': round(row[3], 4)
            })
            
            current_char_count += content_length

        cursor.close()
        release_db_connection(conn)

        return formatted_results

    except Exception as e:
        print(f"[Error: Failed to query the cortex - {str(e)}]")
        return []


#############################################################################################
def index_mz_app_lib(app_root_path: str):
    """
    Scans a given mz_APPNAME directory, parses Python files, 
    and injects directly into the Wernicke Cortex on a per-file basis.
    """
    # Extract the semantic name directly from the folder name (e.g., 'mz_blender')
    semantic_name = os.path.basename(os.path.normpath(app_root_path))
    
    # The parent directory used to calculate relative python dot-paths
    parent_dir = os.path.dirname(os.path.normpath(app_root_path))
    
    print(f"Starting indexer for semantic namespace: '{semantic_name}'...")

    # Walk through the directory tree recursively
    for dirpath, _, filenames in os.walk(app_root_path):
        for filename in filenames:
            # We only care about python files, and we skip empty __init__ files
            if filename.endswith(".py") and filename != "__init__.py":
                filepath = os.path.join(dirpath, filename)
                
                # Calculate the Python dot-notation path
                rel_path = os.path.relpath(filepath, parent_dir)
                module_path = rel_path.replace(os.sep, '.')[:-3]
                
                file_items = [] # Reset the list for the current file
                
                # Safely read and parse the python file
                with open(filepath, 'r', encoding='utf-8') as f:
                    try:
                        file_content = f.read()
                        tree = ast.parse(file_content)
                    except Exception as e:
                        print(f"[Warning] Failed to parse {filepath}: {e}")
                        continue
                        
                # Walk through the Abstract Syntax Tree to find functions
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        docstring = ast.get_docstring(node)
                        
                        # Only index functions that have our standard MZ docstring
                        if docstring and "NAME:" in docstring:
                            function_name = node.name
                            element_path = f"{module_path}.{function_name}"
                            
                            # Build the dictionary aligned with your Wernicke DB schema
                            item = {
                                'element_path': element_path,
                                'element_type': 'method', # Aligned with your DB types
                                'content_markdown': docstring,
                                'metadata': {
                                    'language': 'Python',
                                    'module': module_path,
                                    'file': filepath
                                }
                            }
                            file_items.append(item)
                            print(f"  [+] Found Skill: {element_path}")
                            
                # Step-by-step injection: Inject items for THIS file only
                if file_items:
                    print(f"\nInjecting {len(file_items)} items from '{filename}' into Cortex...")
                    db_response = inject_to_semantic_cortex(file_items, semantic=semantic_name)
                    print(f"  -> DB Response: {db_response.get('message', 'No message')}\n")

    print(f"Indexing complete for '{semantic_name}'.")

# Example usage:
# if __name__ == "__main__":
#     target_folder = r"C:\Users\yuval\Documents\NBAYA_projects\Mainframe_Zero\apps\blender\blender_side\mz_blender"
#     index_mz_app_lib(target_folder)

# ---------------------------------------------------------
# Execution block - Let's test our brain!
# ---------------------------------------------------------
# if __name__ == "__main__":
#     # Let's ask a natural language question about our Strip
#     test_question = "How do I cut a video strip into two separate parts?"
#     software_context = "blender"
    
#     print(f"\n[System: Asking Wernicke...] '{test_question}'")
    
#     # We ask for the top 2 most relevant results
#     answers = query_semantic_cortex(test_question, semantic=software_context, limit=2)
    
#     print("-" * 60)
#     for i, ans in enumerate(answers, 1):
#         print(f"Result #{i} | Match Score: {ans['score']}")
#         print(f"Path: {ans['element_path']} ({ans['element_type']})")
#         print(f"Content Preview: {ans['content'][:150]}...\n")
#         print("-" * 60)

# if __name__ == "__main__":
#     # Run this once to create the new table with updated_at
#     # init_wernicke_semantic_cortex_db()
#     pass