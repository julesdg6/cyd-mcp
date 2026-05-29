from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path


class ToolWorkflowTests(unittest.TestCase):
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

        self.config = importlib.reload(mcp_server.config)
        importlib.reload(mcp_server.state)
        self.build = importlib.reload(mcp_server.tools.build)
        self.images = importlib.reload(mcp_server.tools.images)
        self.run = importlib.reload(mcp_server.tools.run)
        self.screenshot = importlib.reload(mcp_server.tools.screenshot)
        self.test_runner = importlib.reload(mcp_server.tools.test_runner)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_build_and_run_project_create_outputs(self) -> None:
        build_result = self.build.build_project(str(self.project_dir), "cyd_28")
        self.assertTrue(build_result["success"])
        self.assertEqual(len(build_result["output_files"]), 3)

        run_result = self.run.run_project(str(self.project_dir), "cyd_28")
        self.assertTrue(run_result["success"])
        screenshot = self.screenshot.capture_screenshot()
        self.assertTrue(Path(screenshot["path"]).exists())

    def test_list_images_and_run_test(self) -> None:
        self.assertEqual(self.images.list_images(), ["demo.bin"])
        report = self.test_runner.run_test("sample_touch_test.json")
        self.assertTrue(report["success"])
        self.assertTrue(Path(report["report_path"]).exists())


if __name__ == "__main__":
    unittest.main()
