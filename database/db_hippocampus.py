from database.db_connection import get_db_connection, release_db_connection


############################## Hippocampus Database Initialization Script ##############################
def init_hippocampus_db():
    """Initialize the database schema. Warning: This will drop the existing table!"""
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        
        # Ensure the vector extension is enabled
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # Drop the table if it already exists to start fresh
        cursor.execute("DROP TABLE IF EXISTS hippocampus;")
        print("[System: Existing 'hippocampus' table dropped (if it existed).]")
        
        # Create the memory table with 1024 dimensions for BAAI/bge-m3
        create_table_query = """
        CREATE TABLE hippocampus (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            metadata JSONB,
            embedding vector(1024),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(create_table_query)
        conn.commit()
        print("[System: Hippocampus DB initialized successfully. Fresh table 'hippocampus' is ready.]")
        
    except Exception as e:
        print(f"[Memory DB Error: Failed to initialize database schema - {e}]")
        # Rollback the transaction if an error occurs
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_db_connection(conn)