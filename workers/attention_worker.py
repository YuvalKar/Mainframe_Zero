"""
Attention Worker

Used for handling updating, summarizing
This worker operates independently of the main chat loop to ensure that it can process attention-related tasks without interfering with ongoing conversations.
future use: indexing attentions to DB and hipocampus long memory

INPUT: task_data dict with the following structure:
{
    "attention_id": str, # The unique identifier of the attention/memory to update
    "new_data": str,     # The new content or information to update the attention with
    "metadata": dict     # Any additional metadata related to the attention
}
"""
from database.db_attention import get_attention_record, update_attention_record
from workers.worker_base import BaseWorker
from workers.summarizer_agent import SummarizerAgent

class AttentionWorker(BaseWorker):
    def __init__(self):
        super().__init__(name="AttentionWorker")
        # Instantiate the summarizer to be used within this worker
        self.summarizer = SummarizerAgent()

    async def process_task(self, task_data: dict):
        attention_id = task_data.get("attention_id")
        print(f"[{self.name}] Processing attention update for ID: {attention_id} ...")

        orig_attention_data = get_attention_record(attention_id)

        if not orig_attention_data:
            print(f"[{self.name}] Attention ID '{attention_id}' not found.")
            return None
        
        metadata = task_data.get("metadata", {})
        new_data = task_data.get("new_data", "")

        # Prepare a dictionary to hold the fields we want to update
        updates = metadata.copy()

        # Check if we need to summarize
        if len(new_data) > 200:
            # Determine if we need to generate a name (length 80)
            needs_name = (orig_attention_data.get("name") is None) and (metadata.get("name") is None)
            
            if needs_name:
                summary_lengths = [80, 200, 600] # Create name once
            else:
                summary_lengths = [200, 600]

            # Combine existing context with the new data for a comprehensive summary
            existing_context = orig_attention_data.get("detailed_summary") or orig_attention_data.get("short_summary") or ""
            text_to_summarize = f"{existing_context}\n\n{new_data}".strip()

            # Prepare the task for the SummarizerAgent
            summarizer_task = {
                "data": text_to_summarize,
                "summary_lengths": summary_lengths
            }

            # Call summarizer_agent directly (process_task returns the result dict)
            summary_result = await self.summarizer.process_task(summarizer_task)

            # Map the returned summaries to the correct database fields
            if "summaries" in summary_result:
                summaries = summary_result["summaries"]
                if needs_name and "80" in summaries:
                    updates["name"] = summaries["80"]
                if "200" in summaries:
                    updates["short_summary"] = summaries["200"]
                if "600" in summaries:
                    updates["detailed_summary"] = summaries["600"]
        else:
            # If the data is short, we can optionally just append it to the detailed summary 
            # to avoid losing information, or just rely on the metadata update.
            existing_detailed = orig_attention_data.get("detailed_summary") or ""
            updates["detailed_summary"] = f"{existing_detailed}\n{new_data}".strip()

        # Update the attention data in the database with the new summaries and metadata
        if updates:
            success = update_attention_record(attention_id, **updates)
            if not success:
                print(f"[{self.name}] Failed to update database for ID: {attention_id}")

        # Return the new data structure with the updated attention information
        updated_record = get_attention_record(attention_id)
        print(f"[{self.name}] Successfully processed and updated ID: {attention_id}")
        
        return updated_record