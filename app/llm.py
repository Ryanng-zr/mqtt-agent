import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()
if "GEMINI_API_KEY" not in os.environ:
    raise RuntimeError("Please set GEMINI_API_KEY.")

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# change this to use the create_agent

llm = genai.GenerativeModel("gemini-2.0-flash")
