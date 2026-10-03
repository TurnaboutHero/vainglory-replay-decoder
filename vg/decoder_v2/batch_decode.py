"""Batch decode replays conservatively with decoder_v2."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Dict, List, Optional

from vg.core.replay_output import ReplayOutputError, validate_replay_outputs, write_replay_outputs
from .decode_match import decode_match


def find_replays(base_path: str) -> List[Path]:
    """Find all `.0.vgr` replay files under a directory tree."""
    base = Path(base_path)
    replays = []
    for replay in sorted(base.rglob("*.0.vgr")):
        if "__MACOSX" in replay.parts or replay.name.startswith("._"):
            continue
        replays.append(replay)
    return replays


def decode_replay_batch(base_path: str) -> Dict[str, object]:
    """Decode a replay tree using conservative v2 policy."""
    replays = find_replays(base_path)
    matches = []
    completeness_counter: Dict[str, int] = {}
    accepted_field_counter: Dict[str, int] = {}
    withheld_field_counter: Dict[str, int] = {}

    for replay in replays:
        decoded = decode_match(str(replay))
        payload = decoded.to_dict()
        matches.append(payload)

        completeness_status = payload["completeness_status"]
        completeness_counter[completeness_status] = completeness_counter.get(completeness_status, 0) + 1

        withheld = set(payload["withheld_fields"])
        for key, decision in payload["accepted_fields"].items():
            if (decision.get("accepted_for_index") is True
                    and decision.get("scope", "final") != "capture"
                    and payload.get("scope", "final") != "capture"
                    and key not in withheld):
                accepted_field_counter[key] = accepted_field_counter.get(key, 0) + 1
            else:
                withheld.add(key)
        for key in withheld:
            withheld_field_counter[key] = withheld_field_counter.get(key, 0) + 1

    return {
        "schema_version": "decoder_v2.batch.v2",
        "base_path": str(Path(base_path).resolve()),
        "total_replays": len(replays),
        "completeness_summary": completeness_counter,
        "accepted_field_summary": accepted_field_counter,
        "withheld_field_summary": withheld_field_counter,
        "matches": matches,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Batch decode replays conservatively with decoder_v2.")
    parser.add_argument("base_path", help="Replay root directory")
    parser.add_argument("-o", "--output", help="Optional output JSON path")
    args = parser.parse_args(argv)

    try:
        output_path = Path(args.output) if args.output else None
        replays = find_replays(args.base_path) if output_path is not None else []
        if output_path is not None:
            validate_replay_outputs(replays, output_path)
        report = decode_replay_batch(args.base_path)
        payload = json.dumps(report, indent=2, ensure_ascii=False)
        if output_path is not None:
            validate_replay_outputs(find_replays(args.base_path), output_path)
            write_replay_outputs(replays, output_path, payload)
            print(f"decoder_v2 batch output saved to {output_path}")
        else:
            print(payload)
    except (OSError, ReplayOutputError) as error:
        print(f"batch-decode: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
