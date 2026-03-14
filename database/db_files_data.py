from database.db_connection import get_db_connection
import json

############################## Files Metadata ##############################

def init_files_data_db():
    """
    Initialize the files metadata table.
    WARNING: Drops the existing table to allow schema changes during development!
    """
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        
        cursor.execute("DROP TABLE IF EXISTS files_data CASCADE;")
        print("[System: Existing 'files_data' table dropped.]")
        
        # Notice the DEFAULT '' for section_name. 
        # This prevents NULL comparison issues when using ON CONFLICT later.
        create_table_query = """
        CREATE TABLE files_data (
            id SERIAL PRIMARY KEY,
            parent_id INTEGER REFERENCES files_data(id) ON DELETE CASCADE,
            file_path TEXT NOT NULL,
            section_name VARCHAR(255) DEFAULT '',
            file_last_modified TIMESTAMP WITH TIME ZONE,
            short_summary VARCHAR(120),
            long_summary VARCHAR(1200),
            tags JSONB,
            UNIQUE (file_path, section_name)
        );
        """
        
        create_index_queries = """
        CREATE INDEX idx_files_data_path ON files_data(file_path);
        CREATE INDEX idx_files_data_parent ON files_data(parent_id);
        CREATE INDEX idx_files_data_tags ON files_data USING GIN (tags);
        """
        
        cursor.execute(create_table_query)
        cursor.execute(create_index_queries)
        conn.commit()
        print("[System: 'files_data' table initialized successfully.]")
        
    except Exception as e:
        print(f"[DB Error: Failed to initialize files_data table - {e}]")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

#################################
def upsert_file_data(file_path: str, section_name: str = "", parent_id: int = None,
                     file_last_modified=None, short_summary: str = None,
                     long_summary: str = None, tags: list = None):
    """
    Inserts a new record OR updates an existing one if the file_path + section_name 
    already exists. This saves us from writing separate insert and update functions!
    """
    conn = get_db_connection()
    if not conn:
        return None
        
    try:
        cursor = conn.cursor()
        
        # Convert the python list of tags into a JSON string
        tags_json = json.dumps(tags) if tags else '[]'
        
        # The ON CONFLICT clause is the real magic here.
        query = """
        INSERT INTO files_data (parent_id, file_path, section_name, file_last_modified, short_summary, long_summary, tags)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (file_path, section_name) 
        DO UPDATE SET 
            file_last_modified = EXCLUDED.file_last_modified,
            short_summary = EXCLUDED.short_summary,
            long_summary = EXCLUDED.long_summary,
            tags = EXCLUDED.tags
        RETURNING id;
        """
        
        cursor.execute(query, (parent_id, file_path, section_name, file_last_modified, short_summary, long_summary, tags_json))
        inserted_id = cursor.fetchone()[0]
        conn.commit()
        return inserted_id
        
    except Exception as e:
        print(f"[DB Error: Failed to upsert file data - {e}]")
        if conn:
            conn.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

##########################################
def get_file_data(file_path: str, section_name: str = ""):
    """
    Retrieves a specific file or section.
    Returns a dictionary for easy access in Python.
    """
    conn = get_db_connection()
    if not conn:
        return None
        
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM files_data WHERE file_path = %s AND section_name = %s;"
        cursor.execute(query, (file_path, section_name))
            
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "parent_id": row[1],
                "file_path": row[2],
                "section_name": row[3],
                "file_last_modified": row[4],
                "short_summary": row[5],
                "long_summary": row[6],
                "tags": row[7]
            }
        return None
        
    except Exception as e:
        print(f"[DB Error: Failed to get file data - {e}]")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

################################################################
def search_files_by_tag(tag: str):
    """
    Finds all files containing a specific tag using the GIN index.
    """
    conn = get_db_connection()
    if not conn:
        return []
        
    try:
        cursor = conn.cursor()
        
        # Format the search term as a JSON array string to match the JSONB column
        search_json = json.dumps([tag])
        
        # The @> operator checks if our JSONB column contains the search_json
        query = "SELECT file_path, section_name, short_summary FROM files_data WHERE tags @> %s::jsonb;"
        cursor.execute(query, (search_json,))
        
        rows = cursor.fetchall()
        
        # List comprehension to keep things clean
        return [{"file_path": r[0], "section_name": r[1], "short_summary": r[2]} for r in rows]
        
    except Exception as e:
        print(f"[DB Error: Failed to search by tag - {e}]")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

##################################################
def delete_file_data(file_path: str):
    """
    Deletes a file. Thanks to 'ON DELETE CASCADE' in our schema, 
    this will automatically clean up all its sections too.
    """
    conn = get_db_connection()
    if not conn:
        return False
        
    try:
        cursor = conn.cursor()
        query = "DELETE FROM files_data WHERE file_path = %s;"
        cursor.execute(query, (file_path,))
        conn.commit()
        return True
    except Exception as e:
        print(f"[DB Error: Failed to delete file - {e}]")
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            

##################################
if __name__ == "__main__":
    # Run this once to create the new table with updated_at
    # init_files_data_db()
    pass
