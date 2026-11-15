import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import launch  # noqa: E402


class PortSelectionTests(unittest.TestCase):
    def setUp(self):
        self.original = launch.port_available
        self.original_health = launch.health

    def tearDown(self):
        launch.port_available = self.original
        launch.health = self.original_health

    def test_prefers_the_requested_port_when_free(self):
        launch.port_available = lambda port: True
        self.assertEqual(launch.pick_port(8765), 8765)

    def test_skips_blocked_and_occupied_ports(self):
        launch.port_available = lambda port: port not in (8765, 8767)
        self.assertEqual(launch.pick_port(8765, {8766}), 8768)

    def test_reports_when_no_port_is_free(self):
        launch.port_available = lambda port: False
        with self.assertRaises(SystemExit):
            launch.pick_port(8765)

    def test_finds_an_already_running_instance_off_the_default_port(self):
        launch.health = lambda port, timeout=2: {"build": {"version": "0.3.1"}} if port == 8771 else None
        self.assertEqual(launch.running_alibi(), 8771)

    def test_a_foreign_service_on_the_default_port_is_not_alibi(self):
        launch.health = lambda port, timeout=2: {"status": "ready"} if port == 8765 else None
        self.assertIsNone(launch.running_alibi())


if __name__ == "__main__":
    unittest.main()
