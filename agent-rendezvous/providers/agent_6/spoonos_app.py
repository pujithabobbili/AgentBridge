from fastapi import FastAPI, Request
import httpx
from geopy.geocoders import Nominatim
import os

app = FastAPI()


@app.post("/proposal")
async def proposal(req: Request):
    return {
        "est_cost_usd": 0.002,
        "est_latency_ms": 500,
        "confidence": 0.85,
        "plan": [
            "Geocode location",
            "Resolve timezone via TimezoneDB",
        ],
        "needs": {"inputs": ["location"]},
    }


@app.post("/execute")
async def execute(req: Request):
    body = await req.json()
    intent = body.get("intent") or {}
    inputs = intent.get("inputs") or {}
    location = inputs.get("location") or inputs.get("text") or ""
    geolocator = Nominatim(user_agent="timezone-resolver-spoonos")
    lat = None
    lng = None
    try:
        g = geolocator.geocode(location)
        if g:
            lat = g.latitude
            lng = g.longitude
    except Exception:
        ...
    tz_name = None
    cost_usd = 0.002
    latency_ms = 0
    async with httpx.AsyncClient(timeout=5.0) as client:
        if lat is not None and lng is not None:
            key = os.getenv("TIMEZONEDB_API_KEY") or ""
            url = f"https://api.timezonedb.com/v2.1/get-time-zone?key={key}&format=json&by=position&lat={lat}&lng={lng}"
            try:
                r = await client.get(url)
                latency_ms = int(r.elapsed.total_seconds() * 1000) if hasattr(r, "elapsed") else 500
                if r.status_code == 200:
                    data = r.json()
                    tz_name = data.get("zoneName") or data.get("timezone") or data.get("abbreviation")
            except Exception:
                ...
    result = {
        "status": "OK" if tz_name else "PARTIAL",
        "data": {
            "location": location,
            "lat": lat,
            "lng": lng,
            "timezone": tz_name or "UTC",
        },
        "metrics": {
            "latency_ms": latency_ms or 500,
            "cost_usd": cost_usd,
        },
        "evidence": {
            "artifacts": [],
            "root": "",
        },
    }
    return result