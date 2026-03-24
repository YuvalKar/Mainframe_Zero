import asyncio
from datetime import datetime, timezone
from workers.worker_registry import active_workers
import uuid
import os
from datetime import datetime, timezone
from database.db_attention import (
    create_attention_record,
    get_attention_record,
    search_attentions_db,
    bump_attention,
    get_attention_context_tree,
    find_attention_by_focus,
    update_attention_record,
)

#########################################
def create_attention(name: str, required_app: str = None, parent_id: str = None, 
                     tags: list = None, short_summary: str = None, 
                     detailed_summary: str = None, working_files: dict = None,
                     focus: dict = None) -> dict:
    """
    Creates a new Attention node in the database.
    Returns the newly created attention dictionary if successful.
    """
    if tags is None:
        tags = []
    if working_files is None:
        working_files = {}
    if focus is None:
        focus = {}
        
    attention_id = f"attn_{uuid.uuid4().hex[:8]}" # TBD: not a real unique ID generator, but good enough for now
    
    success = create_attention_record(
        attention_id=attention_id,
        parent_id=parent_id,
        name=name,
        required_app=required_app,
        tags=tags,
        short_summary=short_summary,
        detailed_summary=detailed_summary,
        working_files=working_files,
        focus=focus
    )
    
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
def update_session_attention(session_context: dict, active_file: str = None, active_segment: str = None, context_files: list = None) -> None:
    """
    Updates the session's active attention based on the current UI focus.
    Evaluates if a context switch is needed based on the file and segment.
    """
    if context_files is None:
        context_files = []
        
    # 1. Build the new focus object dynamically
    new_focus = {}
    if active_file:
        # Force absolute path immediately, even if the file is just being created
        active_file_path = os.path.abspath(active_file) 
        new_focus["file"] = active_file_path
        if active_segment:
            new_focus["segment"] = active_segment # TODO: create properly and not just the incomming text!
            
    # 2. Ensure active_attention exists in the session_context
    if "active_attention" not in session_context:
        # Initial bootstrap for the session
        session_context["active_attention"] = create_attention(
            name="Initial UI Attention", 
            required_app="mainframe_architect",
            focus=new_focus
        )
        
    current_attention = session_context["active_attention"]
    current_focus = current_attention.get("focus", {})
    
    # 3. Clean up and Update working_files (List Comparison Logic)
    # We work on the dictionary in memory to keep existing data intact
    if "working_files" not in current_attention or not isinstance(current_attention["working_files"], dict):
        current_attention["working_files"] = {}
        
    working_files = current_attention["working_files"]
    
    # Create the target list of absolute paths from the UI
    ui_paths = {os.path.abspath(f) for f in context_files}
    if active_file:
        ui_paths.add(os.path.abspath(active_file))

    # A. Remove files that are no longer in the UI focus
    paths_to_remove = [p for p in working_files if p not in ui_paths]
    for p in paths_to_remove:
        del working_files[p]
        print(f"[Attention Ops] Removed from session: {p}")

    # B. Add new files that aren't in our memory yet
    for p in ui_paths:
        if p not in working_files:
            # We only add the path and a 'pending' status. 
            # Another mechanism (Hydrate) will fill this with data if needed.
            working_files[p] = {
                "path": p,
                "status": "new_in_session"
            }
            print(f"[Attention Ops] Added to session: {p}")
                        
    # C. Existing files? We don't touch them. Their data (summaries, etc.) stays exactly as is.
    # TODO somthing is missing, we need to find files data and inject to attention
    
    # 4. The Crossroads: Did the focus actually change?
    if new_focus == current_focus:
        return
        
    print(f"[Attention Ops] Focus shift detected! From {current_focus} to {new_focus}")
    
    shift_attention(session_context, new_focus)
    
    pass

#########################################
def shift_attention(session_context: dict, new_focus: dict, app_name: str = None) -> bool:
    """
    Find or create an attention with the new focus and switch to it in the session context.
    """
    current_attention = session_context.get("active_attention")
    
    # --- Step A: Save the 'current_attention' to the DB before we lose it ---
    if current_attention and "id" in current_attention:

        # we update for the worker to have later
        update_attention_record(
            current_attention["id"],
            **current_attention, # This includes all the existing fields
        )

        # Prepare the exact data structure the worker expects
        task_data = {
            "attention_id": current_attention["id"],
            "session_id": session_context.get("session_id"), # Using .get() just to be safe
            "timestamp": datetime.now(timezone.utc).isoformat() 
        }

        # Fetch the worker from the registry and enqueue the task
        attention_worker = active_workers.get("attention")
        
        if attention_worker:
            try:
                # Catch the running event loop from the main chat
                loop = asyncio.get_running_loop()
                # Fire and forget the task into the background
                loop.create_task(attention_worker.add_task(task_data))
                print(f"[Attention] Worker task enqueued successfully for ID: {current_attention['id']}")
            except RuntimeError:
                # If for some reason we call this outside the main loop
                print("[Attention] ERROR: No running event loop found to enqueue task!")

    # --- Step B: Search the DB for an existing attention that has EXACTLY 'new_focus' ---
    existing_attention = find_attention_by_focus(focus_dict=new_focus, app_name=app_name)

    # --- Step C: If found -> Load it into session_context["active_attention"] ---
    if existing_attention:
        print(f"[Attention Ops] Found existing history for focus: {new_focus}. Switching...")
        
        # We already have the full record, no need to fetch it again
        session_context["active_attention"] = existing_attention
        
        # Explicitly bump the timestamp to mark it as the most recently active attention
        bump_attention(existing_attention["id"])
        
    # --- Step D: If not found -> Create a new attention with 'new_focus' ---
    else:
        print(f"[Attention Ops] No history for this focus. Creating new attention node...")
        
        # Hierarchy: the new attention is a child of the current one (LOD 1 relation)
        parent_id = current_attention["id"] if current_attention else None
        required_app = app_name if app_name else current_attention.get("required_app", None)
        
        # Construct a name based on the focus for clarity
        file_name = os.path.basename(new_focus.get("file", "Unknown"))
        segment = new_focus.get("segment", "")
        attn_name = f"Focus: {segment} in {file_name}" if segment else f"Focus: {file_name}"
        
        # We inherit the current tools (paths) to the new attention
        inherited_files = current_attention.get("working_files", {}) if current_attention else {}
        
        session_context["active_attention"] = create_attention(
            name=attn_name,
            required_app=required_app,
            parent_id=parent_id,
            focus=new_focus,
            working_files=inherited_files
        )
        
    return True