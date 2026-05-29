FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=32320 \
    WEB_PORT=32321 \
    NOVNC_PORT=32322 \
    CYD_CONFIG_DIR=/config \
    CYD_WORKSPACE=/workspace \
    CYD_IMAGE_DIR=/images \
    CYD_OUTPUT_DIR=/output \
    CYD_DEFAULT_BOARD=cyd_28 \
    ESP_IDF_VERSION=stable \
    QEMU_TARGET=esp32

WORKDIR /app
COPY . /app
RUN mkdir -p /config /workspace /images /output /cache
EXPOSE 32320 32321 32322
CMD ["python", "-m", "mcp_server.server"]
