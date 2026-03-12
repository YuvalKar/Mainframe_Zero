"""
SYNAPSE: hippo_update
PURPOSE: This is your memory correction tool. Use this to overwrite an existing 
         memory ID with new, corrected information without creating duplicates.
         
WHEN TO USE: 
- When a stored memory is partially incorrect and needs fixing.
- When you need to update a fact or a rule but want to keep the same memory ID.

INPUTS:
- memory_id (int): The unique ID of the memory you want to update.
- new_content (str): The updated text or insight.
- new_metadata (dict, optional): Updated contextual tags.
"""

import json
from database.db_connection import get_db_connection, get_local_model

def execute(memory_id: int, new_content: str, new_metadata: dict = None) -> dict:
    # Ensure we have both an ID and new content to update
    if not memory_id or not new_content:
        return {"success": False, "message": "Memory ID and new content are required for an update."}

    try:
        # 1. Generate a new embedding for the updated content
        # This is crucial so the semantic search finds the updated meaning
        model = get_local_model()
        new_embedding_array = model.encode(new_content)
        new_embedding = new_embedding_array.tolist()

        # 2. Connect to the PostgreSQL Hippocampus database
        conn = get_db_connection()
        if not conn:
            return {"success": False, "message": "Failed to connect to Hippocampus DB."}

        cursor = conn.cursor()
        
        # Convert the new metadata dict to a JSON string if provided, else keep it empty
        meta_json = json.dumps(new_metadata) if new_metadata else "{}"

        # 3. Update query - replacing content, metadata, and the vector embedding
        update_query = """
            UPDATE hippocampus 
            SET content = %s, metadata = %s, embedding = %s::vector 
            WHERE id = %s
        """
        cursor.execute(update_query, (new_content, meta_json, new_embedding, memory_id))
        
        # Check if the memory ID actually existed
        updated_count = cursor.rowcount
        conn.commit()
        
        cursor.close()
        conn.close()

        if updated_count > 0:
            return {
                "success": True, 
                "message": f"Successfully updated memory ID {memory_id} in the Hippocampus."
            }
        else:
            return {
                "success": False, 
                "message": f"Cannot update: Memory ID {memory_id} not found."
            }

    except Exception as e:
        return {"success": False, "message": f"Failed to update memory: {str(e)}"}