import sys
import tempfile
import time
import os
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend import settings_store as store  # noqa: E402


class SettingsTests(unittest.TestCase):
    def test_missing_file_returns_defaults(self):
        with tempfile.TemporaryDirectory() as raw:
            self.assertEqual(store.read(raw), store.DEFAULTS)

    def test_patch_is_validated_and_persisted(self):
        with tempfile.TemporaryDirectory() as raw:
            result = store.write(raw, {"default_language": "French", "idle_unload_minutes": 15})
            self.assertEqual(result["default_language"], "French")
            self.assertEqual(store.read(raw)["idle_unload_minutes"], 15)
            self.assertTrue((Path(raw) / store.SETTINGS_FILE).is_file())

    def test_unknown_and_bad_values_are_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            for patch in (
                {"mystery": True},
                {"default_language": "Klingon"},
                {"preload_model": "Huge"},
                {"idle_unload_minutes": -1},
                {"idle_unload_minutes": True},
                {"idle_unload_minutes": 1441},
                {"reduce_motion": "yes"},
            ):
                with self.subTest(patch=patch):
                    with self.assertRaises(ValueError):
                        store.write(raw, patch)
            self.assertEqual(store.read(raw), store.DEFAULTS)

    def test_preload_accepts_empty_and_both_models(self):
        with tempfile.TemporaryDirectory() as raw:
            for value in ("", "Base", "VoiceDesign"):
                self.assertEqual(store.write(raw, {"preload_model": value})["preload_model"], value)

    def test_corrupt_file_falls_back_instead_of_crashing(self):
        with tempfile.TemporaryDirectory() as raw:
            (Path(raw) / store.SETTINGS_FILE).write_text("{not json", encoding="utf-8")
            self.assertEqual(store.read(raw), store.DEFAULTS)

    def test_invalid_stored_value_falls_back_per_key(self):
        with tempfile.TemporaryDirectory() as raw:
            (Path(raw) / store.SETTINGS_FILE).write_text(
                '{"default_language": "Korean", "reduce_motion": 3}', encoding="utf-8")
            values = store.read(raw)
            self.assertEqual(values["default_language"], "Korean")
            self.assertFalse(values["reduce_motion"])

    def test_reset_removes_the_file(self):
        with tempfile.TemporaryDirectory() as raw:
            store.write(raw, {"compact_sidebar": True})
            self.assertEqual(store.reset(raw), store.DEFAULTS)
            self.assertFalse((Path(raw) / store.SETTINGS_FILE).exists())


class StorageTests(unittest.TestCase):
    def test_directory_size_sums_files(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "a").mkdir()
            (root / "a" / "one.bin").write_bytes(b"x" * 10)
            (root / "two.bin").write_bytes(b"y" * 5)
            self.assertEqual(store.directory_size(root), 15)

    def test_storage_report_counts_exports_and_recordings(self):
        with tempfile.TemporaryDirectory() as raw:
            data = Path(raw) / "data"
            models = Path(raw) / "models"
            for folder in ("audio", "originals", "exports"):
                (data / folder).mkdir(parents=True)
            (models / "Model").mkdir(parents=True)
            (data / "audio" / "a.wav").write_bytes(b"a" * 100)
            (data / "exports" / "e.wav").write_bytes(b"e" * 40)
            (data / "exports" / "e.json").write_text("{}", encoding="utf-8")
            (models / "Model" / "config.json").write_text("{}", encoding="utf-8")
            report = store.storage_report(data, models)
            self.assertEqual(report["recordings"], 100)
            self.assertEqual(report["exports"], 42)  # wav plus its metadata file
            self.assertEqual(report["exports_count"], 1)
            self.assertEqual(report["models"], 2)

    def test_cleanup_removes_only_old_exports(self):
        with tempfile.TemporaryDirectory() as raw:
            exports = Path(raw) / "exports"
            exports.mkdir()
            old = time.time() - 40 * 86400
            for name, age in (("old", old), ("new", time.time())):
                audio = exports / (name + ".wav")
                audio.write_bytes(b"z" * 20)
                meta = exports / (name + ".json")
                meta.write_text("{}", encoding="utf-8")
                for path in (audio, meta):
                    os.utime(path, (age, age))
            result = store.cleanup_exports(raw, 30)
            self.assertEqual(result["removed"], 1)
            self.assertEqual(result["freed"], 22)  # 20 bytes of wav plus 2 of metadata
            self.assertTrue((exports / "new.wav").exists())
            self.assertFalse((exports / "old.wav").exists())
            self.assertFalse((exports / "old.json").exists())

    def test_cleanup_days_must_be_sane(self):
        with tempfile.TemporaryDirectory() as raw:
            for days in (0, -5, 4000, True):
                with self.subTest(days=days):
                    with self.assertRaises(ValueError):
                        store.cleanup_exports(raw, days)


class IdleTests(unittest.TestCase):
    def test_should_unload_respects_the_setting(self):
        now = 10_000.0
        self.assertFalse(store.should_unload(now, now - 3600, 0))
        self.assertFalse(store.should_unload(now, now - 60, 15))
        self.assertTrue(store.should_unload(now, now - 16 * 60, 15))
        self.assertFalse(store.should_unload(now, None, 15))


class LogTests(unittest.TestCase):
    def test_tail_returns_the_last_lines(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "service.log"
            path.write_text("\n".join(f"line {i}" for i in range(500)), encoding="utf-8")
            text = store.tail(path, lines=3)
            self.assertEqual(text.splitlines(), ["line 497", "line 498", "line 499"])

    def test_tail_of_a_missing_file_is_empty(self):
        with tempfile.TemporaryDirectory() as raw:
            self.assertEqual(store.tail(Path(raw) / "missing.log"), "")


if __name__ == "__main__":
    unittest.main()
