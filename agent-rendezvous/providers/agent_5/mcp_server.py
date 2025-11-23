from mcp.server.fastmcp import FastMCP

mcp = FastMCP("event-normalizer")

@mcp.tool()
def normalize_event(data: str) -> str:
    """Normalize event data structure."""
    return f"Normalized: {data}"

if __name__ == "__main__":
    mcp.run()
