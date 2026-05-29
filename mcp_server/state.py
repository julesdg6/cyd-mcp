from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp_server.config import DEFAULT_BOARD, LOG_DIR, STATE_FILE, ensure_runtime_directories

_LOCK = threading.Lock()


def _default_state() -> dict[str, Any]:
    return {
        "running": False,
        "board": DEFAULT_BOARD,
        "session_id": None,
        "source_type": None,
        "source_path": None,
        "project_path": None,
        "image_path": None,
        "log_path": None,
        "last_screenshot": None,
        "current_screen": "boot",
        "events": [],
        "started_at": None,
        "stopped_at": None,
    }


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_state() -> dict[str, Any]:
    ensure_runtime_directories()
    if not STATE_FILE.exists():
        return _default_state()
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def save_state(state: dict[str, Any]) -> dict[str, Any]:
    ensure_runtime_directories()
    with _LOCK:
        STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def append_log(message: str, log_path: str | None = None) -> None:
    state = load_state()
    target = Path(log_path or state.get("log_path") or (LOG_DIR / "session.log"))
    target.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with target.open("a", encoding="utf-8") as handle:
            handle.write(f"[{utc_now()}] {message}\n")


def start_session(
    board: str,
    source_type: str,
    source_path: str,
    *,
    project_path: str | None = None,
    image_path: str | None = None,
    initial_screen: str = "home",
) -> dict[str, Any]:
    ensure_runtime_directories()
    session_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = str(LOG_DIR / f"{session_id}.log")
    state = {
        "running": True,
        "board": board,
        "session_id": session_id,
        "source_type": source_type,
        "source_path": source_path,
        "project_path": project_path,
        "image_path": image_path,
        "log_path": log_path,
        "last_screenshot": None,
        "current_screen": initial_screen,
        "events": [],
        "started_at": utc_now(),
        "stopped_at": None,
    }
    save_state(state)
    append_log(f"Synthetic emulator booted for board {board}", log_path)
    append_log(f"Loaded {source_type}: {source_path}", log_path)
    append_log("LVGL demo scene rendered", log_path)
    return state
