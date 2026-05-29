from __future__ import annotations

import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable

from mcp_server.config import MCP_HOST, MCP_PORT, NOVNC_PORT, WEB_PORT, ensure_runtime_directories
from mcp_server.state import load_state
from mcp_server.tools.boards import list_boards
from mcp_server.tools.build import build_project
from mcp_server.tools.images import list_images
from mcp_server.tools.logs import read_logs
from mcp_server.tools.run import run_image, run_project
from mcp_server.tools.screenshot import capture_screenshot
from mcp_server.tools.stop import stop_emulator
from mcp_server.tools.swipe import swipe
from mcp_server.tools.test_runner import run_test
from mcp_server.tools.touch import tap

Method = Callable[..., Any]


METHODS: dict[str, Method] = {
    "cyd.list_boards": list_boards,
    "cyd.list_images": list_images,
    "cyd.build": build_project,
    "cyd.run_project": run_project,
    "cyd.run_image": run_image,
    "cyd.stop": stop_emulator,
    "cyd.logs": read_logs,
    "cyd.screenshot": capture_screenshot,
    "cyd.tap": tap,
    "cyd.swipe": swipe,
    "cyd.run_test": run_test,
}


class _BaseHandler(BaseHTTPRequestHandler):
    server_version = "cyd-mcp/0.1"

    def _send_json(self, payload: Any, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str, status: int = HTTPStatus.OK) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


class MCPHandler(_BaseHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json({"status": "ok", "service": "cyd-mcp"})
            return
        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if self.path != "/mcp":
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return
        content_length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(content_length) or b"{}")
        method_name = payload.get("method")
        params = payload.get("params") or {}
        request_id = payload.get("id")
        try:
            if method_name not in METHODS:
                raise ValueError(f"Unknown method: {method_name}")
            result = METHODS[method_name](**params) if isinstance(params, dict) else METHODS[method_name](*params)
            self._send_json({"jsonrpc": "2.0", "id": request_id, "result": result})
        except Exception as exc:  # noqa: BLE001
            self._send_json(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32000, "message": str(exc)},
                },
                status=HTTPStatus.BAD_REQUEST,
            )


class WebHandler(_BaseHandler):
    def do_GET(self) -> None:
        if self.path == "/api/status":
            self._send_json(
                {
                    "service": "cyd-mcp",
                    "boards": list_boards(),
                    "images": list_images(),
                    "state": load_state(),
                }
            )
            return
        if self.path != "/":
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return
        state = load_state()
        html = f"""
<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\">
    <title>cyd-mcp dashboard</title>
    <style>
      body {{ font-family: sans-serif; margin: 2rem; background: #111827; color: #f3f4f6; }}
      .card {{ background: #1f2937; padding: 1rem; border-radius: 0.75rem; margin-bottom: 1rem; }}
      code {{ color: #93c5fd; }}
    </style>
  </head>
  <body>
    <h1>cyd-mcp dashboard</h1>
    <div class=\"card\">
      <h2>Emulator status</h2>
      <p>Running: <strong>{state.get('running')}</strong></p>
      <p>Board: <strong>{state.get('board')}</strong></p>
      <p>Last screenshot: <code>{state.get('last_screenshot')}</code></p>
    </div>
    <div class=\"card\">
      <h2>Available boards</h2>
      <p>{", ".join(list_boards())}</p>
    </div>
    <div class=\"card\">
      <h2>Available images</h2>
      <p>{", ".join(list_images()) or 'No firmware images found in /images'}</p>
    </div>
  </body>
</html>
"""
        self._send_html(html)


class NoVNCHandler(_BaseHandler):
    def do_GET(self) -> None:
        state = load_state()
        html = f"""
<!doctype html>
<html lang=\"en\">
  <head><meta charset=\"utf-8\"><title>cyd-mcp viewer</title></head>
  <body>
    <h1>cyd-mcp synthetic display viewer</h1>
    <p>This lightweight viewer exposes the latest captured screenshot path for browser-based inspection.</p>
    <p>Current board: <strong>{state.get('board')}</strong></p>
    <p>Latest screenshot: <code>{state.get('last_screenshot')}</code></p>
  </body>
</html>
"""
        self._send_html(html)


def _serve(handler: type[_BaseHandler], port: int) -> None:
    server = ThreadingHTTPServer((MCP_HOST, port), handler)
    server.serve_forever()


def main() -> None:
    ensure_runtime_directories()
    threads = [
        threading.Thread(target=_serve, args=(MCPHandler, MCP_PORT), daemon=True),
        threading.Thread(target=_serve, args=(WebHandler, WEB_PORT), daemon=True),
        threading.Thread(target=_serve, args=(NoVNCHandler, NOVNC_PORT), daemon=True),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
