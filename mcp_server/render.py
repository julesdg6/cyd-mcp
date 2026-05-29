from __future__ import annotations

import base64
from pathlib import Path

_PLACEHOLDER_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wn2pS4AAAAASUVORK5CYII="
)


def write_placeholder_png(path: Path) -> None:
    path.write_bytes(_PLACEHOLDER_PNG)
