from mcp.server.fastmcp import FastMCP

mcp = FastMCP("timezone-resolver")

@mcp.tool()
def resolve_timezone(location: str) -> str:
    """Resolve timezone for a location."""
    return f"Timezone for {location}: UTC"

if __name__ == "__main__":
    mcp.run()
