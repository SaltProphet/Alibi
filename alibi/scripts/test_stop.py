import json
import sys
from pathlib import Path
import tempfile
from unittest import mock
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import stop  # noqa: E402


class StopTests(unittest.TestCase):
    def test_stale_processes_do_not_crash_the_stop_script(self):
        with tempfile.TemporaryDirectory() as raw:
            pid_file = Path(raw) / "alibi-processes.json"
            pid_file.write_text(json.dumps([
                {"name": "inference", "pid": 40001, "port": 8766},
                {"name": "backend", "pid": 40002, "port": 8765},
            ]), encoding="utf-8")
            with mock.patch.object(stop, "PID_FILE", pid_file), \
                 mock.patch.object(stop, "terminate") as terminate:
                stop.main()
            self.assertEqual(terminate.call_count, 2)
            self.assertFalse(pid_file.exists())

    def test_missing_pid_file_is_reported_not_raised(self):
        with tempfile.TemporaryDirectory() as raw:
            with mock.patch.object(stop, "PID_FILE", Path(raw) / "missing.json"):
                stop.main()


if __name__ == "__main__":
    unittest.main()
