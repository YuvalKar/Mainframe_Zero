from dotenv import load_dotenv
import os
from google import genai

# Replace 'YOUR_API_KEY' with your actual Gemini API key
# IMPORTANT: Don't push this to GitHub or share this file anywhere!
load_dotenv()
api_key = os.getenv("GENAI_API_KEY")

# Initialize the client with the explicitly provided key
client = genai.Client(api_key=api_key)

print("Fetching available Google models...\n")

# Loop through the available models and print their names
for model in client.models.list():
    print(model.name)