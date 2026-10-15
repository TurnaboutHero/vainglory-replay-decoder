import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch


class CooldownProbeTests(unittest.TestCase):
    def test_node_vm_regressions(self):
        repo = Path(__file__).resolve().parents[1]
        node = shutil.which('node')
        self.assertIsNotNone(node, 'Node.js 18+ is required for cooldown observer regression coverage; install it and ensure node is on PATH')
        configured_evidence = os.environ.get('COOLDOWN_PROBE_EVIDENCE_DIR')
        if configured_evidence is None:
            temporary_evidence = tempfile.TemporaryDirectory(prefix='cooldown-probe-')
            self.addCleanup(temporary_evidence.cleanup)
            evidence = Path(temporary_evidence.name).resolve()
        else:
            evidence = Path(configured_evidence).resolve()
        evidence.mkdir(parents=True, exist_ok=True)
        command = [node, str(repo / 'tests/fixtures/cooldown_probe_smoke.cjs'), str(evidence)]
        result = subprocess.run(command, cwd=repo, capture_output=True, text=True, timeout=60)
        (evidence / 'node.stdout.log').write_text(result.stdout)
        (evidence / 'node.stderr.log').write_text(result.stderr or '(empty stderr)\n')
        (evidence / 'python-wrapper.json').write_text(json.dumps({
            'scenario': 'Python wrapper executes the complete Node VM suite',
            'invocation': command, 'observable': 'exit_code == 0 and all scenario assertions pass',
            'exit_code': result.returncode, 'artifact_path': str(evidence / 'smoke-results.json'),
        }, indent=2) + '\n')
        diagnostics = f'{result.stderr}\n{result.stdout}'
        if configured_evidence is not None:
            diagnostics += f'\nEvidence retained: {evidence}'
        self.assertEqual(result.returncode, 0, diagnostics)
        report_path = evidence / 'smoke-results.json'
        self.assertGreater(report_path.stat().st_size, 0)
        report = json.loads(report_path.read_text())
        self.assertEqual(report['failed'], 0)
        self.assertGreaterEqual(report['passed'], 70)
        for scenario in report['results']:
            self.assertTrue(scenario['pass'], scenario['scenario'])
            self.assertTrue(scenario['invocation'])
            self.assertTrue(scenario['observable'])
            self.assertGreater(Path(scenario['artifact_path']).stat().st_size, 0)
        self.assertGreater((evidence / 'sample.json').stat().st_size, 0)
        print(f'Node VM: {report["passed"]} passed')
        if configured_evidence is not None:
            print(f'Evidence retained: {evidence}')


class CooldownProbePortabilityTests(unittest.TestCase):
    def make_archive(self):
        temporary = tempfile.TemporaryDirectory(prefix='cooldown-archive-')
        self.addCleanup(temporary.cleanup)
        archive = Path(temporary.name)
        repo = Path(__file__).resolve().parents[1]
        for relative in ('tests/fixtures/cooldown_probe_smoke.cjs',
                         'vg/tools/player_state_capture/player_state_probe.js',
                         'vg/tools/player_state_capture/cooldown_probe.js'):
            target = archive / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(repo / relative, target)
        return archive

    def run_archive(self, archive):
        node = shutil.which('node')
        self.assertIsNotNone(node, 'Node.js 18+ is required; ensure node is on PATH')
        return subprocess.run(
            [node, str(archive / 'tests/fixtures/cooldown_probe_smoke.cjs'),
             str(archive / 'evidence')], cwd=archive, env={**os.environ, 'PATH': ''},
            capture_output=True, text=True, timeout=60)

    def test_source_archive_without_git_or_history(self):
        archive = self.make_archive()
        self.assertFalse((archive / '.git').exists())
        result = self.run_archive(archive)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads((archive / 'evidence/smoke-results.json').read_text())
        self.assertEqual(report['failed'], 0)
        self.assertGreaterEqual(report['passed'], 70)
        self.assertIsNone(report['repo_head'])
        self.assertIsNone(report['repo_status'])

    def test_archive_rejects_changed_stock_source(self):
        archive = self.make_archive()
        stock = archive / 'vg/tools/player_state_capture/player_state_probe.js'
        stock.write_bytes(stock.read_bytes() + b'\n// unexpected stock edit\n')
        result = self.run_archive(archive)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('differs from the pinned baseline', result.stderr)
        self.assertFalse((archive / 'evidence/smoke-results.json').exists())

    def test_missing_node_is_failure_not_skipped_coverage(self):
        case = CooldownProbeTests('test_node_vm_regressions')
        with patch('shutil.which', return_value=None), patch('subprocess.run') as run:
            result = unittest.TestResult()
            case.run(result)
        self.assertEqual(len(result.failures), 1)
        self.assertIn('Node.js 18+ is required', result.failures[0][1])
        self.assertEqual(result.skipped, [])
        run.assert_not_called()

    def test_default_evidence_cleanup_on_success_and_failure(self):
        real_temporary_directory = tempfile.TemporaryDirectory
        for failed in (False, True):
            with self.subTest(failed=failed):
                directories = []

                def track_temporary_directory(*args, **kwargs):
                    directory = real_temporary_directory(*args, **kwargs)
                    directories.append(Path(directory.name))
                    return directory

                case = CooldownProbeTests('test_node_vm_regressions')
                with patch.dict(os.environ):
                    os.environ.pop('COOLDOWN_PROBE_EVIDENCE_DIR', None)
                    with patch('tempfile.TemporaryDirectory', side_effect=track_temporary_directory):
                        result = unittest.TestResult()
                        if failed:
                            with patch('subprocess.run', return_value=subprocess.CompletedProcess(
                                    [], 1, '', 'injected Node failure')):
                                case.run(result)
                        else:
                            case.run(result)
                self.assertEqual(len(result.failures), int(failed), result.failures)
                self.assertEqual(result.errors, [])
                self.assertEqual(len(directories), 1)
                self.assertFalse(directories[0].exists())

    def test_explicit_evidence_retained_on_success_and_failure(self):
        for failed in (False, True):
            with self.subTest(failed=failed), tempfile.TemporaryDirectory() as directory:
                evidence = Path(directory) / 'retained'
                case = CooldownProbeTests('test_node_vm_regressions')
                with patch.dict(os.environ, {'COOLDOWN_PROBE_EVIDENCE_DIR': str(evidence)}):
                    result = unittest.TestResult()
                    if failed:
                        with patch('subprocess.run', return_value=subprocess.CompletedProcess(
                                [], 1, '', 'injected Node failure')):
                            case.run(result)
                    else:
                        case.run(result)
                self.assertEqual(len(result.failures), int(failed), result.failures)
                self.assertEqual(result.errors, [])
                self.assertTrue(evidence.is_dir())
                receipt = json.loads((evidence / 'python-wrapper.json').read_text())
                self.assertEqual(receipt['exit_code'], int(failed))
                self.assertTrue((evidence / 'node.stdout.log').exists())
                self.assertTrue((evidence / 'node.stderr.log').exists())


if __name__ == '__main__':
    unittest.main()
