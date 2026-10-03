import builtins
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from vg.tools.windows_window_capture import capture_window_by_process_name, normalize_window_rect


class TestProductCoreEnvironment(unittest.TestCase):
    def test_core_environment_happy(self) -> None:
        script = """
import builtins
import pathlib
import sys
import unittest
real_import = builtins.__import__
def without_pillow(name, *args, **kwargs):
    if name == 'PIL' or name.startswith('PIL.'):
        raise ImportError('Pillow deliberately unavailable')
    return real_import(name, *args, **kwargs)
builtins.__import__ = without_pillow
from vg.tools.windows_window_capture import build_window_capture_metadata
assert build_window_capture_metadata('game.exe', 'unused.png', (1, 2, 11, 22))['rect']['width'] == 10
sys.path.insert(0, str(pathlib.Path('tests').resolve()))
from test_decoder_v2_validation import TestDecoderV2Validation
result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(TestDecoderV2Validation))
assert result.testsRun == 2 and result.wasSuccessful()
"""
        result = subprocess.run([sys.executable, "-B", "-c", script], cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Ran 2 tests", result.stderr)

    def test_core_environment_failure(self) -> None:
        real_import = builtins.__import__

        def without_pillow(name: str, *args, **kwargs):
            if name == "PIL" or name.startswith("PIL."):
                raise ImportError("Pillow deliberately unavailable")
            return real_import(name, *args, **kwargs)

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "capture.png"
            with patch("vg.tools.windows_window_capture.sys.platform", "darwin"):
                with self.assertRaisesRegex(RuntimeError, "requires Windows"):
                    capture_window_by_process_name("game.exe", str(output))
            with patch("vg.tools.windows_window_capture.sys.platform", "win32"), patch("builtins.__import__", side_effect=without_pillow):
                with self.assertRaisesRegex(RuntimeError, "optional Pillow package"):
                    capture_window_by_process_name("game.exe", str(output))
            self.assertFalse(output.exists())
            self.assertEqual(list(Path(temp_dir).iterdir()), [])
        with self.assertRaises(ValueError):
            normalize_window_rect(1, 2, 1, 3)


if __name__ == "__main__":
    unittest.main()
