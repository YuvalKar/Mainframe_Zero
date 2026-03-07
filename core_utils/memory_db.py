import os
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

# Global variable to hold the model in memory so we don't load it multiple times
_local_model = None

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
    """Load and return the local BAAI/bge-m3 model."""
    global _local_model
    if _local_model is None:
        print("Loading BAAI/bge-m3 model (this might take a bit longer to download the first time)...")
        # Initialize the SentenceTransformer model
        _local_model = SentenceTransformer('BAAI/bge-m3')
    return _local_model

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
            conn.close()

if __name__ == "__main__":
    print('nothing to see here')
    # Run this directly once to set up the table
    # init_hippocampus_db()