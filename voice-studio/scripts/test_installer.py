import importlib.util
import platform
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("voice_studio_installer", ROOT / "install.py")
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class InstallerPlanningTests(unittest.TestCase):
    def test_requirements_without_torch_preserves_local_qwen_dependency(self):
        requirements = "torch==2.8.0+cu128\ntorchaudio==2.8.0+cu128\n-e ./vendor/Qwen3-TTS\nfastapi==1.0\n"
        result = installer.requirements_without_torch(requirements)
        self.assertNotIn("torch==", result)
        self.assertNotIn("torchaudio==", result)
        self.assertIn("-e ./vendor/Qwen3-TTS", result)
        self.assertIn("fastapi==1.0", result)

    def test_torch_index_uses_cpu_when_cuda_is_unavailable(self):
        self.assertEqual(installer.torch_install_args(cuda=False), ["--index-url", installer.CPU_TORCH_INDEX])

    def test_torch_index_uses_cuda_wheels_when_cuda_is_available(self):
        self.assertEqual(installer.torch_install_args(cuda=True), ["--index-url", installer.CUDA_TORCH_INDEX])

    def test_platform_summary_is_safe_to_show_to_users(self):
        summary = installer.platform_summary(cuda=False)
        self.assertIn(platform.system(), summary)
        self.assertIn("CPU", summary)
        self.assertNotIn(str(Path.home()), summary)

    def test_bundled_install_does_not_require_build_tools(self):
        self.assertEqual(installer.required_commands(bundled=True), ["ffmpeg"])

    def test_bundled_install_skips_frontend_build(self):
        self.assertFalse(installer.should_build_frontend(bundled=True))


if __name__ == "__main__":
    unittest.main()
