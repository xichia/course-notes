import json
import io
import os
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch

from build_manifest import build_manifest, main as manifest_main
from build_review_queue import build_queue, main as review_main, resolve_generation_date
from studylib import GenerationDateError, ROOT, generation_date


class GenerationDateTests(unittest.TestCase):
    def test_source_date_epoch_controls_review_queue_date(self):
        with patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1704067200"}, clear=True):
            self.assertEqual(date(2024, 1, 1), resolve_generation_date())

    def test_explicit_today_has_highest_precedence(self):
        with patch.dict(
            os.environ,
            {"SOURCE_DATE_EPOCH": "invalid", "DATE": "also-invalid"},
            clear=True,
        ):
            self.assertEqual(date(2024, 3, 3), resolve_generation_date("2024-03-03"))

    def test_date_environment_override_remains_supported(self):
        with patch.dict(
            os.environ,
            {"SOURCE_DATE_EPOCH": "invalid", "DATE": "2024-02-02"},
            clear=True,
        ):
            self.assertEqual(date(2024, 2, 2), resolve_generation_date())

    def test_invalid_source_date_epoch_values_are_rejected(self):
        for value in ("not-a-number", "-1", "9" * 100):
            with self.subTest(value=value):
                with patch.dict(os.environ, {"SOURCE_DATE_EPOCH": value}, clear=True):
                    with self.assertRaisesRegex(GenerationDateError, "SOURCE_DATE_EPOCH"):
                        generation_date()

    def test_valid_epoch_uses_utc_at_date_boundary(self):
        with patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1704067199"}, clear=True):
            self.assertEqual(date(2023, 12, 31), generation_date())

    def test_invalid_epoch_cli_failures_preserve_or_omit_outputs(self):
        commands = (("manifest", manifest_main), ("review queue", review_main))
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            for label, command in commands:
                with self.subTest(command=label, output="existing"):
                    output = Path(temp_dir) / f"{label.replace(' ', '-')}.out"
                    output.write_bytes(b"original output\n")
                    stderr = io.StringIO()
                    with patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "invalid"}, clear=True):
                        with patch("sys.stderr", stderr):
                            self.assertNotEqual(0, command(["--output", str(output)]))
                    self.assertEqual(b"original output\n", output.read_bytes())
                    self.assertIn("SOURCE_DATE_EPOCH", stderr.getvalue())

                with self.subTest(command=label, output="absent"):
                    output.unlink()
                    stderr = io.StringIO()
                    with patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "invalid"}, clear=True):
                        with patch("sys.stderr", stderr):
                            self.assertNotEqual(0, command(["--output", str(output)]))
                    self.assertFalse(output.exists())
                    self.assertIn("SOURCE_DATE_EPOCH", stderr.getvalue())

    def test_deterministic_regeneration_reproduces_public_generated_files(self):
        generated_on = json.loads(ROOT.joinpath("manifest.json").read_text(encoding="utf-8"))["generated-at"]
        epoch = str(int(datetime.fromisoformat(generated_on).replace(tzinfo=timezone.utc).timestamp()))
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            temp_root = Path(temp_dir)
            manifest = temp_root / "manifest.json"
            queue = temp_root / "REVIEW_QUEUE.md"
            with patch.dict(os.environ, {"SOURCE_DATE_EPOCH": epoch}, clear=True):
                self.assertEqual(0, build_manifest(manifest))
                self.assertEqual(0, build_queue(queue, generation_date()))

            self.assertEqual(ROOT.joinpath("manifest.json").read_bytes(), manifest.read_bytes())
            self.assertEqual(ROOT.joinpath("REVIEW_QUEUE.md").read_bytes(), queue.read_bytes())


if __name__ == "__main__":
    unittest.main()
