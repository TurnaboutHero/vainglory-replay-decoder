import contextlib
from dataclasses import dataclass
import hashlib
import io
import json
import os
from pathlib import Path
from types import ModuleType
import unittest
from unittest.mock import patch


@dataclass(frozen=True, slots=True)
class ReportCase:
    module: ModuleType
    builder: str
    args: tuple[str, ...]
    sources: tuple[Path, ...]
    replays: tuple[Path, ...]
    output: Path


@dataclass(frozen=True, slots=True)
class CommandResult:
    code: int
    stdout: str
    stderr: str


def run_report(case: ReportCase, output: Path | None = None) -> CommandResult:
    stdout, stderr = io.StringIO(), io.StringIO()
    args = [*case.args, *(['--output', str(output)] if output is not None else [])]
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = case.module.main(args)
    return CommandResult(code, stdout.getvalue(), stderr.getvalue())


def hashes(paths: tuple[Path, ...]) -> dict[str, str]:
    return {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def write_replay(folder: Path, name: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    block = bytearray(0xE2)
    block[:3] = b'\xda\x03\xee'
    block[3:12] = b'PlayerOne'
    block[0xA5:0xA7] = (57093).to_bytes(2, 'little')
    block[0xA9:0xAB] = (0xB801).to_bytes(2, 'little')
    block[0xD5] = 1
    replay = folder / f'{name}.0.vgr'
    replay.write_bytes(bytes(block))
    (folder / f'{name}.1.vgr').write_bytes(bytes(block))
    return replay


def assert_report_happy(test: unittest.TestCase, case: ReportCase) -> None:
    before = hashes(case.sources)
    result = run_report(case, case.output)
    test.assertEqual(result.code, 0, result.stderr)
    test.assertTrue(json.loads(case.output.read_text(encoding='utf-8')) is not None)
    with patch('vg.core.replay_output.stage_payload') as stage:
        stdout_result = run_report(case)
    stage.assert_not_called()
    test.assertEqual(stdout_result.code, 0, stdout_result.stderr)
    test.assertTrue(json.loads(stdout_result.stdout) is not None)
    test.assertEqual(hashes(case.sources), before)
    print(json.dumps({'module': case.module.__name__, 'scenario': 'happy',
                      'source_hashes_before': before, 'source_hashes_after': hashes(case.sources)}))


def assert_report_failures(test: unittest.TestCase, case: ReportCase) -> None:
    before = hashes(case.sources)
    builder_path = f'{case.module.__name__}.{case.builder}'
    for source in case.sources:
        for kind in ('direct', 'hardlink', 'symlink'):
            output = source if kind == 'direct' else case.output.with_name(f'alias-{kind}.json')
            if kind == 'hardlink':
                os.link(source, output)
            if kind == 'symlink':
                output.symlink_to(source)
            try:
                with test.subTest(module=case.module.__name__, source=str(source), alias=kind), patch(builder_path) as builder:
                    result = run_report(case, output)
                    test.assertEqual(result.code, 2, result)
                    test.assertTrue(result.stderr)
                    test.assertEqual(result.stdout, '')
                    builder.assert_not_called()
                    test.assertEqual(hashes(case.sources), before)
            finally:
                if kind != 'direct':
                    output.unlink()
    for replay in case.replays:
        output = replay.with_name(replay.name[:-len('.0.vgr')] + '.999.vgr')
        with test.subTest(module=case.module.__name__, future=str(output)), patch(builder_path) as builder:
            test.assertEqual(run_report(case, output).code, 2)
            builder.assert_not_called()
            test.assertFalse(output.exists())
    for fault in ('serialization', 'stage', 'replace', 'late_alias'):
        case.output.write_bytes(b'prior output')

        def late_alias(*args, **kwargs):
            case.output.unlink()
            case.output.symlink_to(case.sources[0])
            return {'ok': True}

        with test.subTest(module=case.module.__name__, fault=fault), contextlib.ExitStack() as stack:
            if fault == 'late_alias':
                stack.enter_context(patch(builder_path, side_effect=late_alias))
            else:
                stack.enter_context(patch(builder_path, return_value={'invalid': {1}} if fault == 'serialization' else {'ok': True}))
            if fault in ('stage', 'replace'):
                target = 'vg.core.replay_output.stage_payload' if fault == 'stage' else 'os.replace'
                stack.enter_context(patch(target, side_effect=OSError('injected publication failure')))
            result = run_report(case, case.output)
            test.assertEqual(result.code, 2, result)
            test.assertEqual(result.stdout, '')
            test.assertTrue(result.stderr)
            test.assertEqual(hashes(case.sources), before)
            if fault == 'late_alias':
                case.output.unlink()
            else:
                test.assertEqual(case.output.read_bytes(), b'prior output')
        test.assertEqual(list(case.output.parent.glob(f'.{case.output.name}.*.tmp')), [])
    print(json.dumps({'module': case.module.__name__, 'scenario': 'failure',
                      'aliases_checked': len(case.sources) * 3, 'future_families': len(case.replays),
                      'faults': ['serialization', 'stage', 'replace', 'late_alias'],
                      'source_hashes_before': before, 'source_hashes_after': hashes(case.sources)}))
