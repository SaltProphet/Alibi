import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("line_please_setup", ROOT / "installer" / "setup.py")
setup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(setup)


class SetupPlanningTests(unittest.TestCase):
    def test_install_directory_is_per_user(self):
        self.assertEqual(setup.install_directory("C:/Users/Ada/AppData/Local"), Path("C:/Users/Ada/AppData/Local/Alibi"))

    def test_model_download_policy(self):
        self.assertEqual(setup.model_repos(voice_design=False), ["Qwen/Qwen3-TTS-12Hz-1.7B-Base", "Qwen/Qwen3-TTS-Tokenizer-12Hz"])
        self.assertIn("Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign", setup.model_repos(voice_design=True))

    def test_free_space_requirement_changes_for_voice_design(self):
        self.assertLess(setup.minimum_free_bytes(False), setup.minimum_free_bytes(True))

    def test_installer_window_keeps_primary_action_visible(self):
        self.assertEqual(setup.window_geometry(), "760x620")
        self.assertLessEqual(setup.log_height(), 10)

    def test_alibi_visual_system_is_defined(self):
        self.assertEqual(setup.COLORS["ink"], "#171310")
        self.assertEqual(setup.COLORS["cream"], "#f1e8d2")
        self.assertEqual(setup.COLORS["orange"], "#e75b2c")
        self.assertEqual(setup.visual_tagline(), "Runs locally. No account required.")

    def test_python_runtime_uses_state_free_nuget_package(self):
        self.assertIn("nuget.org/api/v2/package/python/3.12.10", setup.PYTHON_RUNTIME_URL)

    def test_shortcut_targets_always_include_start_menu_and_optionally_desktop(self):
        start_menu = Path("C:/Start Menu")
        desktop = Path("C:/Desktop")
        self.assertEqual(setup.shortcut_targets(True, start_menu, desktop), [start_menu / "Alibi.lnk", desktop / "Alibi.lnk"])
        self.assertEqual(setup.shortcut_targets(False, start_menu, desktop), [start_menu / "Alibi.lnk"])


if __name__ == "__main__":
    unittest.main()
