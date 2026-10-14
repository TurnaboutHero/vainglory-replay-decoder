import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import unittest


class CooldownProbeTests(unittest.TestCase):
    def test_node_vm_regressions(self):
        repo = Path(__file__).resolve().parents[1]
        node = shutil.which('node')
        self.assertIsNotNone(node, 'Node is required for cooldown observer regression coverage')
        evidence = Path(os.environ.get('COOLDOWN_PROBE_EVIDENCE_DIR',
            str(repo / '.omo' / 'evidence' / f'cooldown-probe-{time.time_ns()}'))).resolve()
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
        self.assertEqual(result.returncode, 0, f'{result.stderr}\n{result.stdout}\nEvidence: {evidence}')
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
        print(f'Node VM: {report["passed"]} passed; evidence: {evidence}')


if __name__ == '__main__':
    unittest.main()
