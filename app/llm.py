import google.generativeai as genai
import os
if "GEMINI_API_KEY" not in os.environ:
    raise RuntimeError("Please set GEMINI_API_KEY.")

genai.configure(api_key="AIzaSyAAopp9JM2R3SWfJcjN9hbUDGSdZx236i4")

# change this to use the create_agent

llm = genai.GenerativeModel("gemini-2.0-flash")
