"""
SYNAPSE: hippo_forget
PURPOSE: This is your active memory deletion tool. Use this synapse to physically 
         delete a specific memory ID if it is proven to be false, outdated, or 
         polluting the database.
         
WHEN TO USE: 
- When a memory is no longer relevant, incorrect, or redundant.
- To keep the Hippocampus clean from bad data.

INPUTS:
- memory_id (int): The unique ID of the memory you want to delete.
"""

from core_utils.memory_db import get_db_connection

def execute(memory_id: int) -> dict:
    # Ensure a valid memory ID is provided
    if not memory_id:
        return {"success": False, "message": "No memory ID provided to forget."}

    try:
        # Connect to the PostgreSQL Hippocampus database
        conn = get_db_connection()
        if not conn:
            return {"success": False, "message": "Failed to connect to Hippocampus DB."}

        cursor = conn.cursor()

        # Delete query targeting the specific memory ID
        delete_query = "DELETE FROM hippocampus WHERE id = %s;"
        cursor.execute(delete_query, (memory_id,))
        
        # Check how many rows were affected by the query
        deleted_count = cursor.rowcount
        conn.commit()
        
        cursor.close()
        conn.close()

        # Return appropriate message based on whether the row existed
        if deleted_count > 0:
            return {
                "success": True, 
                "message": f"Successfully deleted memory ID {memory_id} from the Hippocampus."
            }
        else:
            return {
                "success": False, 
                "message": f"Memory ID {memory_id} not found in the Hippocampus."
            }

    except Exception as e:
        return {"success": False, "message": f"Failed to forget memory: {str(e)}"}