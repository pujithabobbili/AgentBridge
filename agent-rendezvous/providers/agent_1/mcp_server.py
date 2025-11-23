from mcp.server.fastmcp import FastMCP
import re

mcp = FastMCP("poster-ocr-regex")

@mcp.tool()
def extract_event_regex(text: str) -> str:
    """Extract event details from text using regex."""
    # Simple mock implementation
    event = {}
    date_match = re.search(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}', text)
    if date_match:
        event['date'] = date_match.group(0)
    return f"Extracted event: {event}"

if __name__ == "__main__":
    mcp.run()
