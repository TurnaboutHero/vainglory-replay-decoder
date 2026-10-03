"""Export metadata while withholding unvalidated final match statistics."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sys
from typing import Dict, Final, List, Optional, assert_never, override

from vg.core.replay_output import (
    ReplayOutputError, validate_output_sources, validate_replay_outputs, write_replay_outputs,
)
from vg.core.stat_evidence import FINAL_VALIDATION_STATUS, final_field_reason
from .batch_decode import decode_replay_batch, find_replays
from .minion_policy import MINION_POLICY_CHOICES, MINION_POLICY_NONE, evaluate_minion_policy
from .models import FieldDecision

type JSONValue = None | bool | int | float | str | list[JSONValue] | dict[str, JSONValue]
FINAL_FIELDS: Final = ("kills", "deaths", "assists", "gold", "minion_kills", "winner")
CORRECTION_NAMES: Final = frozenset((
    "result_screen_kda_correction_merge.json", "target_replay_corrected_kda_rows.json",
))


@dataclass(frozen=True, slots=True)
class CorrectionInputError(ValueError):
    path: Path
    reason: str

    @override
    def __str__(self) -> str:
        return f"{self.path}: {self.reason}"


@dataclass(frozen=True, slots=True)
class CorrectionSummary:
    path: str | None
    status: str
    reason: str | None
    withheld_documents: int = 0
    withheld_rows: int = 0
    ignored_noncorrection_documents: int = 0
    corrected_matches: int = 0
    corrected_rows: int = 0


def _correction_rows(path: Path, payload: JSONValue, required: bool) -> int | None:
    """Parse correction document shape without trusting its declared provenance."""
    match payload:
        case dict() as document:
            if "players" not in document and not required:
                return None
            players = document.get("players")
        case None | bool() | int() | float() | str() | list():
            raise CorrectionInputError(path, "correction document must be a JSON object")
        case unreachable:
            assert_never(unreachable)
    match players:
        case list() as rows:
            for row in rows:
                match row:
                    case dict():
                        continue
                    case None | bool() | int() | float() | str() | list():
                        raise CorrectionInputError(path, "each correction player must be an object")
                    case unreachable:
                        assert_never(unreachable)
            return len(rows)
        case None | bool() | int() | float() | str() | dict():
            raise CorrectionInputError(path, "correction players must be a JSON array")
        case unreachable:
            assert_never(unreachable)


def _correction_paths(kda_correction_path: str | None) -> tuple[Path, ...]:
    """Enumerate exactly the correction files consumed by this export."""
    if not kda_correction_path:
        return ()
    path = Path(kda_correction_path)
    return tuple(sorted(path.rglob("*.json"))) if path.is_dir() else (path,)


def _load_corrections(kda_correction_path: str | None) -> CorrectionSummary:
    """Read supplied files, surface errors, and count corrections held at the boundary."""
    if not kda_correction_path:
        return CorrectionSummary(None, "not_requested", None)
    path = Path(kda_correction_path)
    directory = path.is_dir()
    candidates = _correction_paths(kda_correction_path)
    documents = rows = ignored = 0
    for candidate in candidates:
        payload: JSONValue = json.loads(candidate.read_text(encoding="utf-8"))
        count = _correction_rows(candidate, payload, not directory or candidate.name in CORRECTION_NAMES)
        if count is None:
            ignored += 1
        else:
            documents += 1
            rows += count
    return CorrectionSummary(
        str(path.resolve()), "withheld", final_field_reason("result-screen KDA correction"),
        documents, rows, ignored,
    )


def build_index_ready_export(
    base_path: str,
    minion_policy: str = MINION_POLICY_NONE,
    *,
    kda_correction_path: Optional[str] = None,
) -> Dict[str, object]:
    """Preserve metadata; current code has no source-bound final-stat validator.

    Legacy flags, capture observations, name-bound corrections and experimental
    minion policies cannot authorize a final field, independently of each other.
    """
    corrections = _load_corrections(kda_correction_path)
    batch = decode_replay_batch(base_path)
    matches = []
    for match in batch["matches"]:
        decisions = {
            name: FieldDecision(None, "unknown", False, f"{name}.final_validation",
                                final_field_reason(name), FINAL_VALIDATION_STATUS, "final").to_dict()
            for name in FINAL_FIELDS
        }
        candidate_allowed, candidate_reason = evaluate_minion_policy(
            minion_policy, match["replay_file"], match["completeness_status"],
        )
        players = []
        for player in match["players"]:
            row = {
                key: player.get(key)
                for key in ("name", "team", "entity_id", "hero_name", "entity_id_be",
                            "replay_scope", "identity_reason")
            }
            row["identity_status"] = player.get("identity_status", "unverified")
            row["withheld_fields"] = {key: decisions[key] for key in FINAL_FIELDS if key != "winner"}
            row["minion_policy"] = {
                "policy": minion_policy, "accepted": False,
                "reason": final_field_reason("minion_kills"),
            }
            players.append(row)
        matches.append({
            key: match[key] for key in ("replay_name", "replay_file", "game_mode", "map_name",
                                       "team_size", "completeness_status")
        } | {
            "replay_scope": match.get("replay_scope"),
            "source_scope": match.get("scope", "final"),
            "withheld_fields": decisions,
            "minion_policy": {
                "policy": minion_policy, "accepted_match": False, "accepted_player_count": 0,
                "reason": final_field_reason("minion_kills"),
                "candidate_match_eligible": candidate_allowed, "candidate_reason": candidate_reason,
                "player_candidate_status": "not_joined_without_scoped_identity_and_final_validation",
            },
            "players": players,
            "kda_source_summary": {
                "parser_rows": 0, "result_screen_rows": 0, "unresolved_rows": len(players),
            },
            "kda_correction": {
                "applied": False, "status": corrections.status, "reason": corrections.reason,
                "corrected_rows": 0,
            },
        })
    return {
        "schema_version": "decoder_v2.index_export.v3",
        "base_path": str(Path(base_path).resolve()),
        "minion_policy": minion_policy,
        "minion_policy_summary": {
            "policy": minion_policy, "accepted_matches": 0, "withheld_matches": len(matches),
        },
        "kda_correction_summary": asdict(corrections),
        "total_replays": batch["total_replays"],
        "completeness_summary": batch["completeness_summary"],
        "matches": matches,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Export index-safe fields from decoder_v2.")
    parser.add_argument("base_path", help="Replay root directory")
    parser.add_argument(
        "--minion-policy",
        choices=MINION_POLICY_CHOICES,
        default=MINION_POLICY_NONE,
        help="Optional conservative minion export policy",
    )
    parser.add_argument(
        "--kda-correction-path",
        help="Inspect legacy correction JSON files; final KDA remains withheld",
    )
    parser.add_argument("-o", "--output", help="Optional output path")
    args = parser.parse_args(argv)

    try:
        output_path = Path(args.output) if args.output else None
        replays = find_replays(args.base_path) if output_path is not None else []
        corrections = _correction_paths(args.kda_correction_path) if output_path is not None else ()
        if output_path is not None:
            validate_replay_outputs(replays, output_path)
            validate_output_sources(corrections, output_path)
        report = build_index_ready_export(
            args.base_path,
            minion_policy=args.minion_policy,
            kda_correction_path=args.kda_correction_path,
        )
        payload = json.dumps(report, indent=2, ensure_ascii=False)
        if output_path is not None:
            validate_replay_outputs(find_replays(args.base_path), output_path)
            validate_output_sources((*corrections, *_correction_paths(args.kda_correction_path)), output_path)
            write_replay_outputs(replays, output_path, payload)
            print(f"Index-safe export saved to {output_path}")
        else:
            print(payload)
    except (OSError, UnicodeError, json.JSONDecodeError, CorrectionInputError, ReplayOutputError) as error:
        print(f"index-export: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
