import json
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import buildinfo


class BuildInfoTests(unittest.TestCase):
    def test_repository_version_file_is_the_source_of_truth(self):
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            (repo / "version.json").write_text('{"version": "9.8.7"}', encoding="utf-8")
            app = repo / "alibi"
            app.mkdir()
            self.assertEqual(buildinfo.build_info(app)["version"], "9.8.7")

    def test_installed_copy_reports_its_build_stamp(self):
        with tempfile.TemporaryDirectory() as raw:
            app = Path(raw) / "Alibi" / "app"
            app.mkdir(parents=True)
            (app / "build-info.json").write_text(json.dumps({
                "version": "0.2.0",
                "commit": "abc1234def",
                "dirty": False,
                "built_at": "2026-11-15T09:00:00Z",
            }), encoding="utf-8")
            info = buildinfo.build_info(app)
            self.assertEqual(info["version"], "0.2.0")
            self.assertEqual(info["commit"], "abc1234def")
            self.assertEqual(info["source"], "build")

    def test_installed_copy_without_a_stamp_is_marked_unknown(self):
        with tempfile.TemporaryDirectory() as raw:
            app = Path(raw) / "Alibi" / "app"
            app.mkdir(parents=True)
            info = buildinfo.build_info(app)
            self.assertEqual(info["version"], "0.0.0-dev")
            self.assertEqual(info["source"], "unknown")

    def test_checkout_ignores_a_stale_stamp(self):
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            (repo / ".git").mkdir()
            (repo / "version.json").write_text('{"version": "1.2.3"}', encoding="utf-8")
            app = repo / "alibi"
            app.mkdir()
            (app / "build-info.json").write_text(json.dumps({"version": "0.0.1"}), encoding="utf-8")
            info = buildinfo.build_info(app)
            self.assertEqual(info["version"], "1.2.3")
            self.assertEqual(info["source"], "source")

    def test_invalid_version_file_falls_back(self):
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            (repo / "version.json").write_text("not json", encoding="utf-8")
            app = repo / "alibi"
            app.mkdir()
            self.assertEqual(buildinfo.build_info(app)["version"], "0.0.0-dev")


if __name__ == "__main__":
    unittest.main()
