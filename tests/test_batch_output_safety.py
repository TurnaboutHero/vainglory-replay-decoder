"""Batch and index output paths must preserve all consumed inputs."""
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from vg.decoder_v2 import batch_decode, index_export

COMMANDS = (
    (batch_decode.main, 'vg.decoder_v2.batch_decode.decode_replay_batch'),
    (index_export.main, 'vg.decoder_v2.index_export.build_index_ready_export'),
)


class BatchOutputSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.replays = self.root / 'replays'
        self.first = self.replays / 'first'
        self.second = self.replays / 'second'
        self.first.mkdir(parents=True)
        self.second.mkdir()
        self.inputs = []
        for directory in (self.first, self.second):
            for number in (0, 1):
                source = directory / f'match.{number}.vgr'
                source.write_bytes(f'original section {directory.name}/{number}'.encode())
                self.inputs.append(source)

    def assert_rejected(self, output: Path) -> None:
        before = [p.read_bytes() for p in self.inputs]
        for entry, dependency in COMMANDS:
            with self.subTest(command=entry.__module__), patch(dependency, return_value={}) as decode:
                with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                    code = entry([str(self.replays), '-o', str(output)])
                self.assertEqual(code, 2)
                decode.assert_not_called()
                self.assertEqual([p.read_bytes() for p in self.inputs], before)

    def test_sections_from_every_replay_family_are_protected(self) -> None:
        for source in self.inputs:
            with self.subTest(source=source):
                self.assert_rejected(source)

    def test_hardlink_to_second_family_is_protected(self) -> None:
        output = self.root / 'report.json'
        os.link(self.inputs[-1], output)
        self.assert_rejected(output)

    def test_symlink_to_second_family_is_protected(self) -> None:
        output = self.root / 'report.json'
        output.symlink_to(self.inputs[-1])
        self.assert_rejected(output)

    def test_future_sibling_cannot_pollute_a_replay(self) -> None:
        output = self.second / 'match.999.vgr'
        self.assert_rejected(output)
        self.assertFalse(output.exists())

    def test_dangling_symlink_to_future_sibling_is_protected(self) -> None:
        output = self.root / 'report.json'
        output.symlink_to(self.second / 'match.999.vgr')
        self.assert_rejected(output)
        self.assertTrue(output.is_symlink())
        self.assertFalse(output.exists())

    def test_symlinked_parent_is_protected(self) -> None:
        alias = self.root / 'alias'
        alias.symlink_to(self.second, target_is_directory=True)
        self.assert_rejected(alias / 'match.1.vgr')

    def test_regular_output_replaces_prior_report_without_touching_inputs(self) -> None:
        before = [p.read_bytes() for p in self.inputs]
        output = self.root / 'report.json'
        for entry, dependency in COMMANDS:
            output.write_text('old report', encoding='utf-8')
            with self.subTest(command=entry.__module__), patch(dependency, return_value={'matches': []}):
                with contextlib.redirect_stdout(io.StringIO()):
                    code = entry([str(self.replays), '-o', str(output)])
                self.assertEqual(code, 0)
                self.assertEqual(json.loads(output.read_text()), {'matches': []})
                self.assertEqual([p.read_bytes() for p in self.inputs], before)

    def test_publication_failure_preserves_prior_report_and_cleans_temporary(self) -> None:
        output = self.root / 'report.json'
        output.write_text('old report', encoding='utf-8')
        for entry, dependency in COMMANDS:
            with self.subTest(command=entry.__module__), patch(dependency, return_value={}):
                with patch('os.replace', side_effect=OSError('publication failed')):
                    with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                        code = entry([str(self.replays), '-o', str(output)])
                self.assertEqual(code, 2)
                self.assertEqual(output.read_text(), 'old report')
                self.assertEqual(list(self.root.glob('.report.json.*.tmp')), [])

    def test_decode_failure_preserves_existing_output(self) -> None:
        output = self.root / 'report.json'
        output.write_text('old report', encoding='utf-8')
        for entry, dependency in COMMANDS:
            with self.subTest(command=entry.__module__), patch(dependency, side_effect=OSError('input missing')):
                with contextlib.redirect_stderr(io.StringIO()):
                    code = entry([str(self.replays), '-o', str(output)])
                self.assertEqual(code, 2)
                self.assertEqual(output.read_text(), 'old report')

    def test_output_alias_created_during_decode_is_rejected(self) -> None:
        output = self.root / 'report.json'
        before = self.inputs[-1].read_bytes()

        def create_alias(*_args: str, **_kwargs: str) -> dict[str, int]:
            output.symlink_to(self.inputs[-1])
            return {}

        for entry, dependency in COMMANDS:
            with self.subTest(command=entry.__module__), patch(dependency, side_effect=create_alias):
                with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                    code = entry([str(self.replays), '-o', str(output)])
                self.assertEqual(code, 2)
                self.assertEqual(self.inputs[-1].read_bytes(), before)
                output.unlink()

    def test_empty_tree_still_allows_output(self) -> None:
        empty = self.root / 'empty'
        empty.mkdir()
        output = self.root / 'report.json'
        for entry, _dependency in COMMANDS:
            with self.subTest(command=entry.__module__), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(entry([str(empty), '-o', str(output)]), 0)
                self.assertEqual(json.loads(output.read_text())['total_replays'], 0)

    def test_index_correction_files_and_aliases_are_protected(self) -> None:
        directory = self.root / 'corrections'
        directory.mkdir()
        correction = directory / 'rows.json'
        correction.write_text('{"players": []}', encoding='utf-8')
        hardlink = self.root / 'hardlink.json'
        os.link(correction, hardlink)
        symlink = self.root / 'symlink.json'
        symlink.symlink_to(correction)
        for source in (correction, directory):
            for output in (correction, hardlink, symlink):
                with self.subTest(source=source, output=output), patch(COMMANDS[1][1], return_value={}) as decode:
                    with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                        code = index_export.main([str(self.replays), '--kda-correction-path', str(source),
                                                  '-o', str(output)])
                    self.assertEqual(code, 2)
                    decode.assert_not_called()
                    self.assertEqual(correction.read_text(), '{"players": []}')


if __name__ == '__main__':
    unittest.main()
