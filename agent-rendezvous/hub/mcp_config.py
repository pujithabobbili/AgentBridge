import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class McpServer:
    """Runtime representation of an MCP server configuration."""

    id: str
    command: str
    args: List[str]
    env: Dict[str, str]


class McpConfigError(Exception):
    """Raised when the MCP configuration file cannot be parsed."""


def _candidate_paths() -> List[Path]:
    project_root = Path(__file__).resolve().parent.parent
    paths: List[Optional[Path]] = [
        Path(os.environ["MCP_CONFIG_PATH"]).expanduser()
        if "MCP_CONFIG_PATH" in os.environ
        else None,
        project_root / ".cursor" / "mcp.json",
        project_root / "config" / "mcp-agents.json",
    ]
    return [p for p in paths if p is not None]


def load_mcp_servers() -> List[McpServer]:
    """Load MCP server definitions from the first available config file."""

    for path in _candidate_paths():
        if not path.exists():
            continue

        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            raise McpConfigError(f"Invalid MCP config JSON in {path}: {exc}") from exc

        servers = data.get("mcpServers", {})
        parsed: List[McpServer] = []

        for server_id, config in servers.items():
            command = config.get("command")
            if not command:
                raise McpConfigError(
                    f"MCP server '{server_id}' in {path} is missing 'command'"
                )

            args = config.get("args", [])
            env = config.get("env", {})

            parsed.append(
                McpServer(
                    id=server_id,
                    command=command,
                    args=[str(arg) for arg in args],
                    env={k: str(v) for k, v in env.items()},
                )
            )

        return parsed

    # No config found; return empty list by default.
    return []


def get_mcp_server(server_id: str) -> Optional[McpServer]:
    """Convenience helper to look up a single server by ID."""

    return next((server for server in load_mcp_servers() if server.id == server_id), None)


