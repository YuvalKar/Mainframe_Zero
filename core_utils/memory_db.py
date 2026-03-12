import os
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv
import json

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
    """Load and return the local BAAI/bge-m3 model using Lazy Loading."""
    global _local_model
    if _local_model is None:
        print("Loading BAAI/bge-m3 model (this might take a bit longer to download the first time)...")
        # We import it HERE, only when actually requested, to save startup time!
        from sentence_transformers import SentenceTransformer
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


import json

############################## Short-Term Memory (History) ##############################

def init_chat_history_db():
    """
    Initialize the short-term memory (chat history) table.
    WARNING: Drops the existing table to allow schema changes during development!
    """
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        
        # Drop the table if it already exists to start fresh
        cursor.execute("DROP TABLE IF EXISTS chat_history;")
        print("[System: Existing 'chat_history' table dropped (if it existed).]")
        
        create_table_query = """
        CREATE TABLE chat_history (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(100) NOT NULL,
            user_input TEXT NOT NULL,
            actions JSONB,
            ai_response TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Create an index on session_id to make history retrieval blazing fast
        create_index_query = """
        CREATE INDEX idx_chat_history_session ON chat_history(session_id);
        """
        
        cursor.execute(create_table_query)
        cursor.execute(create_index_query)
        conn.commit()
        print("[System: 'chat_history' table initialized successfully.]")
        
    except Exception as e:
        print(f"[Memory DB Error: Failed to initialize chat_history table - {e}]")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def save_chat_history_turn(session_id: str, user_input: str, actions: list, ai_response: str):
    """Saves a single conversation turn and its actions to the database."""
    conn = get_db_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        insert_query = """
        INSERT INTO chat_history (session_id, user_input, actions, ai_response)
        VALUES (%s, %s, %s, %s)
        """
        # Ensure actions list is converted to a JSON string for the JSONB column
        actions_json = json.dumps(actions) if actions else '[]'
        
        cursor.execute(insert_query, (session_id, user_input, actions_json, ai_response))
        conn.commit()
    except Exception as e:
        print(f"[Memory DB Error: Failed to save history turn - {e}]")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_recent_chat_history(session_id: str, limit: int = 5) -> list:
    """Retrieves the last N turns for a specific session."""
    conn = get_db_connection()
    if not conn:
        return []
        
    try:
        cursor = conn.cursor()
        # Fetch the latest N records for this session, ordered by newest first
        select_query = """
        SELECT user_input, actions, ai_response
        FROM chat_history
        WHERE session_id = %s
        ORDER BY id DESC
        LIMIT %s
        """
        cursor.execute(select_query, (session_id, limit))
        rows = cursor.fetchall()
        
        history = []
        for row in rows:
            history.append({
                "user": row[0],
                "actions": row[1] if row[1] else [],
                "ai": row[2]
            })
            
        # Reverse the list so the oldest memory in the batch appears first in the prompt
        history.reverse()
        return history
        
    except Exception as e:
        print(f"[Memory DB Error: Failed to fetch history - {e}]")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            
if __name__ == "__main__":
    print('nothing to see here')
    # Run this directly once to set up the table
    # init_hippocampus_db()
    # init_chat_history_db()