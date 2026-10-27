import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

load_llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-6-luna"),
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=1,
    streaming=True,
)
