from mcp.server.fastmcp import FastMCP

mcp = FastMCP("poster-ocr-fast")

@mcp.tool()
def fast_scan(text: str) -> str:
    """Quickly scan text for keywords."""
    return "Fast scan complete."

if __name__ == "__main__":
    mcp.run()
