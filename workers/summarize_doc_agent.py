"""
Summarize doc Agent

Used for generating summaries of documents - python, MD, etc.
This agent operates independently of the main chat loop to ensure that it can process summarization tasks without interfering with ongoing conversations.
This agent also saves the data to the DB to be used in the future for context or long-term memory.

INPUT: task_data: dict
    "file_path": str  # The path to the document file to summarize

OUTPUT: a dict with the following structure:
{
    "short_summary": str  # A concise summary of the document (1-2 sentences)
    "long_summary": str   # A more detailed summary of the document (a few paragraphs)
}
"""
import os
import ast
import copy
import datetime
from workers.worker_base import BaseWorker
from workers.summarizer_agent import SummarizerAgent
from database.db_files_data import upsert_file_data, get_file_data

class SummarizeDocAgent(BaseWorker):

    # We now accept the shared summarizer from the outside (Dependency Injection)
    def __init__(self, summarizer: SummarizerAgent):
        super().__init__(name="Summarize Doc")
        self.summarizer = summarizer

    #####################
    async def process_task(self, task_data: dict):
        # Extracting the file path to summarize
        file_path = task_data.get("file_path")

        # Check if the file exists
        if not file_path or not os.path.isfile(file_path):
            print(f"[{self.name}] Error: File '{file_path}' not found.")
            return None
        
        # Get the file last updated time as a float
        file_timestamp_float = os.path.getmtime(file_path)
        
        # Convert float to a timezone-aware datetime object for DB compatibility
        file_timestamp = datetime.datetime.fromtimestamp(file_timestamp_float, tz=datetime.timezone.utc)

        # Look for the file with this timestamp in the files DB
        file_data = get_file_data(file_path)

        # If exists and time is OK, do nothing
        if file_data and file_data["file_last_modified"] == file_timestamp:
            print(f"[{self.name}] Info: File '{file_path}' is already summarized and up to date. Skipping summarization.")
            return None

        # If not in DB or too old, summarize and update the DB with the new summaries and timestamp
        # Added utf-8 encoding to prevent crashes on special characters
        with open(file_path, 'r', encoding='utf-8') as file:
            file_content = file.read()
        
        file_type = os.path.splitext(file_path)[1].lower()

        # Act according to the file type (for now we just support .py and .md)
        if file_type not in ['.py', '.md']:
            print(f"[{self.name}] Warning: Unsupported file type '{file_type}' for file '{file_path}'. Skipping summarization.")
            return None 
        
        return_val = {}

        if file_type == '.py':
            return_val = await self.summarize_py(file_content)
            
        elif file_type == '.md':
            return_val = await self.summarize_md(file_content)
        else:
            # TODO: split to sections if too long

            # name and summarize each section
            
            # summarize the whole thing
            pass

        # Keep the summaries in the DB with a reference to the file and the timestamp, 
        # so we can use it for context in the future and also to know when to update it if the file changes again
        upsert_file_data(file_path, file_last_modified=file_timestamp, **return_val)
        
        return return_val
    
    #########################################
    async def summarize_py(self, file_content: str) -> dict:
        
        use_full_file = len(file_content) < 1000
        return_val = {}

        if len(file_content) < 200:
            # No need to sum it up
            return_val["short_summary"] = file_content
            return_val["long_summary"] = file_content
            return return_val
        
        elif use_full_file:
            summarizer_task = {
                "summary_lengths": [120]
            }
        else:
            summarizer_task = {
                "summary_lengths": [120, 600]
            }
          
        summarizer_task["data"] = file_content

        # 1. Take a number in line and get a beeper (Future)
        beeper = await self.summarizer.add_task(summarizer_task)
        
        # 2. Wait until the summarizer finishes the task and rings the beeper
        summary_result = await beeper

        # Map the returned summaries to the correct database fields
        if "summaries" in summary_result:
            summaries = summary_result["summaries"]

            if "120" in summaries:
                return_val["short_summary"] = summaries["120"]
            if "600" in summaries:
                return_val["long_summary"] = summaries["600"]

        if not use_full_file:
            """
            Parses Python code and extracts beautifully formatted 
            signatures of functions and classes.
            """
            try:
                tree = ast.parse(file_content)
            except SyntaxError as e:
                # Returned as a dict to match expected type
                return {"error": f"Failed to parse code safely: {e}"}
                
            extracted_items = ''
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    
                    # 1. Create a shallow copy to avoid altering the original tree
                    node_copy = copy.copy(node)
                    
                    # 2. Remove decorators if you only want the raw 'def' (Optional)
                    node_copy.decorator_list = []
                    
                    # 3. Replace the actual body with a simple 'pass' statement
                    node_copy.body = [ast.Pass()]
                    
                    # 4. Convert the AST node back to a code string
                    unparsed_code = ast.unparse(node_copy)
                    
                    # 5. Extract just the signature by splitting before the 'pass'
                    clean_signature = unparsed_code.split(':\n')[0] + ':'
                    
                    extracted_items += clean_signature.strip() + '\n'
                
            if len(extracted_items) > 0:
                # Make sure long_summary is initialized before appending
                if "long_summary" not in return_val:
                    return_val["long_summary"] = ""
                return_val["long_summary"] += '\n[------- FUNCTIONS/CLASSES -------]\n'
                return_val["long_summary"] += extracted_items

        return return_val
    
    #########################################
    async def summarize_md(self, file_content: str) -> dict:
        return_val = {}

        if len(file_content) < 200:
            # No need to sum it up
            return_val["short_summary"] = file_content
            return_val["long_summary"] = file_content
            return return_val

        summarizer_task = {
            "data": file_content,
            "summary_lengths": [120]
        }

        # 1. Take a number in line and get a beeper (Future)
        beeper = await self.summarizer.add_task(summarizer_task)
        
        # 2. Wait until the summarizer finishes the task and rings the beeper
        summary_result = await beeper

        # Map the returned summaries to the correct database fields
        if "summaries" in summary_result:
            summaries = summary_result["summaries"]

            if "120" in summaries:
                return_val["short_summary"] = summaries["120"]
            
            # For MD files we don't need a detailed summary, but we can keep the original content
            return_val["long_summary"] = file_content

        return return_val