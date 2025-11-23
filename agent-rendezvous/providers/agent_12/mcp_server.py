from mcp.server.fastmcp import FastMCP
from spoon_ai.tools.base import BaseTool
import google.generativeai as genai
import os
import asyncio


class GeminiTool(BaseTool):
    name: str = "gemini_complete"
    description: str = "Gemini text generation for a user prompt"
    parameters: dict = {
        "type": "object",
        "properties": {
            "prompt": {"type": "string"},
            "system": {"type": "string"},
            "model": {"type": "string"},
        },
        "required": ["prompt"],
    }

    async def execute(self, prompt: str, system: str = "You are helpful", model: str = "gemini-1.5-flash") -> str:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "Missing GEMINI_API_KEY"
        genai.configure(api_key=api_key)
        m = genai.GenerativeModel(model, system_instruction=system)
        resp = m.generate_content(prompt)
        return getattr(resp, "text", "") or ""


mcp = FastMCP("gemini")


tool_instance = GeminiTool()


@mcp.tool()
def gemini_complete(text: str, system: str = "You are helpful") -> str:
    return asyncio.get_event_loop().run_until_complete(tool_instance.execute(prompt=text, system=system))


if __name__ == "__main__":
    mcp.run()