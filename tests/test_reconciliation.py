"""Regression checks for behavior retained while reconciling the source trees."""

import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile


ROOT = Path(__file__).resolve().parents[1]
RECONSTRUCTION = ROOT / "reconstruction_pipeline"
sys.path.insert(0, str(RECONSTRUCTION))

import run_pipeline
import step3_splat


class ReconstructionTests(unittest.TestCase):
    def test_defaults_follow_checkout(self):
        self.assertEqual(Path(run_pipeline.DEFAULT_FRAMES), ROOT / "vision_pipeline/data/edited_frames")
        self.assertEqual(Path(run_pipeline.DEFAULT_OUTPUT), RECONSTRUCTION / "output")
        self.assertEqual(Path(run_pipeline.DEFAULT_COLMAP_WS), RECONSTRUCTION / "colmap_workspace")

    def test_opensplat_environment_override_wins(self):
        with patch.dict(os.environ, {"OPENSPLAT_BIN": "/custom/opensplat"}):
            self.assertEqual(step3_splat.find_opensplat(), "/custom/opensplat")

    def test_opensplat_reads_setup_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root / "custom-opensplat"
            binary.touch()
            (root / ".pipeline_config").write_text(f"OPENSPLAT_BIN={binary}\n")
            with patch.dict(os.environ, {}, clear=True), patch.object(
                step3_splat, "__file__", str(root / "step3_splat.py")
            ):
                self.assertEqual(step3_splat.find_opensplat(), str(binary))

    def test_opensplat_falls_back_to_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.dict(os.environ, {}, clear=True), patch.object(
                step3_splat, "__file__", str(root / "step3_splat.py")
            ), patch.object(step3_splat.Path, "home", return_value=root), patch.object(
                step3_splat.shutil, "which", return_value="/tools/opensplat"
            ):
                self.assertEqual(step3_splat.find_opensplat(), "/tools/opensplat")

    def test_missing_opensplat_returns_failure_without_launching(self):
        with patch.object(step3_splat, "OPENSPLAT_BIN", None), patch.object(
            step3_splat.subprocess, "run"
        ) as launch, patch("sys.stdout", new=io.StringIO()):
            result = step3_splat.train_splat("unused", "unused")
        self.assertFalse(result["success"])
        launch.assert_not_called()

    def test_test_mode_uses_separate_outputs_and_workspace(self):
        with patch.object(sys, "argv", ["run_pipeline.py", "--test"]), patch.object(
            run_pipeline, "download_test_dataset", return_value="/tmp/banana/images"
        ), patch.object(run_pipeline.os.path, "isdir", return_value=True), patch.object(
            run_pipeline, "run"
        ) as run:
            run_pipeline.main()
        args = run.call_args.args[0]
        self.assertEqual(args.frames, "/tmp/banana/images")
        self.assertEqual(Path(args.output), RECONSTRUCTION / "test_output")
        self.assertEqual(Path(args.workspace), RECONSTRUCTION / "test_workspace")

    def test_dataset_archive_cannot_escape_destination(self):
        def malicious_download(url, destination):
            with zipfile.ZipFile(destination, "w") as archive:
                archive.writestr("../escaped.txt", "unexpected")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(run_pipeline.urllib.request, "urlretrieve", side_effect=malicious_download):
                with self.assertRaisesRegex(ValueError, "Unsafe dataset archive path"):
                    run_pipeline.download_test_dataset(str(root / "dataset"))
            self.assertFalse((root / "escaped.txt").exists())

    def test_dataset_extracts_images(self):
        def download(url, destination):
            with zipfile.ZipFile(destination, "w") as archive:
                archive.writestr("banana/images/frame.jpg", b"fixture")

        with tempfile.TemporaryDirectory() as directory:
            with patch.object(run_pipeline.urllib.request, "urlretrieve", side_effect=download):
                images = Path(run_pipeline.download_test_dataset(directory))
            self.assertEqual(images, Path(directory) / "banana/images")
            self.assertTrue((images / "frame.jpg").is_file())


if __name__ == "__main__":
    unittest.main()
