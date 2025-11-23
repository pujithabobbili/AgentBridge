from mcp.server.fastmcp import FastMCP
from spoon_ai.tools.base import BaseTool
from openai import OpenAI
import os
import asyncio


class ChatGPTTool(BaseTool):
    name: str = "chat_complete"
    description: str = "ChatGPT completion for text input"
    parameters: dict = {
        "type": "object",
        "properties": {
            "prompt": {"type": "string"},
            "system": {"type": "string"},
        },
        "required": ["prompt"],
    }

    async def execute(self, prompt: str, system: str = "You are helpful") -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "Missing OPENAI_API_KEY"
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content or ""


mcp = FastMCP("chatgpt")


tool_instance = ChatGPTTool()


@mcp.tool()
def chat_complete(text: str, system: str = "You are helpful") -> str:
    return asyncio.get_event_loop().run_until_complete(tool_instance.execute(prompt=text, system=system))


if __name__ == "__main__":
    mcp.run()