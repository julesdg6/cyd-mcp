from __future__ import annotations

from mcp_server.state import append_log, load_state, save_state, utc_now
from mcp_server.tools.boards import get_board


def tap(x: int, y: int) -> dict:
    state = load_state()
    if not state.get("running"):
        raise ValueError("No emulator session is currently running.")
    board = get_board(state["board"])
    width = board["resolution"]["width"]
    height = board["resolution"]["height"]
    if not (0 <= x < width and 0 <= y < height):
        raise ValueError(f"Tap coordinates out of bounds for {state['board']}: ({x}, {y})")
    event = {"type": "tap", "x": x, "y": y, "timestamp": utc_now()}
    state.setdefault("events", []).append(event)
    state["current_screen"] = "interaction"
    save_state(state)
    append_log(f"Tap injected at ({x}, {y})", state.get("log_path"))
    return {"success": True, "event": event}
