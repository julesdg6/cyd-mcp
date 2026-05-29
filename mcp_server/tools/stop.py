from __future__ import annotations

from mcp_server.state import append_log, load_state, save_state, utc_now


def stop_emulator() -> dict:
    state = load_state()
    if not state.get("running"):
        return {"success": True, "message": "No emulator session is currently running."}
    state["running"] = False
    state["stopped_at"] = utc_now()
    save_state(state)
    append_log("Synthetic emulator stopped", state.get("log_path"))
    return {"success": True, "message": "Emulator stopped.", "session": state}
