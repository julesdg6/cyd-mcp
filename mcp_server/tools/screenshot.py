from __future__ import annotations

import json
from pathlib import Path

from mcp_server.config import SCREENSHOT_DIR, ensure_runtime_directories
from mcp_server.render import write_placeholder_png
from mcp_server.state import append_log, load_state, save_state
from mcp_server.tools.boards import get_board


def capture_screenshot(filename: str | None = None) -> dict:
    ensure_runtime_directories()
    state = load_state()
    if not state.get("running"):
        raise ValueError("No emulator session is currently running.")
    board = get_board(state["board"])
    if not filename:
        filename = f"{state['session_id']}-screen.png"
    elif not filename.endswith(".png"):
        filename = f"{filename}.png"
    path = SCREENSHOT_DIR / Path(filename).name
    write_placeholder_png(path)
    metadata = {
        "board": state["board"],
        "resolution": board["resolution"],
        "current_screen": state.get("current_screen", "home"),
        "events": len(state.get("events", [])),
    }
    path.with_suffix(path.suffix + ".json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    state["last_screenshot"] = str(path)
    save_state(state)
    append_log(f"Screenshot captured at {path}", state.get("log_path"))
    return {"success": True, "filename": path.name, "path": str(path), "metadata": metadata}
