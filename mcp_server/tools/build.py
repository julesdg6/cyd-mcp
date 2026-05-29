from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from mcp_server.config import BUILD_DIR, WORKSPACE_DIR, ensure_runtime_directories
from mcp_server.tools.boards import get_board


def resolve_project_path(project_path: str) -> Path:
    candidate = Path(project_path)
    if not candidate.is_absolute():
        candidate = (WORKSPACE_DIR / candidate).resolve()
    else:
        candidate = candidate.resolve()
    if not candidate.exists() or not candidate.is_dir():
        raise ValueError(f"Project path does not exist: {candidate}")
    return candidate


def load_project_manifest(project_dir: Path) -> dict[str, Any]:
    manifest_path = project_dir / "manifest.json"
    if manifest_path.exists():
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    return {
        "name": project_dir.name,
        "boot_log": [
            f"Booting {project_dir.name}",
            "Initialising synthetic CYD display",
            "UI ready",
        ],
        "initial_screen": "home",
    }


def build_project(project_path: str, board: str, clean: bool = False) -> dict[str, Any]:
    ensure_runtime_directories()
    board_profile = get_board(board)
    project_dir = resolve_project_path(project_path)
    manifest = load_project_manifest(project_dir)
    target_dir = BUILD_DIR / project_dir.name
    if clean and target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    artifact_base = f"{project_dir.name}-{board}"
    artifact_payload = {
        "project": project_dir.name,
        "board": board,
        "chip": board_profile["chip"],
        "resolution": board_profile["resolution"],
        "manifest": manifest,
    }
    artifact_paths = []
    for suffix in (".bin", ".elf", "-merged-flash.bin"):
        artifact_path = target_dir / f"{artifact_base}{suffix}"
        artifact_path.write_text(json.dumps(artifact_payload, indent=2), encoding="utf-8")
        artifact_paths.append(str(artifact_path))

    build_log = [
        f"Resolved project: {project_dir}",
        f"Using board profile: {board}",
        f"Synthesised firmware artifacts in {target_dir}",
        f"Display target: {board_profile['resolution']['width']}x{board_profile['resolution']['height']}",
    ]
    return {
        "success": True,
        "project_path": str(project_dir),
        "board": board,
        "build_log": build_log,
        "output_files": artifact_paths,
        "manifest": manifest,
    }
