import uuid
from database.db_attention import (
    create_attention_record,
    get_attention_record,
    search_attentions_db,
    bump_attention
)

class AttentionManager:
    def __init__(self):
        """
        Initialize the manager.
        We no longer use local folders; everything is managed via PostgreSQL.
        """
        # The base_dir and os.makedirs are gone! 
        pass

    def create_attention(self, name: str, required_app: str = None, parent_id: str = None, tags: list = None):
        """
        Creates a new Attention node in the database.
        Returns the newly created attention dictionary if successful.
        """
        if tags is None:
            tags = []
            
        attention_id = f"attn_{uuid.uuid4().hex[:8]}"
        
        # Insert into the database
        success = create_attention_record(
            attention_id=attention_id,
            name=name,
            required_app=required_app,
            parent_id=parent_id,
            tags=tags
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