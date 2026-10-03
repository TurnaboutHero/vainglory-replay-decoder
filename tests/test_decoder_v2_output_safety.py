"""Output-path safety at the match CLI boundary; only disposable inputs are used."""
import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from vg.decoder_v2.decode_match import main


class MatchOutputSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.replay = self.root / "match.0.vgr"
        self.sibling = self.root / "match.1.vgr"
        self.replay.write_bytes(b"private replay metadata")
        self.sibling.write_bytes(b"private replay section")

    def assert_rejected(self, output: Path, replay: Path | None = None) -> None:
        before = (self.replay.read_bytes(), self.sibling.read_bytes())
        with patch("vg.decoder_v2.decode_match.decode_match") as safe, \
             patch("vg.decoder_v2.decode_match.decode_match_debug", return_value={}) as debug:
            safe.return_value.to_dict.return_value = {}
            for format_name in ("safe-json", "debug-json"):
                with self.subTest(format=format_name), contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as caught:
                        main([str(replay or self.replay), "--format", format_name,
                              "--at-game-time", "100", "-o", str(output)])
                    self.assertEqual(caught.exception.code, 2)
            safe.assert_not_called()
            debug.assert_not_called()
        self.assertEqual((self.replay.read_bytes(), self.sibling.read_bytes()), before)

    def test_direct_input_and_sibling_are_protected(self) -> None:
        for output in (self.replay, self.sibling):
            with self.subTest(output=output.name):
                self.assert_rejected(output)

    def test_hardlink_alias_is_protected(self) -> None:
        output = self.root / "report.json"
        os.link(self.sibling, output)
        self.assert_rejected(output)

    def test_symlink_alias_is_protected(self) -> None:
        output = self.root / "report.json"
        output.symlink_to(self.sibling)
        self.assert_rejected(output)

    def test_new_siblings_cannot_contaminate_replay_discovery(self) -> None:
        for name in ("match.2.vgr", "match.invalid.vgr"):
            output = self.root / name
            with self.subTest(name=name):
                self.assert_rejected(output)
                self.assertFalse(output.exists())

    def test_dangling_symlink_to_future_sibling_is_protected(self) -> None:
        output = self.root / "report.json"
        output.symlink_to(self.root / "match.2.vgr")
        self.assert_rejected(output)
        self.assertTrue(output.is_symlink())
        self.assertFalse(output.exists())

    def test_symlinked_parent_is_protected(self) -> None:
        directory = self.root / "alias"
        directory.symlink_to(self.root, target_is_directory=True)
        self.assert_rejected(directory / self.sibling.name)

    def test_input_symlink_keeps_lexical_sibling_discovery(self) -> None:
        source = self.root / "source"
        source.mkdir()
        metadata = source / "original.0.vgr"
        metadata.write_bytes(b"original metadata")
        self.replay.unlink()
        self.replay.symlink_to(metadata)
        self.assert_rejected(self.sibling)
        self.assertEqual(metadata.read_bytes(), b"original metadata")

    def test_input_glob_metacharacters_still_protect_discovered_frames(self) -> None:
        replay = self.root / "[m]atch.0.vgr"
        replay.write_bytes(b"metadata with glob metacharacters")
        self.assert_rejected(self.sibling, replay)

    def test_regular_json_output_is_allowed(self) -> None:
        output = self.root / "report.json"
        output.write_text("old result", encoding="utf-8")
        with patch("vg.decoder_v2.decode_match.decode_match_debug", return_value={"scope": "capture"}), \
             contextlib.redirect_stdout(io.StringIO()):
            code = main([str(self.replay), "--format", "debug-json", "-o", str(output)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.read_text(encoding="utf-8")), {"scope": "capture"})
        self.assertEqual(self.replay.read_bytes(), b"private replay metadata")

    def test_decode_failure_preserves_existing_output(self) -> None:
        output = self.root / "report.json"
        output.write_text("old result", encoding="utf-8")
        with patch("vg.decoder_v2.decode_match.decode_match_debug", side_effect=ValueError("malformed input")):
            with self.assertRaisesRegex(ValueError, "malformed input"):
                main([str(self.replay), "--format", "debug-json", "-o", str(output)])
        self.assertEqual(output.read_text(encoding="utf-8"), "old result")

    def test_failed_publication_preserves_existing_output(self) -> None:
        output = self.root / "report.json"
        output.write_text("old result", encoding="utf-8")
        with patch("vg.decoder_v2.decode_match.decode_match_debug", return_value={}), \
             patch("os.replace", side_effect=OSError("publication failed")), \
             contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                main([str(self.replay), "--format", "debug-json", "-o", str(output)])
        self.assertEqual(caught.exception.code, 2)
        self.assertEqual(output.read_text(encoding="utf-8"), "old result")
        self.assertEqual(list(self.root.glob(".report.json.*.tmp")), [])

    def test_output_alias_created_during_decode_is_rejected(self) -> None:
        output = self.root / "report.json"

        def create_alias(_replay: str, *, at_game_time: float | None = None) -> dict[str, str]:
            output.symlink_to(self.sibling)
            return {"scope": "capture"}

        with patch("vg.decoder_v2.decode_match.decode_match_debug", side_effect=create_alias), \
             contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                main([str(self.replay), "--format", "debug-json", "-o", str(output)])
        self.assertEqual(caught.exception.code, 2)
        self.assertEqual(self.sibling.read_bytes(), b"private replay section")


if __name__ == "__main__":
    unittest.main()
