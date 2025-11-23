import os
from typing import Any, Dict, Optional
import httpx


class SpoonOSClient:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base = base_url or os.getenv("SPOONOS_API", "http://localhost:8080")
        self.key = api_key or os.getenv("SPOONOS_API_KEY", "dev")
        self.headers = {"Authorization": f"Bearer {self.key}"}

    async def spawn(self, manifest: Dict[str, Any]) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{self.base}/v1/sandboxes", json=manifest, headers=self.headers)
            r.raise_for_status()
            data = r.json()
            return data.get("id") or data.get("sandboxId") or data.get("sandbox_id")

    async def call_json(self, sandbox_id: str, route: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                f"{self.base}/v1/sandboxes/{sandbox_id}/call",
                json={"route": route, "input": payload},
                headers=self.headers,
            )
            r.raise_for_status()
            return r.json()

    def logs_url(self, sandbox_id: str) -> str:
        return f"{self.base}/v1/sandboxes/{sandbox_id}/logs"