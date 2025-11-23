from mcp.server.fastmcp import FastMCP
import re
import json
import dateparser

mcp = FastMCP("poster-ocr-regex")

@mcp.tool()
def extract_event_regex(text: str) -> str:
    title = None
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if lines:
        title = lines[0][:120]
    date_candidate = None
    m = re.search(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:,\s*\d{4})?(?:\s+\d{1,2}:\d{2}\s*(?:AM|PM))?", text, re.IGNORECASE)
    if m:
        date_candidate = m.group(0)
    parsed = dateparser.parse(date_candidate or text, settings={"PREFER_DATES_FROM": "future"})
    event = {
        "title": title or "",
        "start": parsed.isoformat() if parsed else "",
    }
    return json.dumps(event)

if __name__ == "__main__":
    mcp.run()
