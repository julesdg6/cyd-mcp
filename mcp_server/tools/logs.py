from __future__ import annotations

from pathlib import Path

from mcp_server.state import load_state


def read_logs(*, tail: int | None = None, follow: bool = False, full_log: bool = False) -> dict:
    state = load_state()
    log_path = state.get("log_path")
    if not log_path:
        return {"success": True, "log": "", "lines": [], "log_path": None}
    path = Path(log_path)
    if not path.exists():
        return {"success": True, "log": "", "lines": [], "log_path": str(path)}
    lines = path.read_text(encoding="utf-8").splitlines()
    if full_log:
        selected = lines
    elif tail is not None:
        selected = lines[-tail:]
    else:
        selected = lines
    return {
        "success": True,
        "log_path": str(path),
        "follow": follow,
        "lines": selected,
        "log": "\n".join(selected),
    }
