from datetime import datetime
from zoneinfo import ZoneInfo

from deepagents import create_deep_agent
from langchain_core.messages import AIMessageChunk
from langgraph.checkpoint.memory import InMemorySaver

from utils.llm import load_llm
from utils.prompt import supervisor_prompt


class Agents:
    def __init__(self):
        self.llm_instance = load_llm
        self.checkpointer_instance = InMemorySaver()
        self.subagents = []

    def build_supervisor(self):
        current_datetime = datetime.now(ZoneInfo("Asia/Jakarta")).isoformat(
            timespec="seconds"
        )
        return create_deep_agent(
            model=self.llm_instance,
            system_prompt=supervisor_prompt.format(current_datetime=current_datetime),
            subagents=self.subagents,
            checkpointer=self.checkpointer_instance,
        )

    def ai_agent(self, user_input: str, session_id: str):
        agent_instance = self.build_supervisor()
        config = {"configurable": {"thread_id": session_id}}

        for chunk, _ in agent_instance.stream(
            {"messages": [{"role": "user", "content": user_input}]},
            config=config,
            stream_mode="messages",
        ):
            if not isinstance(chunk, AIMessageChunk):
                continue

            content = chunk.content

            if isinstance(content, str):
                if content:
                    yield content
            else:
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        if block.get("text"):
                            yield block["text"]
