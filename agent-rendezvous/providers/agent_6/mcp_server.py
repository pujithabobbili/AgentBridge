from mcp.server.fastmcp import FastMCP
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

mcp = FastMCP("timezone-resolver")

@mcp.tool()
def resolve_timezone(location: str) -> str:
    geolocator = Nominatim(user_agent="agent-timezone-resolver")
    try:
        g = geolocator.geocode(location)
        if not g:
            return "UTC"
        tz = TimezoneFinder().timezone_at(lng=g.longitude, lat=g.latitude)
        return tz or "UTC"
    except Exception:
        return "UTC"

if __name__ == "__main__":
    mcp.run()
