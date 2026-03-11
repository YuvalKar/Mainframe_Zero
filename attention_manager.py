import os
import json
import uuid

class AttentionManager:
    def __init__(self, base_dir=".attentions"):
        """
        Initialize the manager. Sets up the base directory for all isolated workspaces.
        """
        self.base_dir = base_dir
        
        # Ensure the base directory exists
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def create_attention(self, name, target_app, tags=None):
        """
        Creates a new Attention workspace and saves its metadata.
        """
        if tags is None:
            tags = []
            
        attention_id = f"attn_{uuid.uuid4().hex[:8]}"
        attention_dir = os.path.join(self.base_dir, attention_id)
        os.makedirs(attention_dir, exist_ok=True)
        
        attention_data = {
            "id": attention_id,
            "name": name,
            "required_app": target_app,
            "attention_dir": attention_dir,
            "tags": tags,
            "chat_history": [], 
            "status": "ready"
        }
        
        self._save_metadata(attention_dir, attention_data)
        return attention_data

    def load_attention(self, attention_id):
        """
        Loads an existing Attention by its ID.
        """
        attention_dir = os.path.join(self.base_dir, attention_id)
        metadata_path = os.path.join(attention_dir, "attention_meta.json")
        
        if not os.path.exists(metadata_path):
            return None
            
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def search_attentions(self, app_filter=None, tag_filter=None, name_filter=None):
        """
        Scans the base directory and returns a list of Attentions matching the criteria.
        """
        results = []
        
        # Iterate over all folders in the base directory
        for folder_name in os.listdir(self.base_dir):
            attention_dir = os.path.join(self.base_dir, folder_name)
            metadata_path = os.path.join(attention_dir, "attention_meta.json")
            
            if os.path.isfile(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Apply filters
                if app_filter and data.get("required_app") != app_filter:
                    continue
                    
                if tag_filter and tag_filter not in data.get("tags", []):
                    continue
                    
                if name_filter and name_filter.lower() not in data.get("name", "").lower():
                    continue
                    
                results.append(data)
                
        return results

    def _save_metadata(self, attention_dir, data):
        """
        Internal helper to save the JSON metadata.
        """
        metadata_path = os.path.join(attention_dir, "attention_meta.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)