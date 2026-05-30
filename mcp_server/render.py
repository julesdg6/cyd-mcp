from __future__ import annotations

import struct
import zlib
from pathlib import Path

Color = tuple[int, int, int]

_STATUS_BAR = (22, 28, 44)
_PANEL = (245, 248, 255)
_PANEL_SHADOW = (213, 220, 238)
_TEXT = (39, 48, 70)
_ACCENT = (70, 120, 255)
_SUCCESS = (76, 175, 80)
_WARNING = (255, 179, 71)
_DANGER = (244, 96, 96)
_BACKGROUND_BY_SCREEN = {
    "boot": ((27, 36, 80), (66, 86, 190)),
    "home": ((78, 167, 255), (38, 95, 201)),
    "interaction": ((0, 188, 212), (0, 121, 182)),
    "gesture": ((138, 95, 255), (92, 56, 204)),
}


def _clamp(value: int, lower: int, upper: int) -> int:
    return max(lower, min(upper, value))


def _blend(start: Color, end: Color, weight: float) -> Color:
    return tuple(
        int(round(component_start + (component_end - component_start) * weight))
        for component_start, component_end in zip(start, end)
    )


def _set_pixel(buffer: bytearray, width: int, height: int, x: int, y: int, color: Color) -> None:
    if not (0 <= x < width and 0 <= y < height):
        return
    offset = (y * width + x) * 3
    buffer[offset : offset + 3] = bytes(color)


def _fill_rect(
    buffer: bytearray,
    width: int,
    height: int,
    x: int,
    y: int,
    rect_width: int,
    rect_height: int,
    color: Color,
) -> None:
    left = _clamp(x, 0, width)
    top = _clamp(y, 0, height)
    right = _clamp(x + rect_width, 0, width)
    bottom = _clamp(y + rect_height, 0, height)
    row = bytes(color) * max(0, right - left)
    for current_y in range(top, bottom):
        offset = (current_y * width + left) * 3
        buffer[offset : offset + len(row)] = row


def _draw_frame(
    buffer: bytearray,
    width: int,
    height: int,
    x: int,
    y: int,
    frame_width: int,
    frame_height: int,
    thickness: int,
    color: Color,
) -> None:
    _fill_rect(buffer, width, height, x, y, frame_width, thickness, color)
    _fill_rect(buffer, width, height, x, y + frame_height - thickness, frame_width, thickness, color)
    _fill_rect(buffer, width, height, x, y, thickness, frame_height, color)
    _fill_rect(buffer, width, height, x + frame_width - thickness, y, thickness, frame_height, color)


def _draw_line(
    buffer: bytearray,
    width: int,
    height: int,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    color: Color,
    thickness: int = 1,
) -> None:
    dx = abs(x2 - x1)
    dy = -abs(y2 - y1)
    step_x = 1 if x1 < x2 else -1
    step_y = 1 if y1 < y2 else -1
    error = dx + dy

    while True:
        radius = max(0, thickness // 2)
        _fill_rect(buffer, width, height, x1 - radius, y1 - radius, radius * 2 + 1, radius * 2 + 1, color)
        if x1 == x2 and y1 == y2:
            break
        doubled_error = 2 * error
        if doubled_error >= dy:
            error += dy
            x1 += step_x
        if doubled_error <= dx:
            error += dx
            y1 += step_y


def _draw_circle(
    buffer: bytearray,
    width: int,
    height: int,
    center_x: int,
    center_y: int,
    radius: int,
    color: Color,
) -> None:
    radius_squared = radius * radius
    for y in range(center_y - radius, center_y + radius + 1):
        for x in range(center_x - radius, center_x + radius + 1):
            if (x - center_x) ** 2 + (y - center_y) ** 2 <= radius_squared:
                _set_pixel(buffer, width, height, x, y, color)


def _draw_status_bar(buffer: bytearray, width: int, height: int, event_count: int) -> int:
    bar_height = max(24, height // 12)
    _fill_rect(buffer, width, height, 0, 0, width, bar_height, _STATUS_BAR)

    left_margin = max(10, width // 24)
    indicator_size = max(5, min(8, height // 48))
    for index in range(3):
        _draw_circle(
            buffer,
            width,
            height,
            left_margin + index * (indicator_size * 3),
            bar_height // 2,
            indicator_size,
            _SUCCESS,
        )

    event_width = min(width // 3, max(24, event_count * max(6, width // 40)))
    if event_width > 0:
        _fill_rect(
            buffer,
            width,
            height,
            width - left_margin - event_width,
            bar_height // 3,
            event_width,
            max(4, bar_height // 3),
            _WARNING,
        )
    return bar_height


def _draw_card(buffer: bytearray, width: int, height: int, top: int, screen_name: str, event_count: int) -> None:
    margin = max(12, width // 18)
    card_width = width - margin * 2
    card_height = max(height // 3, 92)
    _fill_rect(buffer, width, height, margin + 3, top + 4, card_width, card_height, _PANEL_SHADOW)
    _fill_rect(buffer, width, height, margin, top, card_width, card_height, _PANEL)
    _draw_frame(buffer, width, height, margin, top, card_width, card_height, 2, _ACCENT)

    title_height = max(16, card_height // 5)
    _fill_rect(buffer, width, height, margin + 10, top + 12, card_width - 20, title_height, _ACCENT)

    line_height = max(8, card_height // 10)
    first_line_width = max(40, card_width // 2 + len(screen_name) * 4)
    second_line_width = max(30, min(card_width - 40, card_width // 3 + event_count * 10))
    _fill_rect(buffer, width, height, margin + 10, top + 12 + title_height + 14, first_line_width, line_height, _TEXT)
    _fill_rect(
        buffer,
        width,
        height,
        margin + 10,
        top + 12 + title_height + 14 + line_height + 12,
        second_line_width,
        line_height,
        _TEXT,
    )


def _draw_footer_buttons(buffer: bytearray, width: int, height: int, screen_name: str) -> None:
    button_width = max(44, width // 4)
    button_height = max(26, height // 11)
    spacing = max(10, width // 24)
    total_width = button_width * 2 + spacing
    start_x = max(10, (width - total_width) // 2)
    y = height - button_height - max(14, height // 20)
    colors = (_SUCCESS, _DANGER if screen_name == "gesture" else _ACCENT)
    for index, color in enumerate(colors):
        x = start_x + index * (button_width + spacing)
        _fill_rect(buffer, width, height, x, y, button_width, button_height, color)
        _draw_frame(buffer, width, height, x, y, button_width, button_height, 2, _PANEL)


def _draw_events(buffer: bytearray, width: int, height: int, events: list[dict]) -> None:
    radius = max(4, min(width, height) // 40)
    for event in events[-8:]:
        if event.get("type") == "tap":
            _draw_circle(buffer, width, height, int(event["x"]), int(event["y"]), radius + 2, _PANEL)
            _draw_circle(buffer, width, height, int(event["x"]), int(event["y"]), radius, _DANGER)
        elif event.get("type") == "swipe":
            _draw_line(
                buffer,
                width,
                height,
                int(event["x1"]),
                int(event["y1"]),
                int(event["x2"]),
                int(event["y2"]),
                _PANEL,
                thickness=max(3, radius),
            )
            _draw_line(
                buffer,
                width,
                height,
                int(event["x1"]),
                int(event["y1"]),
                int(event["x2"]),
                int(event["y2"]),
                _WARNING,
                thickness=max(1, radius - 2),
            )
            _draw_circle(buffer, width, height, int(event["x2"]), int(event["y2"]), radius + 1, _DANGER)


def render_screen(width: int, height: int, current_screen: str, events: list[dict]) -> bytes:
    top_color, bottom_color = _BACKGROUND_BY_SCREEN.get(current_screen, _BACKGROUND_BY_SCREEN["home"])
    buffer = bytearray(width * height * 3)

    for y in range(height):
        shade = _blend(top_color, bottom_color, y / max(1, height - 1))
        row = bytes(shade) * width
        offset = y * width * 3
        buffer[offset : offset + len(row)] = row

    status_bar_height = _draw_status_bar(buffer, width, height, len(events))
    _draw_card(buffer, width, height, status_bar_height + max(14, height // 18), current_screen, len(events))
    _draw_footer_buttons(buffer, width, height, current_screen)
    _draw_events(buffer, width, height, events)
    return bytes(buffer)


def encode_png(width: int, height: int, pixels: bytes) -> bytes:
    signature = b"\x89PNG\r\n\x1a\n"
    raw = bytearray()
    row_width = width * 3
    for start in range(0, len(pixels), row_width):
        raw.append(0)
        raw.extend(pixels[start : start + row_width])

    def chunk(chunk_type: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + chunk_type
            + data
            + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    idat = zlib.compress(bytes(raw), level=9)
    return signature + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def write_screenshot_png(path: Path, width: int, height: int, current_screen: str, events: list[dict]) -> None:
    path.write_bytes(encode_png(width, height, render_screen(width, height, current_screen, events)))
