"""
Summarizer Agent

Used for generating summaries of conversations or toehr text data.
This agent operates independently of the main chat loop to ensure that it can process summarization tasks without interfering with ongoing conversations.

INPUT: task_data: dict
- data: text (like - the conversation history to summarize)
- summary_lengths: list with values of summary length to be created {40, 120, 500}
OUTPUT: a dict with the following structure:
{
    "summary_requested_length": int, # The length of the summary that was requested (e.g., 40, 120, 500)
    "summary": str,       # The generated summary text
}
"""
import os
import json
from dotenv import load_dotenv
from google import genai
from workers.worker_base import BaseWorker

# Resolve the path to the .env file located in the parent directory
# current_dir will be the 'workers' folder
current_dir = os.path.dirname(os.path.abspath(__file__))
# parent_dir will be 'Mainframe_Zero'
parent_dir = os.path.dirname(current_dir)
env_path = os.path.join(parent_dir, '.env')

# Load the environment variables before the class is defined or instantiated
load_dotenv(dotenv_path=env_path)

# The Specific Summarizer Agent
class SummarizerAgent(BaseWorker):
    def __init__(self):
        super().__init__(name="Summarizer")
        # Independent client so it doesn't interfere with the main chat loop
        self.client = genai.Client()

    async def process_task(self, task_data: dict):
        # Extracting the text data to summarize
        data = task_data.get("data")
        
        # Extracting the requested lengths, defaulting to [120] if empty
        summary_lengths = task_data.get("summary_lengths", [120])

        print(f"[{self.name}] Generating summaries for lengths: {summary_lengths}...")

        # Dynamically building the expected JSON structure for the prompt
        # Example output: '{"40": "A summary...", "120": "A summary..."}'
        expected_format = {str(length): f"A summary of approximately {length} characters" for length in summary_lengths}
        json_instruction = json.dumps(expected_format)

        prompt = f"""
        Please summarize the following text in multiple lengths.
        You must return a valid JSON object exactly in this format:
        {json_instruction}

        CRITICAL: Return ONLY the raw JSON object. Do not include any Markdown formatting, do not use ```json wrappers, and do not add any conversational text.

        Text to summarize:
        {data}
        """

        try:
            # Making the asynchronous call to the model
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )

            # Extracting the raw text response
            raw_response_text = response.text.strip()
            
            # Defensive programming: cleaning up markdown wrappers if the model ignored our instruction
            if raw_response_text.startswith("```json"):
                raw_response_text = raw_response_text[7:-3].strip()
            elif raw_response_text.startswith("```"):
                raw_response_text = raw_response_text[3:-3].strip()

            # Parsing the string response back into a Python dictionary
            summaries_dict = json.loads(raw_response_text)

            # Constructing the final output
            result = {
                "summary_requested_lengths": summary_lengths,
                "summaries": summaries_dict # The parsed dictionary from the LLM
            }

            print(f"[{self.name}] Summaries generated and parsed successfully.")
            
            return result

        except json.JSONDecodeError as e:
            print(f"[{self.name}] Error parsing JSON from LLM: {e}")
            print(f"[{self.name}] Raw LLM output was: {response.text}")
            return {"error": "Failed to parse summaries"}
        
        except Exception as e:
            print(f"[{self.name}] Error during LLM API call: {e}")
            return {"error": "Failed to generate summaries"}