import os
import psycopg2
from psycopg2.extras import Json
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
    """Establish and return a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "postgres"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "")
        )
        return conn
    except Exception as e:
        print(f"[Memory DB Error: Failed to connect to database - {e}]")
        return None

def get_local_model():
    global _local_model
    if _local_model is not None:
        return _local_model
    
    print("Loading BAAI/bge-m3 model (this might take a bit longer to download)...")
    # פשוט מחליפים את שם המודל כאן
    _local_model = SentenceTransformer('BAAI/bge-m3')
    return _local_model

# def init_db():
#     """Initialize the database schema, creating the memory table if it doesn't exist."""
#     conn = get_db_connection()
#     if not conn:
#         return

#     try:
#         cursor = conn.cursor()
        
#         # Ensure the vector extension is enabled (we did this manually, but good practice to ensure)
#         cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
#         # Create the memory table
#         # We use vector(768) because Gemini embeddings typically have 768 dimensions
#         create_table_query = """
#         CREATE TABLE IF NOT EXISTS mainframe_memory (
#             id SERIAL PRIMARY KEY,
#             content TEXT NOT NULL,
#             metadata JSONB,
#             embedding vector(768),
#             created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
#         );
#         """
#         cursor.execute(create_table_query)
#         conn.commit()
#         print("[System: Hippocampus DB initialized successfully. Table 'mainframe_memory' is ready.]")
        
#     except Exception as e:
#         print(f"[Memory DB Error: Failed to initialize database schema - {e}]")
#     finally:
#         if cursor:
#             cursor.close()
#         if conn:
#             conn.close()

# if __name__ == "__main__":
#     # Run this directly once to set up the table
#     init_db()