"""
Attention Worker

Used for handling updating and summarizing the current attention state.
This worker operates independently of the main chat loop to ensure that it can 
process attention-related tasks without interfering with ongoing conversations.
Future use: indexing attentions to DB and hippocampus long memory.

INPUT: task_data dict with the following structure:
{
    "attention_id": str, # The unique identifier of the attention/memory to update
    "session_id": str,   # The ID of the current chat session to fetch recent context
    "timestamp": str     # ISO 8601 formatted timestamp with timezone (e.g., '2026-03-17T14:00:00+00:00') 
                         # used to filter chat history up to the exact moment the task was created
}
"""
from jinja2 import Template
import os
from jinja2 import Environment, FileSystemLoader

from database.db_attention import get_attention_record, update_attention_record
from workers.worker_base import BaseWorker
from workers.summarizer_agent import SummarizerAgent
from database.db_files_data import get_file_data
from database.db_chat_history import get_recent_chat_history


class AttentionWorker(BaseWorker):
    
    # We now accept the shared summarizer from the outside (Dependency Injection)
    def __init__(self, summarizer: SummarizerAgent):
        super().__init__(name="AttentionWorker")
        self.summarizer = summarizer

    async def process_task(self, task_data: dict):
        # Extract the new expected fields from the incoming task
        attention_id = task_data.get("attention_id")
        session_id = task_data.get("session_id")
        timestamp = task_data.get("timestamp")

        print(f"[{self.name}] Processing attention update for ID: {attention_id} ...")

        # Validate that we have all the necessary breadcrumbs to start working
        if not all([attention_id, session_id, timestamp]):
            print(f"[{self.name}] Missing required data (attention_id, session_id, or timestamp). Aborting.")
            return None

        # Fetch the main attention record from the database
        orig_attention_data = get_attention_record(attention_id)

        if not orig_attention_data:
            print(f"[{self.name}] Attention ID '{attention_id}' not found in DB.")
            return None
        
        # --- Data Gathering Phase ---
        
        # 1. Gather summaries for all working files attached to this attention
        working_files_data = [] # list of Dict
        for file_path in orig_attention_data.get("working_files", {}).keys():
            # Fetch file data from DB. Default section_name is ""
            file_info = get_file_data(file_path)
            if file_info:
                working_files_data.append(file_info)

        # 2. Gather data for the current focus (the specific file/segment the user is looking at)
        focus_data = None
        focus_dict = orig_attention_data.get("focus", {})
        if focus_dict and "file" in focus_dict:
            focus_path = focus_dict["file"]
            focus_segment = focus_dict.get("segment", "")
            # Fetch specific segment if it exists, otherwise just the file
            focus_data = get_file_data(focus_path, focus_segment)

        # 3. Gather recent chat history
        recent_chats = get_recent_chat_history(session_id, limit=10, timestamp=timestamp)
        
        # ... Next up: formatting all this gathered data! ...

        # Extract the existing context
        existing_context = orig_attention_data.get("detailed_summary") or orig_attention_data.get("short_summary") or ""

        # Setup Jinja environment to load templates from the 'prompt_templates' directory
        # We assume the worker runs from the project root. Adjust 'base_dir' if your directory structure is different.
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
        templates_dir = os.path.join(base_dir, 'prompt_templates')
        
        env = Environment(loader=FileSystemLoader(templates_dir))
        template = env.get_template('attention_summary.j2')

        # Render the template with all our gathered data
        text_to_summarize = template.render(
            existing_context=existing_context,
            files=working_files_data,
            focus=focus_data,
            chats=recent_chats
        )

        print(f"[{self.name}] Generated prompt from template successfully. Sending to summarizer...")

        # 5. Send to SummarizerAgent
        needs_name = (orig_attention_data.get("name") is None)
        summary_lengths = [80, 200, 600] if needs_name else [200, 600]

        summarizer_task = {
            "data": text_to_summarize,
            "summary_lengths": summary_lengths
        }

        # Take a number in line and get a beeper
        beeper = await self.summarizer.add_task(summarizer_task)
        
        # Wait until the summarizer finishes the task and rings the beeper
        summary_result = await beeper

        # 6. Prepare dictionary for DB updates and save
        updates = {}
        if "summaries" in summary_result:
            summaries = summary_result["summaries"]
            if needs_name and "80" in summaries:
                updates["name"] = summaries["80"]
            if "200" in summaries:
                updates["short_summary"] = summaries["200"]
            if "600" in summaries:
                updates["detailed_summary"] = summaries["600"]

        # Update the attention data in the database
        if updates:
            success = update_attention_record(attention_id, **updates)
            if not success:
                print(f"[{self.name}] Failed to update database for ID: {attention_id}")

        updated_record = get_attention_record(attention_id)
        print(f"[{self.name}] Successfully processed and updated ID: {attention_id}")
        
        return updated_record