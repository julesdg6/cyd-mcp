from __future__ import annotations

from mcp_server.state import append_log, load_state, save_state, utc_now
from mcp_server.tools.boards import get_board


def swipe(x1: int, y1: int, x2: int, y2: int, duration_ms: int) -> dict:
    state = load_state()
    if not state.get("running"):
        raise ValueError("No emulator session is currently running.")
    board = get_board(state["board"])
    width = board["resolution"]["width"]
    height = board["resolution"]["height"]
    for x, y in ((x1, y1), (x2, y2)):
        if not (0 <= x < width and 0 <= y < height):
            raise ValueError(f"Swipe coordinates out of bounds for {state['board']}: ({x}, {y})")
    if duration_ms <= 0:
        raise ValueError("duration_ms must be positive")
    event = {
        "type": "swipe",
        "x1": x1,
        "y1": y1,
        "x2": x2,
        "y2": y2,
        "duration_ms": duration_ms,
        "timestamp": utc_now(),
    }
    state.setdefault("events", []).append(event)
    state["current_screen"] = "gesture"
    save_state(state)
    append_log(f"Swipe injected from ({x1}, {y1}) to ({x2}, {y2}) in {duration_ms}ms", state.get("log_path"))
    return {"success": True, "event": event}
