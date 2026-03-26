from db_connection import get_db_connection

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
            language VARCHAR(50) NOT NULL,
            function_name VARCHAR(255) NOT NULL,
            content_markdown TEXT NOT NULL,
            embedding vector(1024),
            tags TEXT[],
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


if __name__ == "__main__":
    # Run this once to create the new table with updated_at
    # init_wernicke_semantic_cortex_db()
    pass