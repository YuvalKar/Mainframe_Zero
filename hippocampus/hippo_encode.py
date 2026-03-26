"""
SYNAPSE: hippo_encode
PURPOSE: This is your active memory encoder. Use this synapse to save important facts, 
         architectural decisions, user preferences, or distilled insights into your 
         Hippocampus (long-term PostgreSQL vector database).
         
WHEN TO USE: 
- When the user explicitly asks you to remember something.
- When a significant project milestone or architectural decision is reached.
- DO NOT use this for raw chat logs. Summarize and distill insights before encoding.

INPUTS:
- content (str): The distilled text, rule, or fact you need to remember.
- metadata (dict, optional): Contextual tags to help filter later 
  (e.g., {"category": "architecture", "topic": "database"}).
"""

import json
from database.db_connection import get_db_connection, release_db_connection, get_local_model

def execute(content: str, metadata: dict = None) -> dict:
    # Ensure there is content to save
    if not content:
        return {"success": False, "message": "No content provided to encode."}

    try:
        # 1. Generate embedding using the local BAAI/bge-m3 model
        model = get_local_model()
        
        # The encode method returns a numpy array, we convert it to a standard python list
        embedding_array = model.encode(content)
        embedding = embedding_array.tolist()

        # 2. Save to PostgreSQL Hippocampus database
        conn = get_db_connection()
        if not conn:
            return {"success": False, "message": "Failed to connect to Hippocampus DB."}

        cursor = conn.cursor()
        
        # Convert metadata dict to JSON string if provided, default to empty JSON
        meta_json = json.dumps(metadata) if metadata else "{}"

        # Insert query - casting the python list to a pgvector type using ::vector
        insert_query = """
            INSERT INTO hippocampus (content, metadata, embedding)
            VALUES (%s, %s, %s::vector)
        """
        cursor.execute(insert_query, (content, meta_json, embedding))
        conn.commit()
        
        cursor.close()
        release_db_connection(conn)

        return {
            "success": True, 
            "message": f"Successfully encoded the memory into the Hippocampus. (Content length: {len(content)} chars)"
        }

    except Exception as e:
        return {"success": False, "message": f"Failed to encode memory: {str(e)}"}
      