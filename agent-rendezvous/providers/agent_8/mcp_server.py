from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ics-builder")

@mcp.tool()
def build_ics(event_data: str) -> str:
    """Generate ICS file content."""
    return "BEGIN:VCALENDAR\nVERSION:2.0\nEND:VCALENDAR"

if __name__ == "__main__":
    mcp.run()
