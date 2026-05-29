from __future__ import annotations

from mcp_server.config import IMAGE_DIR, SUPPORTED_IMAGE_SUFFIXES, ensure_runtime_directories


def list_images() -> list[str]:
    ensure_runtime_directories()
    return sorted(
        path.name for path in IMAGE_DIR.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES
    )
