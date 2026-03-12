import uuid
from database.db_attention import (
    create_attention_record,
    get_attention_record,
    search_attentions_db,
    bump_attention,
    update_attention_record,
    get_attention_context_tree
)

class AttentionManager:
    def __init__(self):
        """
        Initialize the manager.
        We no longer use local folders; everything is managed via PostgreSQL.
        """
        pass

    def create_attention(self, name: str, required_app: str = None, parent_id: str = None, 
                         tags: list = None, short_summary: str = None, 
                         detailed_summary: str = None, working_files: list = None):
        """
        Creates a new Attention node in the database with full state support.
        Returns the newly created attention dictionary if successful.
        """
        if tags is None:
            tags = []
        if working_files is None:
            working_files = []
            
        attention_id = f"attn_{uuid.uuid4().hex[:8]}"
        
        success = create_attention_record(
            attention_id=attention_id,
            name=name,
            required_app=required_app,
            parent_id=parent_id,
            tags=tags,
            short_summary=short_summary,
            detailed_summary=detailed_summary,
            working_files=working_files
        )
        
        if success:
            # Load it right back to get the full record with timestamps
            return self.load_attention(attention_id)
        
        print(f"[AttentionManager] Error: Could not create attention '{name}'")
        return None

    def load_attention(self, attention_id: str) -> dict:
        """
        Loads an existing Attention by its ID and bumps its updated_at timestamp.
        """
        record = get_attention_record(attention_id)
        
        if record:
            # The "Bump" - Every time we load an attention, it becomes the most recent
            bump_attention(attention_id)
            return record
            
        print(f"[AttentionManager] Warning: Attention '{attention_id}' not found.")
        return None

    def search_attentions(self, app_filter: str = None, tag_filter: str = None, name_filter: str = None) -> list:
        """
        Searches the database for Attentions matching the criteria.
        Results are automatically ordered by the most recently updated.
        """
        return search_attentions_db(
            app_filter=app_filter, 
            tag_filter=tag_filter, 
            name_filter=name_filter
        )

    def update_attention(self, attention_id: str, **kwargs) -> bool:
        """
        Updates specific fields of an Attention (e.g., short_summary, working_files).
        Automatically bumps the updated_at timestamp.
        """
        success = update_attention_record(attention_id, **kwargs)
        if not success:
            print(f"[AttentionManager] Warning: Failed to update attention '{attention_id}'.")
        return success

    def get_lod_context(self, attention_id: str) -> dict:
        """
        Retrieves the full Level of Detail (LOD) tree for the AI's context window.
        Includes self (LOD 0), relatives (LOD 1), and distant nodes (LOD 2).
        """
        tree = get_attention_context_tree(attention_id)
        if not tree:
            print(f"[AttentionManager] Warning: Could not fetch LOD tree for '{attention_id}'.")
        return tree