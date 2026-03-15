import asyncio
import uuid
import os
import datetime
from database.db_files_data import get_file_data
from workers.worker_registry import active_workers
from database.db_attention import (
    create_attention_record,
    get_attention_record,
    search_attentions_db,
    bump_attention,
    get_attention_context_tree
)

#########################################
def create_attention(name: str, required_app: str = None, parent_id: str = None, 
                     tags: list = None, short_summary: str = None, 
                     detailed_summary: str = None, working_files: list = None) -> dict:
    """
    Creates a new Attention node in the database.
    Returns the newly created attention dictionary if successful.
    """
    if tags is None:
        tags = []
    if working_files is None:
        working_files = []
        
    attention_id = f"attn_{uuid.uuid4().hex[:8]}" # TBD: not a real unique ID generator, but good enough for now
    
    success = create_attention_record(
        attention_id=attention_id,
        parent_id=parent_id,
        name=name,
        required_app=required_app,
        tags=tags,
        short_summary=short_summary,
        detailed_summary=detailed_summary,
        working_files=working_files
    )
    
    # attentions (
    #         id VARCHAR(50) PRIMARY KEY,
    #         parent_id VARCHAR(50) REFERENCES attentions(id) ON DELETE CASCADE,
    #         name VARCHAR(255) NOT NULL,
    #         required_app VARCHAR(100),
    #         tags JSONB DEFAULT '[]'::jsonb,
    #         status VARCHAR(50) DEFAULT 'ready',
    #         short_summary TEXT,
    #         detailed_summary TEXT,
    #         working_files JSONB DEFAULT '[]'::jsonb,
    #         created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    #         updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    # )
    
    if success:
        # Load it right back to get the full record with timestamps
        return load_attention(attention_id)
    
    print(f"[Attention Ops] Error: Could not create attention '{name}'")
    return None

#########################################
def load_attention(attention_id: str) -> dict:
    """
    Loads an existing Attention by its ID and bumps its updated_at timestamp.
    """
    record = get_attention_record(attention_id)
    
    if record:
        # The "Bump" - Every time we load an attention, it becomes the most recent
        bump_attention(attention_id)
        return record
        
    print(f"[Attention Ops] Warning: Attention '{attention_id}' not found.")
    return None

##########################################
def search_attentions(app_filter: str = None, status_filter: str = None, tag_filter: str = None, name_filter: str = None) -> list:
    """
    Searches the database for Attentions matching the criteria.
    Results are automatically ordered by the most recently updated.
    """
    return search_attentions_db(
        app_filter=app_filter, 
        status_filter=status_filter,
        tag_filter=tag_filter, 
        name_filter=name_filter
    )

#########################################
# def update_attention(attention_id: str, **kwargs) -> bool:
# REMOVED - handled using the asinq worker !

#########################################
def get_lod_context(attention_id: str) -> dict:
    """
    Retrieves the full Level of Detail (LOD) tree for the AI's context window.
    Includes self (LOD 0), relatives (LOD 1), and distant nodes (LOD 2).
    """
    tree = get_attention_context_tree(attention_id)
    if not tree:
        print(f"[Attention Ops] Warning: Could not fetch LOD tree for '{attention_id}'.")
    return tree

#########################################
def update_session_attention(session_context: dict, active_file: str = None, context_files: list = None) -> None:
    """
    Updates the session's active attention with the current UI and terminal context.
    Implements a 3-layer caching strategy: Session Cache -> DB Cache -> Fallback to Worker.
    """
    if active_file and os.path.exists(active_file):
        active_file = os.path.abspath(active_file)
    
    if context_files is None:
        context_files = []
        
    # 1. Ensure active_attention exists in the session_context
    if "active_attention" not in session_context:
        from core_utils.attention_ops import create_attention
        session_context["active_attention"] = create_attention(name="Dynamic UI Attention")
        
    active_attention = session_context["active_attention"]
    
    # Ensure working_files is a dictionary, not a list
    if "working_files" not in active_attention or not isinstance(active_attention["working_files"], dict):
        active_attention["working_files"] = {}
        
    working_files = active_attention["working_files"]   

    # 2. Combine files into a unique set to avoid redundant processing
    files_to_process = set(context_files)
    if active_file:
        files_to_process.add(active_file)

    # 3. Process each file using the 3-layer lazy loading logic
    for file_path in files_to_process:
        if not os.path.exists(file_path):
            continue

        try:
            # Use UTC timestamp to match database format and prevent comparison issues
            current_mtime_float = os.path.getmtime(file_path)
            current_mtime = datetime.datetime.fromtimestamp(current_mtime_float, tz=datetime.timezone.utc)

            # --- Layer 1: Session Cache (Short-term memory) ---
            cached_file = working_files.get(file_path)
            if cached_file and cached_file.get("status") == "ready" and cached_file.get("last_modified") == current_mtime:
                # File is already up-to-date in the current session
                cached_file["is_active"] = (file_path == active_file)
                continue 

            # --- Layer 2: DB Cache (Long-term memory) ---
            db_data = get_file_data(file_path)
            is_fresh_in_db = db_data and db_data.get("file_last_modified") == current_mtime

            if is_fresh_in_db and db_data.get("long_summary"):
                # Load existing summary from Database
                working_files[file_path] = {
                    "path": file_path,
                    "status": "ready",
                    "last_modified": current_mtime,
                    "long_summary": db_data["long_summary"],
                    "short_summary": db_data.get("short_summary", ""),
                    "is_active": (file_path == active_file)
                }
                continue

            # --- Layer 3: Fallback & Background Worker Dispatch ---
            # File is new or modified; provide temp lines while worker processes the full summary
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            preview = "".join(lines[:20])
            
            working_files[file_path] = {
                "path": file_path,
                "status": "pending_worker",
                "last_modified": current_mtime,
                "long_summary": f"[Temp Preview - Processing Background Summary...]\n{preview}...\n",
                "short_summary": "Processing...",
                "is_active": (file_path == active_file)
            }
            
            # Dispatch summarization task (Fire and Forget)
            doc_agent = active_workers.get("doc_agent")
            if doc_agent:
                # Use the running loop to schedule the async task from a sync function
                loop = asyncio.get_running_loop()
                loop.create_task(doc_agent.add_task({"file_path": file_path}))

        except Exception as e:
            print(f"[Attention Ops Error] Could not process {file_path}: {e}")

#########################################
def shift_attention(session_context: dict, attention_id: str) -> bool:
    """
    Loads an Attention context, stores it in the session, and dynamically mounts its required App.
    """
    # 1. Load the attention metadata using the ops module
    attn_data = load_attention(attention_id)
    if not attn_data:
        print(f"[Core Error] Attention ID '{attention_id}' not found.")
        return False
        
    # Store the active attention directly in our session context
    session_context["active_attention"] = attn_data
    
    print(f"\n[Core] Shifting attention to: '{attn_data.get('name')}'")