import tempfile
import unittest
import os
from pathlib import Path
from unittest.mock import patch

from vg.tools.vgrplay_inject import find_live_temp_replay, inject_replay_with_vgrplay
from vg.core.replay_archive import ArchiveError


class TestVgrplayInject(unittest.TestCase):
    def test_find_live_temp_replay_requires_explicit_group_when_ambiguous(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_frame0 = Path(tmp) / "old.0.vgr"
            old_latest = Path(tmp) / "old.9.vgr"
            new_frame0 = Path(tmp) / "new.0.vgr"
            old_frame0.write_text("a", encoding="utf-8")
            old_latest.write_text("b", encoding="utf-8")
            new_frame0.write_text("c", encoding="utf-8")
            os.utime(old_frame0, (1, 1))
            os.utime(new_frame0, (2, 2))
            os.utime(old_latest, (3, 3))
            with self.assertRaises(ArchiveError):
                find_live_temp_replay(tmp)
            result = find_live_temp_replay(tmp, 'new')
        self.assertTrue(result["latest_file"].endswith("new.0.vgr"))
        self.assertEqual(result["oname"], "new")
        self.assertEqual(result["selected_by"], "explicit_replay_name")

    def test_inject_replay_with_vgrplay_reports_changed_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            temp = root / "temp"
            source.mkdir()
            temp.mkdir()
            (source / "demo-replay.0.vgr").write_bytes(b"source0")
            (source / "demo-replay.1.vgr").write_bytes(b"source1")
            before = temp / "slot.0.vgr"
            before.write_bytes(b"before")

            def fake_run(cmd, capture_output, text, timeout):
                self.assertEqual(cmd, ['C:/tools/vgrplay.exe', '-source', str(source), '-sname',
                                      'demo-replay', '-overwrite', str(temp), '-oname', 'slot'])
                before.write_bytes((source / "demo-replay.0.vgr").read_bytes())
                (temp / "slot.1.vgr").write_bytes((source / "demo-replay.1.vgr").read_bytes())
                return type("Completed", (), {"returncode": 0, "stdout": "ok", "stderr": ""})()

            with patch("vg.tools.vgrplay_inject.subprocess.run", side_effect=fake_run):
                report = inject_replay_with_vgrplay(
                    source_dir=str(source),
                    replay_name="demo-replay",
                    temp_dir=str(temp),
                    vgrplay_path="C:/tools/vgrplay.exe",
                )

        self.assertEqual(report["returncode"], 0)
        self.assertGreaterEqual(report["changed_count"], 1)
        self.assertIn("slot.0.vgr", report["changed_files"])
        self.assertTrue(report["verification"]["ok"])
        self.assertEqual(report["verification"]["source_frame_count"], 2)
        self.assertEqual(report["verification"]["target_frame_count"], 2)


if __name__ == "__main__":
    unittest.main()
