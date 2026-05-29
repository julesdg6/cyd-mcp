# cyd-mcp

`cyd-mcp` is a lightweight, Docker-friendly MCP-style service for building, launching, inspecting and testing Cheap Yellow Display (CYD) touchscreen projects with a synthetic ESP-IDF/QEMU workflow.

## Included capabilities

- Board profile discovery for `cyd_28`, `cyd_35`, `cyd_40`, and `cyd_50`
- Firmware image discovery from `/images`
- Synthetic project build output generation into `/output/builds`
- Project and image launch flows with persisted runtime state
- Serial log capture, screenshot capture, tap injection, swipe injection, and JSON test execution
- HTTP endpoints for the MCP API (`32320`), dashboard (`32321`), and noVNC-style viewer placeholder (`32322`)
- Docker Compose and Unraid template scaffolding for self-hosted deployment

## Running locally

```bash
python -m mcp_server.server
```

### Example MCP request

```bash
curl -s http://127.0.0.1:32320/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"cyd.list_boards","params":{}}'
```

## Test command

```bash
python -m unittest discover -s tests -p 'test_*.py'
```
