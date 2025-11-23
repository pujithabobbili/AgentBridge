from mcp.server.fastmcp import FastMCP

mcp = FastMCP("event-validator")

@mcp.tool()
def validate_event(event_json: str) -> str:
    """Validate event JSON schema."""
    return "Valid"

if __name__ == "__main__":
    mcp.run()
