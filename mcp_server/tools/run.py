from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mcp_server.config import IMAGE_DIR, SUPPORTED_IMAGE_SUFFIXES
from mcp_server.state import append_log, start_session
from mcp_server.tools.boards import get_board
from mcp_server.tools.build import build_project, load_project_manifest, resolve_project_path


def _load_image_manifest(image_path: Path) -> dict[str, Any]:
    try:
        return json.loads(image_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {
            "name": image_path.name,
            "boot_log": [
                f"Booting image {image_path.name}",
                "Synthetic framebuffer initialised",
                "UI ready",
            ],
            "initial_screen": "home",
        }


def resolve_image_path(image_path: str) -> Path:
    candidate = Path(image_path)
    if not candidate.is_absolute():
        candidate = (IMAGE_DIR / candidate).resolve()
    else:
        candidate = candidate.resolve()
    if not candidate.exists() or not candidate.is_file():
        raise ValueError(f"Image path does not exist: {candidate}")
    if candidate.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
        raise ValueError(f"Unsupported firmware image type: {candidate.suffix}")
    return candidate


def run_project(project_path: str, board: str) -> dict[str, Any]:
    get_board(board)
    build_result = build_project(project_path, board)
    project_dir = resolve_project_path(project_path)
    manifest = load_project_manifest(project_dir)
    state = start_session(
        board,
        "project",
        str(project_dir),
        project_path=str(project_dir),
        initial_screen=manifest.get("initial_screen", "home"),
    )
    for line in manifest.get("boot_log", []):
        append_log(line, state["log_path"])
    return {
        "success": True,
        "board": board,
        "project_path": str(project_dir),
        "build": build_result,
        "session": state,
    }


def run_image(image_path: str, board: str) -> dict[str, Any]:
    get_board(board)
    resolved_image = resolve_image_path(image_path)
    manifest = _load_image_manifest(resolved_image)
    state = start_session(
        board,
        "image",
        str(resolved_image),
        image_path=str(resolved_image),
        initial_screen=manifest.get("initial_screen", "home"),
    )
    for line in manifest.get("boot_log", []):
        append_log(line, state["log_path"])
    return {
        "success": True,
        "board": board,
        "image_path": str(resolved_image),
        "session": state,
        "manifest": manifest,
    }
