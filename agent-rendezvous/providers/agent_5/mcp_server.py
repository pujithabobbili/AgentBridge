from mcp.server.fastmcp import FastMCP
import json
import dateparser

mcp = FastMCP("event-normalizer")

@mcp.tool()
def normalize_event(data: str) -> str:
    try:
        obj = json.loads(data)
    except Exception:
        obj = {}
    title = (obj.get("title") or obj.get("name") or "").strip()
    start_raw = obj.get("start") or obj.get("date") or obj.get("start_time") or ""
    end_raw = obj.get("end") or obj.get("end_time") or ""
    start = dateparser.parse(str(start_raw))
    end = dateparser.parse(str(end_raw))
    norm = {
        "title": title,
        "start": start.isoformat() if start else "",
        "end": end.isoformat() if end else "",
        "location": (obj.get("location") or "").strip(),
    }
    return json.dumps(norm)

if __name__ == "__main__":
    mcp.run()
