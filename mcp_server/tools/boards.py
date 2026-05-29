from __future__ import annotations

import json
from pathlib import Path

from mcp_server.config import BOARD_DIR


def load_profiles() -> list[dict]:
    profiles: list[dict] = []
    for path in sorted(BOARD_DIR.glob("*.yaml")):
        profiles.append(json.loads(path.read_text(encoding="utf-8")))
    return profiles


def list_boards() -> list[str]:
    return [profile["name"] for profile in load_profiles()]


def get_board(board: str) -> dict:
    for profile in load_profiles():
        if profile["name"] == board:
            return profile
    raise ValueError(f"Unknown board profile: {board}")
