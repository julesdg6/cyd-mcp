from __future__ import annotations

import json
import time
from pathlib import Path

from mcp_server.config import REPO_ROOT, TEST_RESULT_DIR, WORKSPACE_DIR, ensure_runtime_directories
from mcp_server.tools.run import run_image, run_project
from mcp_server.tools.screenshot import capture_screenshot
from mcp_server.tools.swipe import swipe
from mcp_server.tools.touch import tap


def resolve_test_path(test_file: str) -> Path:
    candidate = Path(test_file)
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        repo_candidate = (REPO_ROOT / "tests" / candidate).resolve()
        resolved = repo_candidate if repo_candidate.exists() else (WORKSPACE_DIR / candidate).resolve()
    if not resolved.exists() or not resolved.is_file():
        raise ValueError(f"Test file does not exist: {resolved}")
    return resolved


def run_test(test_file: str) -> dict:
    ensure_runtime_directories()
    test_path = resolve_test_path(test_file)
    definition = json.loads(test_path.read_text(encoding="utf-8"))
    board = definition["board"]

    if "project_path" in definition:
        run_target = run_project(definition["project_path"], board)
    else:
        run_target = run_image(definition["image"], board)

    executed_steps = []
    for step in definition.get("steps", []):
        if "tap" in step:
            executed_steps.append(tap(*step["tap"]))
        elif "swipe" in step:
            executed_steps.append(swipe(*step["swipe"]))
        elif "wait_ms" in step:
            wait_ms = max(0, int(step["wait_ms"]))
            time.sleep(min(wait_ms, 50) / 1000)
            executed_steps.append({"success": True, "wait_ms": wait_ms})
        elif "screenshot" in step:
            executed_steps.append(capture_screenshot(step["screenshot"]))
        else:
            raise ValueError(f"Unsupported test step: {step}")

    report = {
        "success": True,
        "test_file": str(test_path),
        "board": board,
        "run_target": run_target,
        "steps_executed": executed_steps,
    }
    report_path = TEST_RESULT_DIR / f"{test_path.stem}-report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    report["report_path"] = str(report_path)
    return report
