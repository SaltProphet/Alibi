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

    def test_python_install_command_quotes_target_and_uses_per_user_mode(self):
        command = setup.python_install_command(Path(r"C:\Users\Ada Smith\AppData\Local\Alibi\runtime"), Path("python-installer.exe"))
        self.assertIn("InstallAllUsers=0", command)
        self.assertIn('TargetDir="C:\\Users\\Ada Smith\\AppData\\Local\\Alibi\\runtime"', command)


if __name__ == "__main__":
    unittest.main()
