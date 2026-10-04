from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path

from .evidence import export_reference, import_capture, publish, read_json, verify_capture
from .guards import CaptureError, require


def challenge(capture_dir, mutation):
    baseline = verify_capture(capture_dir)
    require(baseline['ok'], 'challenge_precondition', 'A valid observation capture is required before mutation')
    changed = deepcopy(read_json(Path(capture_dir) / 'capture.json'))
    if mutation == 'native-hash':
        ref = next(r for r in changed['artifacts'] if r['artifact_id'] == changed['native_artifact_id'])
        ref['sha256'] = '0' * 64
    elif mutation == 'foreign-pid':
        changed['process']['pid'] += 1
    elif mutation == 'missing-screenshot':
        changed['artifacts'] = [r for r in changed['artifacts'] if r['role'] != 'screenshot']
    else:
        raise CaptureError('unsupported_challenge', 'Unknown in-memory evidence challenge')
    result = verify_capture(capture_dir, capture_override=changed)
    return {'ok': not result['ok'], 'mutation': mutation, 'original_capture_unchanged': True,
            'baseline_status': baseline['status'], 'rejection': result['errors']}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Verify and import independent owned-client evidence; bounded Windows passive capture')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('verify')
    p.add_argument('--capture-dir', type=Path, required=True)
    p.add_argument('--require-restored', action='store_true')
    p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('import')
    p.add_argument('--spec', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p = sub.add_parser('export-reference')
    p.add_argument('--capture-dir', type=Path, required=True)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--query-clock', choices=('game_time', 'record_time'), default='game_time')
    p = sub.add_parser('align')
    p.add_argument('--capture-dir', type=Path, required=True)
    p.add_argument('--sample-sequence', type=int, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p = sub.add_parser('capture')
    p.add_argument('--profile', type=Path, required=True)
    p.add_argument('--spec', type=Path, required=True)
    p.add_argument('--seconds', type=int, default=3)
    p.add_argument('--output-dir', type=Path, required=True)
    p = sub.add_parser('restore')
    p.add_argument('--profile', type=Path, required=True)
    p.add_argument('--trial', required=True)
    p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('challenge')
    p.add_argument('--capture-dir', type=Path, required=True)
    p.add_argument('--mutation', choices=['native-hash', 'foreign-pid', 'missing-screenshot'], required=True)
    p.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'verify':
            result = verify_capture(args.capture_dir, args.require_restored)
            publish(args.output, result, [args.capture_dir / 'capture.json'])
        elif args.command == 'import':
            result = import_capture(args.spec, args.output_dir)
        elif args.command == 'export-reference':
            result = export_reference(args.capture_dir, args.manifest, args.output_dir, query_clock=args.query_clock)
        elif args.command == 'align':
            from .alignment import align_capture
            result = align_capture(args.capture_dir, args.output_dir, args.sample_sequence)
        elif args.command == 'challenge':
            result = challenge(args.capture_dir, args.mutation)
            publish(args.output, result, [args.capture_dir / 'capture.json'])
        else:
            from .runner import capture, restore
            result = (capture(args.profile, args.spec, args.output_dir, args.seconds)
                      if args.command == 'capture' else restore(args.profile, args.trial, args.output))
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0 if result['ok'] else 1
    except (CaptureError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'ok': False, 'errors': [{'code': getattr(exc, 'code', 'invocation_error'), 'message': str(exc)}]}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
