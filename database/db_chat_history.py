from database.db_connection import get_db_connection
import json

############################## Short-Term Memory (chat History) ##############################
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