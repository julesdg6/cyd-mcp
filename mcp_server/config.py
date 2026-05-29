from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = Path(os.environ.get("CYD_CONFIG_DIR", "/config"))
WORKSPACE_DIR = Path(os.environ.get("CYD_WORKSPACE", "/workspace"))
IMAGE_DIR = Path(os.environ.get("CYD_IMAGE_DIR", "/images"))
OUTPUT_DIR = Path(os.environ.get("CYD_OUTPUT_DIR", "/output"))
CACHE_DIR = Path(os.environ.get("CYD_CACHE_DIR", "/cache"))
BOARD_DIR = Path(os.environ.get("CYD_BOARD_DIR", str(REPO_ROOT / "boards")))
DEFAULT_BOARD = os.environ.get("CYD_DEFAULT_BOARD", "cyd_28")
MCP_HOST = os.environ.get("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.environ.get("MCP_PORT", "32320"))
WEB_PORT = int(os.environ.get("WEB_PORT", "32321"))
NOVNC_PORT = int(os.environ.get("NOVNC_PORT", "32322"))
STATE_DIR = OUTPUT_DIR / "state"
STATE_FILE = STATE_DIR / "session.json"
SCREENSHOT_DIR = OUTPUT_DIR / "screenshots"
LOG_DIR = OUTPUT_DIR / "logs"
TEST_RESULT_DIR = OUTPUT_DIR / "test-results"
BUILD_DIR = OUTPUT_DIR / "builds"
SUPPORTED_IMAGE_SUFFIXES = {".bin", ".elf"}


def ensure_runtime_directories() -> None:
    for path in (
        CONFIG_DIR,
        WORKSPACE_DIR,
        IMAGE_DIR,
        OUTPUT_DIR,
        CACHE_DIR,
        STATE_DIR,
        SCREENSHOT_DIR,
        LOG_DIR,
        TEST_RESULT_DIR,
        BUILD_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)
