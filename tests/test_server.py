from __future__ import annotations

import json
import os
import struct
import tempfile
import unittest
import zlib
from pathlib import Path


class ToolWorkflowTests(unittest.TestCase):
    @staticmethod
    def _read_png(path: Path) -> tuple[int, int, bytes]:
        data = path.read_bytes()
        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise AssertionError("Not a PNG file")

        offset = 8
        width = height = None
        compressed = bytearray()
        while offset < len(data):
            length = struct.unpack(">I", data[offset : offset + 4])[0]
            chunk_type = data[offset + 4 : offset + 8]
            chunk_data = data[offset + 8 : offset + 8 + length]
            offset += length + 12
            if chunk_type == b"IHDR":
                width, height = struct.unpack(">II", chunk_data[:8])
            elif chunk_type == b"IDAT":
                compressed.extend(chunk_data)
            elif chunk_type == b"IEND":
                break

        if width is None or height is None:
            raise AssertionError("Missing PNG IHDR")

        decoded = zlib.decompress(bytes(compressed))
        row_width = width * 3
        pixels = bytearray()
        pointer = 0
        for _ in range(height):
            filter_type = decoded[pointer]
            pointer += 1
            if filter_type != 0:
                raise AssertionError(f"Unsupported PNG filter: {filter_type}")
            pixels.extend(decoded[pointer : pointer + row_width])
            pointer += row_width
        return width, height, bytes(pixels)

    @staticmethod
    def _pixel_at(pixels: bytes, width: int, x: int, y: int) -> tuple[int, int, int]:
        offset = (y * width + x) * 3
        return tuple(pixels[offset : offset + 3])

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.output_dir = self.root / "output"
        self.image_dir = self.root / "images"
        self.workspace_dir = self.root / "workspace"
        self.config_dir = self.root / "config"
        self.cache_dir = self.root / "cache"
        self.output_dir.mkdir()
        self.image_dir.mkdir()
        self.workspace_dir.mkdir()
        self.config_dir.mkdir()
        self.cache_dir.mkdir()

        os.environ["CYD_OUTPUT_DIR"] = str(self.output_dir)
        os.environ["CYD_IMAGE_DIR"] = str(self.image_dir)
        os.environ["CYD_WORKSPACE"] = str(self.workspace_dir)
        os.environ["CYD_CONFIG_DIR"] = str(self.config_dir)
        os.environ["CYD_CACHE_DIR"] = str(self.cache_dir)

        self.project_dir = self.workspace_dir / "demo_project"
        self.project_dir.mkdir()
        (self.project_dir / "manifest.json").write_text(
            json.dumps(
                {
                    "name": "demo_project",
                    "boot_log": ["Synthetic boot", "UI ready"],
                    "initial_screen": "home",
                }
            ),
            encoding="utf-8",
        )
        (self.image_dir / "demo.bin").write_text(
            json.dumps({"name": "demo.bin", "boot_log": ["Image boot", "UI ready"]}),
            encoding="utf-8",
        )

        import importlib
        import mcp_server.config
        import mcp_server.state
        import mcp_server.tools.build
        import mcp_server.tools.images
        import mcp_server.tools.run
        import mcp_server.tools.screenshot
        import mcp_server.tools.test_runner
        import mcp_server.tools.touch

        self.config = importlib.reload(mcp_server.config)
        importlib.reload(mcp_server.state)
        self.build = importlib.reload(mcp_server.tools.build)
        self.images = importlib.reload(mcp_server.tools.images)
        self.run = importlib.reload(mcp_server.tools.run)
        self.screenshot = importlib.reload(mcp_server.tools.screenshot)
        self.test_runner = importlib.reload(mcp_server.tools.test_runner)
        self.touch = importlib.reload(mcp_server.tools.touch)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_build_and_run_project_create_outputs(self) -> None:
        build_result = self.build.build_project(str(self.project_dir), "cyd_28")
        self.assertTrue(build_result["success"])
        self.assertEqual(len(build_result["output_files"]), 3)

        run_result = self.run.run_project(str(self.project_dir), "cyd_28")
        self.assertTrue(run_result["success"])
        self.assertTrue(self.screenshot.capture_screenshot("baseline")["path"].endswith("baseline.png"))
        self.touch.tap(120, 280)
        screenshot = self.screenshot.capture_screenshot()
        screenshot_path = Path(screenshot["path"])
        self.assertTrue(screenshot_path.exists())
        self.assertGreater(screenshot_path.stat().st_size, 68)

        width, height, pixels = self._read_png(screenshot_path)
        self.assertEqual((width, height), (240, 320))
        self.assertEqual(self._pixel_at(pixels, width, 120, 280), (244, 96, 96))
        self.assertGreater(len(set(pixels[:: 3 * 97])), 3)

    def test_list_images_and_run_test(self) -> None:
        self.assertEqual(self.images.list_images(), ["demo.bin"])
        report = self.test_runner.run_test("sample_touch_test.json")
        self.assertTrue(report["success"])
        self.assertTrue(Path(report["report_path"]).exists())
        screenshot = Path(report["steps_executed"][-1]["path"])
        width, height, pixels = self._read_png(screenshot)
        self.assertEqual((width, height), (240, 320))
        self.assertEqual(self._pixel_at(pixels, width, 120, 280), (244, 96, 96))


if __name__ == "__main__":
    unittest.main()
