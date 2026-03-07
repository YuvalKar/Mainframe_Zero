"""
SYNAPSE: hippo_recall
PURPOSE: This is your memory retrieval tool. It searches the Hippocampus 
         (PostgreSQL vector DB) for the most semantically relevant memories 
         based on a given context or question.
"""

import sys
import os
import json

# Add the parent directory (Mainframe_Zero) to the Python path for direct execution
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from core_utils.memory_db import get_db_connection, get_local_model

def execute(query: str, limit: int = 3) -> dict:
    # Ensure there is a query to search for
    if not query:
        return {"success": False, "message": "No query provided for recall."}

    try:
        # 1. Generate embedding for the search query using the local model
        model = get_local_model()
        query_embedding_array = model.encode(query)
        query_embedding = query_embedding_array.tolist()

        # 2. Connect to the DB and perform the vector similarity search
        conn = get_db_connection()
        if not conn:
            return {"success": False, "message": "Failed to connect to Hippocampus DB."}

        cursor = conn.cursor()

        # Using the <=> operator for cosine distance (standard for semantic search)
        # We order by distance ASC (lowest distance = highest similarity)
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

        # 3. Format the results
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

# Test script to verify the recall process locally
def run_test():
    print("Searching the Hippocampus...\n")
    
    # Let's search for something related to the memory we encoded earlier
    test_query = "What is the release date for the project?"
    
    result = execute(query=test_query)
    
    if result.get("success"):
        for i, mem in enumerate(result.get("memories", [])):
            print(f"--- Result {i+1} (Distance: {mem['distance']:.4f}) ---")
            print(f"Content: {mem['content']}")
            print(f"Metadata: {json.dumps(mem['metadata'])}\n")
    else:
        print(f"Error: {result.get('message')}")

if __name__ == "__main__":
    run_test()