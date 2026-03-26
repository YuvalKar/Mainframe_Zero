"""
SYNAPSE: hippo_audit
PURPOSE: This is your metadata browsing tool. Use this to retrieve memories strictly 
         by metadata (e.g., date, category, tag) rather than semantic similarity.
         
WHEN TO USE: 
- When you need a list of all memories under a specific project, category, or date range.
- To review the contents of the database systematically without semantic fuzzy matching.

INPUTS:
- filter_dict (dict): A dictionary of key-value pairs to match in the metadata 
  (e.g., {"category": "architecture"}).
- limit (int): Maximum number of records to return. Default is 10.
"""

import json
from database.db_connection import get_db_connection, release_db_connection


def execute(filter_dict: dict, limit: int = 10) -> dict:
    # We need something to filter by, or at least a conscious decision to pull all
    if not filter_dict:
        return {"success": False, "message": "Please provide a filter_dict to audit specific memories."}

    try:
        # Connect to the PostgreSQL Hippocampus database
        conn = get_db_connection()
        if not conn:
            return {"success": False, "message": "Failed to connect to Hippocampus DB."}

        cursor = conn.cursor()

        # Convert the filter dictionary to a JSON string
        filter_json = json.dumps(filter_dict)

        # Query using PostgreSQL JSONB containment operator (@>)
        # This checks if the metadata column contains the exact key-value pairs in filter_json
        audit_query = """
            SELECT id, content, metadata
            FROM hippocampus
            WHERE metadata::jsonb @> %s::jsonb
            ORDER BY id DESC
            LIMIT %s;
        """
        
        cursor.execute(audit_query, (filter_json, limit))
        results = cursor.fetchall()
        
        cursor.close()
        release_db_connection(conn)

        # Format the output gracefully
        memories = []
        for row in results:
            memory_id, content, metadata = row
            memories.append({
                "id": memory_id,
                "content": content,
                "metadata": metadata
            })

        return {
            "success": True,
            "memories": memories,
            "message": f"Audited and found {len(memories)} matching memories."
        }

    except Exception as e:
        return {"success": False, "message": f"Failed to audit memories: {str(e)}"}