import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

from tests.test_product_duration_provenance import replay_bytes
from vg.core.replay_input import ReplayInputError
from vg.core.stat_evidence import frame_scope


ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / 'vg/docs/PRODUCT_RELIABILITY.md'
MATRIX = ROOT / 'vg/docs/decoder_v2/README.md'


def make_fixture(destination: Path) -> None:
    if destination.exists() and any(destination.iterdir()):
        raise ReplayInputError('output_not_empty', destination, 'Use a new or empty disposable directory')
    for folder in ('replays', 'reports', 'slot', 'mixed', 'ambiguous', 'empty'):
        (destination / folder).mkdir(parents=True, exist_ok=True)
    data = replay_bytes(crystal=120, death=110)
    replay = destination / 'replays/demo.0.vgr'
    replay.write_bytes(data)
    (destination / 'slot/slot.0.vgr').write_bytes(b'disposable original slot')
    for filename in ('mixed/good.0.vgr', 'ambiguous/one.0.vgr', 'ambiguous/two.0.vgr'):
        (destination / filename).write_bytes(data)
    (destination / 'mixed/broken.0.vgr').write_bytes(b'synthetic malformed input')
    truth = {'matches': [{'replay_name': 'demo', 'replay_file': str(replay.absolute()),
              'match_info': {'duration_seconds': 0}, 'players': {'PlayerOne': {
                  'team': 'left', 'hero_name': 'Unknown', 'kills': 6, 'deaths': 2,
                  'assists': 3, 'minion_kills': 100}}}]}
    (destination / 'truth.json').write_text(json.dumps(truth, indent=2), encoding='utf-8')
    image = destination / 'synthetic-screen.png'
    image.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jCfoAAAAASUVORK5CYII='))
    observation = {'schema_version': 'vg.final-screen-observation.v1',
        'replay_scope': frame_scope([(0, data)]),
        'screenshot_sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
        'capture_stage': 'final_screen', 'provenance': {'transcription_method': 'manual_visual',
            'observed_at_utc': '2026-10-04T00:00:00Z', 'fixture_kind': 'synthetic_not_observed_game'},
        'screen_side_to_team': {'blue': 'left', 'orange': 'right'},
        'winner_screen_side': None, 'duration_display': '0:00', 'players': [
            {'entity_id_be': 7, 'screen_side': 'blue', 'kills': 6, 'deaths': 2,
             'assists': 3, 'cs': 100, 'gold_display': '0.0k'}]}
    (destination / 'observation.json').write_text(json.dumps(observation, indent=2), encoding='utf-8')


def documented_commands(marker: str) -> list[list[str]]:
    sections = re.findall(r'<!-- ' + marker + r':start -->(.*?)<!-- ' + marker + r':end -->',
                          GUIDE.read_text(encoding='utf-8'), re.DOTALL)
    return [shlex.split(line) for section in sections for line in section.splitlines() if line.startswith('python ')]


class ProductQuickstartTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='vg quickstart ')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name) / 'fixture with spaces'
        self.commands = []
        self.addCleanup(self.record_evidence)

    def record_evidence(self):
        evidence = os.environ.get('VG_QUICKSTART_EVIDENCE')
        if evidence:
            target = Path(evidence) / self._testMethodName
            target.mkdir(parents=True, exist_ok=True)
            (target / 'commands.json').write_text(json.dumps(self.commands, indent=2), encoding='utf-8')
            if self.base.exists():
                shutil.copytree(self.base, target / 'fixture', dirs_exist_ok=True)

    def run_command(self, args, expected=0):
        command = [sys.executable, *[str(arg).replace('.quickstart', str(self.base)) for arg in args[1:]]]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=60)
        self.commands.append({'argv': command, 'exit_code': result.returncode,
                              'stdout': result.stdout, 'stderr': result.stderr})
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def source_hashes(self):
        paths = [*self.base.glob('*.json'), *self.base.glob('*.png'),
                 *(p for folder in ('replays', 'mixed', 'ambiguous') for p in (self.base / folder).glob('*.vgr'))]
        return {str(p.relative_to(self.base)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

    def payload(self, name):
        return json.loads((self.base / 'reports' / name).read_text(encoding='utf-8'))

    def test_quickstart_happy_documented_offline_commands(self):
        # Given the executable quickstart commands, including its fixture generator.
        commands = documented_commands('offline-commands')
        self.assertGreater(len(commands), 20)
        self.run_command(commands[0])
        before = self.source_hashes()
        # When every remaining documented command runs in order on disposable paths.
        for command in commands[1:]:
            self.run_command(command)
        # Then real schemas, evidence scope, catalogs and archives match the contract.
        safe, capture = self.payload('safe.json'), self.payload('capture.json')
        self.assertEqual(safe['schema_version'], 'decoder_v2.match.v2')
        for field in ('kills', 'deaths', 'assists', 'minion_kills', 'gold', 'winner', 'duration_seconds'):
            self.assertFalse(safe['withheld_fields'][field]['accepted_for_index'])
            self.assertFalse(self.payload('index.json')['matches'][0]['withheld_fields'][field]['accepted_for_index'])
        self.assertEqual(capture['schema_version'], 'decoder_v2.capture.v2')
        self.assertEqual(capture['players'][0]['kills'], 6)
        self.assertEqual((capture['at_game_time'], capture['as_of_game_time']), (105, 105))
        self.assertFalse(capture['accepted_fields']['kills']['accepted_for_index'])
        self.assertEqual(self.payload('debug.json')['schema_version'], 'decoder_v2.debug_match.v2')
        for name in ('batch.json', 'index.json', 'parsed-batch.json'):
            self.assertEqual(self.payload(name)['status'], 'complete')
        self.assertEqual(self.payload('catalog.json')['coverage'], 'catalog_only')
        self.assertEqual(self.payload('legacy.json')['duration_provenance']['status'], 'supplied_truth')
        self.assertEqual(self.payload('statistics.json')['match_stats']['avg_duration_s'], 0)
        self.assertEqual(self.payload('csv-batch/export_receipt.json')['status'], 'complete')
        comparison = self.payload('comparison.json')
        self.assertEqual(comparison['comparison_status'], 'matched')
        self.assertEqual(comparison['compared_fields'], 4)
        self.assertEqual(comparison['compared_field_names'], ['kills', 'deaths', 'assists', 'minion_kills'])
        self.assertEqual(comparison['observation_only_fields'], ['gold', 'winner', 'duration', 'result'])
        self.assertFalse(comparison['accepted_for_index'])
        self.assertTrue(list((self.base / 'backups').rglob('snapshot.json')))
        self.assertEqual((self.base / 'slot/slot.0.vgr').read_bytes(), (self.base / 'replays/demo.0.vgr').read_bytes())
        self.assertEqual(self.source_hashes(), before)
        self.commands.append({'source_hashes_before': before, 'source_hashes_after': self.source_hashes()})

    def test_quickstart_happy_documented_python_api(self):
        # Given the exact Python API block from the guide and generated fixtures.
        make_fixture(self.base)
        before = self.source_hashes()
        section = re.search(r'<!-- offline-api:start -->(.*?)<!-- offline-api:end -->',
                            GUIDE.read_text(encoding='utf-8'), re.DOTALL)[1]
        code = re.search(r'```python\n(.*?)```', section, re.DOTALL)[1]
        code = code.replace('Path(".quickstart")', f'Path({str(self.base)!r})')
        # When the documented code executes in a fresh interpreter.
        self.run_command(['python', '-B', '-c', code])
        # Then the assertions pass without changing any input bytes.
        self.assertEqual(self.source_hashes(), before)

    def test_quickstart_happy_all_forty_module_help(self):
        # Given the machine-executable module and option names in the capability table.
        rows = re.findall(r'^\| `(vg\.decoder_v2\.\w+)` \|[^\n]+$', MATRIX.read_text(encoding='utf-8'), re.MULTILINE)
        self.assertEqual(len(rows), 40)
        self.assertEqual(len(set(rows)), 40)
        # When every documented module is imported through its actual CLI help.
        for module in rows:
            result = self.run_command(['python', '-B', '-m', module, '--help'])
            line = next(line for line in MATRIX.read_text(encoding='utf-8').splitlines() if f'`{module}`' in line)
            # Then every advertised option is accepted and output remains available.
            for flag in re.findall(r'`(--[a-z-]+)`', line):
                self.assertIn(flag, result.stdout)
            self.assertIn('--output', result.stdout)

    def test_quickstart_failure_documented_outcomes(self):
        # Given the guide's malformed, ambiguous, partial, empty and unavailable examples.
        make_fixture(self.base)
        before = self.source_hashes()
        commands = documented_commands('offline-errors')
        self.assertEqual(len(commands), 5)
        # When those commands execute with their documented exit expectations.
        for command, expected in zip(commands, (2, 2, 1, 0, 0), strict=True):
            result = self.run_command(command, expected)
            self.assertNotIn('Traceback (most recent call last)', result.stderr)
        # Then unavailable fields stay null and partial/empty batches stay explicit.
        partial = self.payload('partial.json')
        self.assertEqual((partial['discovered'], partial['succeeded'], partial['failed']), (2, 1, 1))
        self.assertEqual(self.payload('empty.json')['status'], 'empty')
        unavailable = self.payload('unavailable.json')
        self.assertIsNone(unavailable['players'][0]['kills'])
        self.assertTrue(unavailable['withheld_fields']['kills']['reason'])
        for field in ('winner', 'gold', 'duration_seconds'):
            self.assertIsNone(unavailable['withheld_fields'][field]['value'])
            self.assertFalse(unavailable['withheld_fields'][field]['accepted_for_index'])
        self.assertEqual(self.source_hashes(), before)
        self.run_command(['python', '-B', '-m', 'tests.test_product_quickstart', '--make-fixture', '.quickstart'], 2)
        self.assertEqual(self.source_hashes(), before)

    def test_quickstart_failure_documented_archive_recovery(self):
        # Given an interrupted synthetic slot operation with verified original backups.
        make_fixture(self.base)
        (self.base / 'replays/demo.1.vgr').write_bytes(replay_bytes())
        original = (self.base / 'slot/slot.0.vgr').read_bytes()
        code = '''from pathlib import Path
from unittest.mock import patch
from vg.core import replay_archive as archive
from vg.core.vgr_loader import VGRLoader
import json
real = archive.os.replace
def fail(source, target):
    if (Path(source).parent.name == 'stage' and Path(target).name == 'slot.1.vgr') or Path(source).name.startswith('restore-'):
        raise OSError('synthetic interruption')
    return real(source, target)
with patch.object(archive.os, 'replace', side_effect=fail):
    result = VGRLoader(str(BASE / 'slot')).load_replay(str(BASE / 'replays'), 'demo', 'slot')
assert result['error_code'] == 'recovery_required', result
print(json.dumps(result))
'''.replace('BASE', f'Path({str(self.base)!r})')
        setup = self.run_command(['python', '-B', '-c', code])
        operation = json.loads(setup.stdout)['recovery']
        # When the documented recovery command runs after the owner process exits.
        self.run_command(['python', '-B', '-m', 'vg.core.vgr_loader', 'recover', operation])
        # Then the original slot is restored and the introduced section is removed.
        self.assertEqual((self.base / 'slot/slot.0.vgr').read_bytes(), original)
        self.assertFalse((self.base / 'slot/slot.1.vgr').exists())

    def test_quickstart_failure_documented_report_recovery(self):
        # Given a multi-file export whose replacement and rollback both fail.
        make_fixture(self.base)
        code = '''from pathlib import Path
from unittest.mock import patch
import os
from vg.core.export_matches import decode_batch_report
from vg.core.replay_output import ReplayOutputError
base = BASE
out = base / 'reports/recovery'
decode_batch_report(str(base / 'replays'), output_dir=str(out))
real = os.replace
calls = 0
def fail(source, target):
    global calls
    calls += 1
    if calls in (3, 4): raise OSError('synthetic interruption')
    return real(source, target)
try:
    with patch('vg.core.report_transaction.os.replace', side_effect=fail):
        decode_batch_report(str(base / 'replays'), output_dir=str(out))
except ReplayOutputError as error:
    assert error.code == 'recovery_required', error
else:
    raise AssertionError('Expected pending report receipt')
'''.replace('BASE', f'Path({str(self.base)!r})')
        self.run_command(['python', '-B', '-c', code])
        receipt = self.base / 'reports/recovery/export_receipt.json'
        self.assertEqual(json.loads(receipt.read_text())['status'], 'pending')
        # When the documented explicit recovery API is called.
        self.run_command(['python', '-B', '-c',
            f'from pathlib import Path\nfrom vg.core.replay_output import recover_report_set\nrecover_report_set(Path({str(receipt)!r}))'])
        # Then the complete prior receipt and its hashes are restored.
        restored = json.loads(receipt.read_text())
        self.assertEqual(restored['status'], 'complete')
        for entry in restored['entries']:
            self.assertEqual(hashlib.sha256(Path(entry['path']).read_bytes()).hexdigest(), entry['new_hash'])


if __name__ == '__main__':
    if '--make-fixture' in sys.argv:
        parser = argparse.ArgumentParser(description='Generate a disposable synthetic offline quickstart fixture')
        parser.add_argument('--make-fixture', type=Path, required=True)
        args = parser.parse_args()
        try:
            make_fixture(args.make_fixture)
        except (OSError, ValueError) as error:
            parser.error(str(error))
        print(args.make_fixture)
    else:
        unittest.main()
