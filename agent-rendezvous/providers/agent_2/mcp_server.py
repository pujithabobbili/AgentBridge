from mcp.server.fastmcp import FastMCP
import dateparser

mcp = FastMCP("poster-ocr-dateparser")

@mcp.tool()
def parse_date(text: str) -> str:
    d = dateparser.parse(text, settings={"PREFER_DATES_FROM": "future"})
    return d.isoformat() if d else ""

if __name__ == "__main__":
    mcp.run()
