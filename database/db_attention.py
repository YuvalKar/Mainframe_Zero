from database.db_connection import get_db_connection
import json

############################## Attention (LOD Hierarchy) DB ##############################

def init_attentions_db():
    """
    Initialize the hierarchical attentions table.
    WARNING: Drops the existing table to allow schema changes during development!
    """
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        
        # Drop the table if it exists (CASCADE ensures we also drop dependent rows if needed)
        cursor.execute("DROP TABLE IF EXISTS attentions CASCADE;")
        print("[System: Existing 'attentions' table dropped (if it existed).]")
        
        # Create the hierarchical table
        # Notice how parent_id references the id of the same table
        create_table_query = """
        CREATE TABLE attentions (
            id VARCHAR(50) PRIMARY KEY,
            parent_id VARCHAR(50) REFERENCES attentions(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            required_app VARCHAR(100),
            tags JSONB DEFAULT '[]'::jsonb,
            status VARCHAR(50) DEFAULT 'ready',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Create an index on parent_id to make tree traversal (LOD fetching) blazing fast
        create_index_query = """
        CREATE INDEX idx_attentions_parent ON attentions(parent_id);
        """
        
        cursor.execute(create_table_query)
        cursor.execute(create_index_query)
        conn.commit()
        print("[System: 'attentions' table initialized successfully.]")
        
    except Exception as e:
        print(f"[Memory DB Error: Failed to initialize attentions table - {e}]")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

#### Attention DB Operations #######

def create_attention_record(attention_id: str, name: str, required_app: str = None, 
                            parent_id: str = None, tags: list = None):
    """
    Inserts a new Attention node into the database.
    If parent_id is None, it acts as a root node.
    """
    conn = get_db_connection()
    if not conn:
        return False
        
    try:
        cursor = conn.cursor()
        
        # Ensure tags are stored as a JSON string for the JSONB column
        tags_json = json.dumps(tags) if tags else '[]'
        
        insert_query = """
        INSERT INTO attentions (id, parent_id, name, required_app, tags, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(insert_query, (attention_id, parent_id, name, required_app, tags_json, "ready"))
        conn.commit()
        return True
        
    except Exception as e:
        print(f"[Memory DB Error: Failed to create attention record - {e}]")
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_attention_record(attention_id: str) -> dict:
    """
    Retrieves a single Attention node by its ID, including the updated_at timestamp.
    """
    conn = get_db_connection()
    if not conn:
        return None
        
    try:
        cursor = conn.cursor()
        
        # Added updated_at to the SELECT query
        select_query = """
        SELECT id, parent_id, name, required_app, tags, status, created_at, updated_at
        FROM attentions
        WHERE id = %s
        """
        
        cursor.execute(select_query, (attention_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
            
        # Map the tuple to a dictionary for easy use in Python
        return {
            "id": row[0],
            "parent_id": row[1],
            "name": row[2],
            "required_app": row[3],
            "tags": row[4],  # psycopg2 automatically parses JSONB to a Python list/dict
            "status": row[5],
            "created_at": row[6].isoformat() if row[6] else None,
            "updated_at": row[7].isoformat() if row[7] else None
        }
        
    except Exception as e:
        print(f"[Memory DB Error: Failed to fetch attention record - {e}]")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def search_attentions_db(app_filter: str = None, tag_filter: str = None, name_filter: str = None) -> list:
    """
    Searches the attentions table based on optional filters.
    Orders by updated_at to show the most recently used contexts first.
    """
    conn = get_db_connection()
    if not conn:
        return []
        
    try:
        cursor = conn.cursor()
        
        # Added updated_at to the SELECT query
        query = "SELECT id, parent_id, name, required_app, tags, status, created_at, updated_at FROM attentions WHERE 1=1"
        params = []
        
        # Add filters dynamically
        if app_filter:
            query += " AND required_app = %s"
            params.append(app_filter)
            
        if name_filter:
            # ILIKE is PostgreSQL's case-insensitive search
            query += " AND name ILIKE %s"
            params.append(f"%{name_filter}%")
            
        if tag_filter:
            # The @> operator checks if the JSONB array contains the specified element
            query += " AND tags @> %s::jsonb"
            params.append(json.dumps([tag_filter]))
            
        # Order by the most recently updated first, not by creation date
        query += " ORDER BY updated_at DESC"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "parent_id": row[1],
                "name": row[2],
                "required_app": row[3],
                "tags": row[4],
                "status": row[5],
                "created_at": row[6].isoformat() if row[6] else None,
                "updated_at": row[7].isoformat() if row[7] else None
            })
            
        return results
        
    except Exception as e:
        print(f"[Memory DB Error: Failed to search attentions - {e}]")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def bump_attention(attention_id: str) -> bool:
    """
    Updates the 'updated_at' timestamp of a specific Attention node to CURRENT_TIMESTAMP.
    This ensures it floats to the top of recent searches.
    """
    conn = get_db_connection()
    if not conn:
        return False
        
    try:
        cursor = conn.cursor()
        
        # Update only the updated_at column
        update_query = """
        UPDATE attentions 
        SET updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        
        cursor.execute(update_query, (attention_id,))
        conn.commit()
        
        # Check if any row was actually updated
        if cursor.rowcount == 0:
            print(f"[Memory DB Warning: Tried to bump attention '{attention_id}' but it was not found.]")
            return False
            
        return True
        
    except Exception as e:
        print(f"[Memory DB Error: Failed to bump attention record - {e}]")
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
    # init_attentions_db()
    pass
