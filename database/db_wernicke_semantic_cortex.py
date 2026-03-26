from database.db_connection import get_db_connection, get_local_model

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
        
        # Create the memory table
        # Note: Using 1024 dimensions to match the hippocampus DB (e.g., for BAAI/bge-m3)
        create_table_query = """
        CREATE TABLE wernicke_semantic_cortex (
            id SERIAL PRIMARY KEY,
            semantic VARCHAR(50) NOT NULL,      -- e.g., 'Blender', 'UEFN', 'Verse'
            element_path VARCHAR(255) NOT NULL, -- e.g., 'bpy.types.Strip.split'
            element_type VARCHAR(50) NOT NULL,  -- e.g., 'class', 'method', 'property'
            content_markdown TEXT NOT NULL,
            metadata JSONB,                     -- e.g., {"language": "Python", "module": "bpy.types"}
            embedding vector(1024),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
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
            conn.close()

######################################################
import json
from database.db_connection import get_db_connection, get_local_model

def inject_to_cortex(parsed_items: list, semantic: str = "Blender") -> dict:
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
            
            # Insert query matching the new schema
            insert_query = """
                INSERT INTO wernicke_semantic_cortex 
                (semantic, element_path, element_type, content_markdown, metadata, embedding)
                VALUES (%s, %s, %s, %s, %s, %s::vector)
            """
            cursor.execute(insert_query, (semantic, element_path, element_type, md_content, meta_json, embedding))
            
            # Print progress
            if (i + 1) % 10 == 0:
                print(f"  -> Injected {i + 1}/{len(parsed_items)} items...")

        conn.commit()
        cursor.close()
        conn.close()

        return {
            "success": True, 
            "message": f"Successfully encoded {len(parsed_items)} items into the Wernicke Semantic Cortex."
        }

    except Exception as e:
        return {"success": False, "message": f"Failed to encode documentation: {str(e)}"}


if __name__ == "__main__":
    # Run this once to create the new table with updated_at
    # init_wernicke_semantic_cortex_db()
    pass