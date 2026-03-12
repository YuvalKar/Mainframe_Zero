"""
SYNAPSE: hippo_recall
PURPOSE: This is your memory retrieval tool. It searches the Hippocampus 
         (PostgreSQL vector DB) for the most semantically relevant memories 
         based on a given context or question.
         It supports Hybrid Search: combining vector similarity with 
         optional metadata filtering.
         
WHEN TO USE: 
- When lacking context for a new task or ambiguous request.
- When returning to an old topic/project to re-establish context.
- To retrieve similar past solutions or known constraints to prevent repeating mistakes.

INPUTS:
- query (str): The search string or question to find relevant memories for.
- limit (int, optional): Maximum number of memories to return. Default is 3.
- filter_dict (dict, optional): A dictionary of metadata to hard-filter the results 
  before the semantic search (e.g., {"software": "blender"}).
"""

import json
from database.db_connection import get_db_connection, get_local_model

def execute(query: str, limit: int = 3, filter_dict: dict = None) -> dict:
    # Ensure there is a query to search for
    if not query:
        return {"success": False, "message": "No query provided for recall."}

    try:
        # 1. Generate embedding for the search query using the local model
        model = get_local_model()
        query_embedding_array = model.encode(query)
        query_embedding = query_embedding_array.tolist()

        # 2. Connect to the DB and prepare for the search
        conn = get_db_connection()
        if not conn:
            return {"success": False, "message": "Failed to connect to Hippocampus DB."}

        cursor = conn.cursor()

        # 3. Build the query dynamically based on the presence of filter_dict
        if filter_dict:
            # Hybrid search: Vector distance + JSONB metadata filter
            filter_json = json.dumps(filter_dict)
            search_query = """
                SELECT id, content, metadata, embedding <=> %s::vector AS distance
                FROM hippocampus
                WHERE metadata::jsonb @> %s::jsonb
                ORDER BY distance ASC
                LIMIT %s;
            """
            cursor.execute(search_query, (query_embedding, filter_json, limit))
        else:
            # Pure semantic search: Vector distance only
            search_query = """
                SELECT id, content, metadata, embedding <=> %s::vector AS distance
                FROM hippocampus
                ORDER BY distance ASC
                LIMIT %s;
            """
            cursor.execute(search_query, (query_embedding, limit))
            
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()

        # 4. Format the results
        memories = []
        for row in results:
            memory_id, content, metadata, distance = row
            memories.append({
                "id": memory_id,
                "content": content,
                "metadata": metadata,
                "distance": float(distance) # The closer to 0, the more relevant
            })

        return {
            "success": True,
            "memories": memories,
            "message": f"Retrieved {len(memories)} memories."
        }

    except Exception as e:
        return {"success": False, "message": f"Failed to recall memory: {str(e)}"}