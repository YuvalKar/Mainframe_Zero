"""
SENSE NAME: sense_db_schema
PURPOSE: Retrieves the current schema of the PostgreSQL database, including tables, columns, and data types.
         
WHEN TO USE: 
- When you need to understand the database structure before writing or reading data.
- To verify if a specific table (like 'history' or 'memory') exists in the database.
         
INPUTS:
- None
"""

from core_utils.memory_db import get_db_connection

def execute() -> dict:
    # 1. Establish connection using the existing utility
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Failed to connect to the database."}
        
    try:
        cursor = conn.cursor()
        
        # 2. Query the information_schema to get tables and columns for the public schema
        query = """
            SELECT table_name, column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            ORDER BY table_name, ordinal_position;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # 3. Format the output into a structured dictionary
        schema_dict = {}
        for table_name, column_name, data_type in rows:
            if table_name not in schema_dict:
                schema_dict[table_name] = []
            schema_dict[table_name].append({
                "column": column_name,
                "type": data_type
            })
            
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": f"Successfully retrieved schema for {len(schema_dict)} tables.",
            "data": schema_dict
        }
        
    except Exception as e:
        return {"success": False, "message": f"Failed to retrieve database schema: {str(e)}"}