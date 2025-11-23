from mcp.server.fastmcp import FastMCP
from ics import Calendar, Event
import json
import dateparser

mcp = FastMCP("ics-builder")

@mcp.tool()
def build_ics(event_data: str) -> str:
    try:
        data = json.loads(event_data)
    except Exception:
        data = {}
    title = data.get("title") or "Event"
    start = dateparser.parse(str(data.get("start") or ""))
    end = dateparser.parse(str(data.get("end") or ""))
    cal = Calendar()
    ev = Event()
    ev.name = title
    if start:
        ev.begin = start
    if end:
        ev.end = end
    ev.location = data.get("location") or ""
    cal.events.add(ev)
    return str(cal)

if __name__ == "__main__":
    mcp.run()
