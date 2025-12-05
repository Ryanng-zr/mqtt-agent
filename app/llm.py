import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# Prefer GEMINI_API_KEY for backward compatibility, but also support GOOGLE_API_KEY
_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

if not _API_KEY:
    raise RuntimeError("Please set GEMINI_API_KEY or GOOGLE_API_KEY.")

# This chat model can be plugged into LangChain/LangGraph create_agent helpers
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    api_key=_API_KEY,
    temperature=0.2,
)
