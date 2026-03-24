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
        
        cursor.execute("DROP TABLE IF EXISTS attentions CASCADE;")
        print("[System: Existing 'attentions' table dropped (if it existed).]")
        
        # Added short_summary, detailed_summary, working_files, and focus
        create_table_query = """
        CREATE TABLE attentions (
            id VARCHAR(50) PRIMARY KEY,
            parent_id VARCHAR(50) REFERENCES attentions(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            required_app VARCHAR(100),
            tags JSONB DEFAULT '[]'::jsonb,
            status VARCHAR(50) DEFAULT 'ready',
            short_summary TEXT,
            detailed_summary TEXT,
            working_files JSONB DEFAULT '{}'::jsonb,
            focus JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """
        
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
                            parent_id: str = None, tags: list = None,
                            short_summary: str = None, detailed_summary: str = None, 
                            working_files: dict = None, focus: dict = None):
    """
    Inserts a new Attention node into the database.
    If parent_id is None, it acts as a root node.
    """
    conn = get_db_connection()
    if not conn:
        return False
        
    try:
        cursor = conn.cursor()
        
        tags_json = json.dumps(tags) if tags else '[]'
        files_json = json.dumps(working_files) if working_files else '{}'
        focus_json = json.dumps(focus) if focus else '{}'
        
        insert_query = """
        INSERT INTO attentions (id, parent_id, name, required_app, tags, status, 
                              short_summary, detailed_summary, working_files, focus)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(insert_query, (attention_id, parent_id, name, required_app, 
                                      tags_json, "ready", short_summary, detailed_summary, files_json, focus_json))
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
    Retrieves a single Attention node by its ID.
    """
    conn = get_db_connection()
    if not conn:
        return None
        
    try:
        cursor = conn.cursor()
        
        select_query = """
        SELECT id, parent_id, name, required_app, tags, status, 
               short_summary, detailed_summary, working_files, focus,
               created_at, updated_at
        FROM attentions
        WHERE id = %s
        """
        
        cursor.execute(select_query, (attention_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
            
        return {
            "id": row[0],
            "parent_id": row[1],
            "name": row[2],
            "required_app": row[3],
            "tags": row[4],
            "status": row[5],
            "short_summary": row[6],
            "detailed_summary": row[7],
            "working_files": row[8],
            "focus": row[9],
            "created_at": row[10].isoformat() if row[10] else None,
            "updated_at": row[11].isoformat() if row[11] else None
        }
        
    except Exception as e:
        print(f"[Memory DB Error: Failed to fetch attention record - {e}]")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def search_attentions_db(app_filter: str = None, tag_filter: str = None, name_filter: str = None, status_filter: str = None) -> list:
    """
    Searches the attentions table based on optional filters.
    """
    conn = get_db_connection()
    if not conn:
        return []
        
    try:
        cursor = conn.cursor()
        
        query = """
        SELECT id, parent_id, name, required_app, tags, status, 
               short_summary, detailed_summary, working_files, focus,
               created_at, updated_at 
        FROM attentions WHERE 1=1
        """
        params = []
        
        # Re-added the status filter logic
        if status_filter:
            query += " AND status = %s"
            params.append(status_filter)
            
        if app_filter:
            query += " AND required_app = %s"
            params.append(app_filter)
            
        if name_filter:
            query += " AND name ILIKE %s"
            params.append(f"%{name_filter}%")
            
        if tag_filter:
            query += " AND tags @> %s::jsonb"
            params.append(json.dumps([tag_filter]))
            
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
                "short_summary": row[6],
                "detailed_summary": row[7],
                "working_files": row[8],
                "focus": row[9],
                "created_at": row[10].isoformat() if row[10] else None,
                "updated_at": row[11].isoformat() if row[11] else None
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

####################################################
def find_attention_by_focus(focus_dict: dict, app_name: str = None) -> dict:
    """
    Searches for the most recently updated Attention record 
    that matches the given focus EXACTLY.
    """
    conn = get_db_connection()
    if not conn:
        return None
            
    try:
        cursor = conn.cursor()
        
        # We cast the parameter to jsonb to safely compare it with the focus column
        query = """
        SELECT id, parent_id, name, required_app, tags, status, 
               short_summary, detailed_summary, working_files, focus,
               created_at, updated_at
        FROM attentions
        WHERE focus = %s::jsonb
        AND required_app = %s"
        ORDER BY updated_at DESC
        LIMIT 1
        """
        
        focus_json = json.dumps(focus_dict)
        cursor.execute(query, (focus_json, app_name))
        row = cursor.fetchone()
        
        if not row:
            return None
            
        return {
            "id": row[0],
            "parent_id": row[1],
            "name": row[2],
            "required_app": row[3],
            "tags": row[4],
            "status": row[5],
            "short_summary": row[6],
            "detailed_summary": row[7],
            "working_files": row[8],
            "focus": row[9],
            "created_at": row[10].isoformat() if row[10] else None,
            "updated_at": row[11].isoformat() if row[11] else None
        }
        
    except Exception as e:
        print(f"[Memory DB Error: Failed to find attention by focus - {e}]")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

#######################################################
def bump_attention(attention_id: str) -> bool:
    """
    Updates the 'updated_at' timestamp of a specific Attention node.
    """
    conn = get_db_connection()
    if not conn:
        return False
        
    try:
        cursor = conn.cursor()
        
        update_query = """
        UPDATE attentions 
        SET updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        
        cursor.execute(update_query, (attention_id,))
        conn.commit()
        
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

def update_attention_record(attention_id: str, **kwargs) -> bool:
    """
    Updates specific fields of an Attention record dynamically.
    Automatically bumps the updated_at timestamp.
    
    Example usage:
    update_attention_record('attn_123', short_summary="New status", focus={"primary_file": "main.py"})
    """
    if not kwargs:
        # If no fields were passed to update, just bump the timestamp
        return bump_attention(attention_id)
        
    conn = get_db_connection()
    if not conn:
        return False
        
    try:
        cursor = conn.cursor()

        # Whitelist of allowed columns to prevent SQL injection or accidental typos
        allowed_columns = {
            'name', 'parent_id', 'required_app', 'status', 
            'short_summary', 'detailed_summary', 'tags', 'working_files', 'focus'
        }
        
        set_clauses = []
        values = []
        
        for key, value in kwargs.items():

            if key in allowed_columns:
                set_clauses.append(f"{key} = %s")

                # Handle JSONB fields gracefully
                if key in ('tags', 'working_files', 'focus'):
                    # Use empty structures based on the expected type if None is passed
                    if value is None:
                        val_str = '[]' if key == 'tags' else '{}'
                    else:
                        val_str = json.dumps(value)
                    values.append(val_str)
                else:
                    values.append(value)
                    
        if not set_clauses:
            return bump_attention(attention_id)
            
        # The ultimate Bump: Always update the timestamp when modifying data
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        
        query = f"""
        UPDATE attentions 
        SET {', '.join(set_clauses)}
        WHERE id = %s
        """
        values.append(attention_id)
        
        cursor.execute(query, tuple(values))
        conn.commit()
        
        if cursor.rowcount == 0:
            print(f"[Memory DB Warning: Tried to update attention '{attention_id}' but it was not found.]")
            return False
            
        return True
        
    except Exception as e:
        print(f"[Memory DB Error: Failed to update attention record - {e}]")
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_attention_context_tree(attention_id: str) -> dict:
    """
    Retrieves the Level of Detail (LOD) context tree for a given Attention ID.
    Includes summaries, working files, and focus for context generation.
    """
    conn = get_db_connection()
    if not conn:
        return None
        
    try:
        cursor = conn.cursor()
        
        query = """
        WITH RECURSIVE
        tree_up AS (
            SELECT id, parent_id, name, required_app, tags, status, 
                   short_summary, detailed_summary, working_files, focus,
                   0 AS lod_level, 'self'::text AS relation
            FROM attentions WHERE id = %s
            UNION
            SELECT a.id, a.parent_id, a.name, a.required_app, a.tags, a.status, 
                   a.short_summary, a.detailed_summary, a.working_files, a.focus,
                   tu.lod_level + 1, 'parent'::text
            FROM attentions a
            INNER JOIN tree_up tu ON a.id = tu.parent_id
            WHERE tu.lod_level < 2 
        ),
        tree_down AS (
            SELECT id, parent_id, name, required_app, tags, status, 
                   short_summary, detailed_summary, working_files, focus,
                   0 AS lod_level, 'self'::text AS relation
            FROM attentions WHERE id = %s
            UNION
            SELECT a.id, a.parent_id, a.name, a.required_app, a.tags, a.status, 
                   a.short_summary, a.detailed_summary, a.working_files, a.focus,
                   td.lod_level + 1, 'child'::text
            FROM attentions a
            INNER JOIN tree_down td ON a.parent_id = td.id
            WHERE td.lod_level < 2 
        ),
        siblings AS (
            SELECT a.id, a.parent_id, a.name, a.required_app, a.tags, a.status, 
                   a.short_summary, a.detailed_summary, a.working_files, a.focus,
                   1 AS lod_level, 'sibling'::text AS relation
            FROM attentions a
            WHERE a.parent_id = (SELECT parent_id FROM attentions WHERE id = %s)
              AND a.id != %s
              AND a.parent_id IS NOT NULL
        )
        SELECT * FROM tree_up
        UNION
        SELECT * FROM tree_down WHERE relation != 'self'
        UNION
        SELECT * FROM siblings
        ORDER BY lod_level ASC, relation ASC;
        """
        
        cursor.execute(query, (attention_id, attention_id, attention_id, attention_id))
        rows = cursor.fetchall()
        
        context_tree = {
            "lod_0_self": None,
            "lod_1_relatives": [],
            "lod_2_distant": []
        }
        
        for row in rows:
            node = {
                "id": row[0],
                "parent_id": row[1],
                "name": row[2],
                "required_app": row[3],
                "tags": row[4],
                "status": row[5],
                "short_summary": row[6],
                "detailed_summary": row[7],
                "working_files": row[8],
                "focus": row[9],
                "relation": row[11] # row[10] is lod_level now
            }
            
            lod_level = row[10]
            
            if lod_level == 0:
                context_tree["lod_0_self"] = node
            elif lod_level == 1:
                context_tree["lod_1_relatives"].append(node)
            elif lod_level == 2:
                context_tree["lod_2_distant"].append(node)
                
        return context_tree
        
    except Exception as e:
        print(f"[Memory DB Error: Failed to fetch context tree - {e}]")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            
##################################
if __name__ == "__main__":
    # Run this once to create the new table with focus and updated_at
    # init_attentions_db()
    pass