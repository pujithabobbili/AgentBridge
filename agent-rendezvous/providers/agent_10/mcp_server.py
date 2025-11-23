from mcp.server.fastmcp import FastMCP
import json
from jsonschema import validate, Draft202012Validator

mcp = FastMCP("event-validator")

schema = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "start": {"type": "string"},
        "end": {"type": "string"},
        "location": {"type": "string"},
    },
    "required": ["title", "start"],
}

@mcp.tool()
def validate_event(event_json: str) -> str:
    try:
        data = json.loads(event_json)
        Draft202012Validator(schema).validate(data)
        return "Valid"
    except Exception as e:
        return f"Invalid: {str(e)}"

if __name__ == "__main__":
    mcp.run()
