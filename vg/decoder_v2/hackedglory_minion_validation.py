"""Summarize HackedGlory-style minion source-target-reward evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from vg.core.replay_output import validate_report_outputs, write_report_output
from .report_inputs import prepare_truth_inputs, truth_replay_files

from .minion_policy import (
    MINION_POLICY_NONFINALS_BASELINE_0E,
    MINION_POLICY_NONFINALS_OR_LOW_MIXED_RATIO_EXPERIMENTAL,
)
from .minion_policy_cross_validation import build_minion_policy_cross_validation
from .minion_policy_validation import validate_minion_policy
from .minion_window_fixture_research import build_minion_window_fixture_report


def _validation_summary(report: Dict[str, object]) -> Dict[str, object]:
    accepted_error_rows = [
        row
        for row in report.get("rows", [])
        if isinstance(row, dict) and row.get("accepted") and row.get("error") != 0
    ]
    return {
        "policy": report.get("policy"),
        "player_rows": report.get("player_rows"),
        "accepted_rows": report.get("accepted_rows"),
        "accepted_exact": report.get("accepted_exact"),
        "accepted_error": report.get("accepted_error"),
        "precision": report.get("precision"),
        "coverage": report.get("coverage"),
        "accepted_error_rows": accepted_error_rows[:10],
    }


def _window_summary(report: Dict[str, object]) -> Dict[str, object]:
    positive_matches = [
        row
        for row in report.get("per_match", [])
        if isinstance(row, dict) and int(row.get("positive_residual_players") or 0) > 0
    ]
    return {
        "complete_fixture_matches": report.get("complete_fixture_matches"),
        "global_positive_target_samples": report.get("global_positive_target_samples"),
        "global_nonpositive_target_samples": report.get("global_nonpositive_target_samples"),
        "positive_residual_match_count": len(positive_matches),
        "positive_residual_matches": positive_matches,
        "top_enriched_headers": report.get("global_enriched_headers", [])[:8],
        "top_enriched_credit_patterns": report.get("global_enriched_credit_patterns", [])[:12],
    }


def _fixed_policy_summary(cross_validation: Dict[str, object]) -> List[Dict[str, object]]:
    rows = cross_validation.get("fixed_policy_reference", [])
    return [row for row in rows if isinstance(row, dict)]


def _assessment(
    nonfinals: Dict[str, object],
    experimental: Dict[str, object],
    cross_validation: Dict[str, object],
    window: Dict[str, object],
) -> Dict[str, object]:
    nonfinals_safe = (
        float(nonfinals.get("precision") or 0.0) == 1.0
        and int(nonfinals.get("accepted_error") or 0) == 0
        and int(nonfinals.get("accepted_rows") or 0) > 0
    )
    experimental_error = int(experimental.get("accepted_error") or 0) > 0
    loso = cross_validation.get("leave_one_series_out", {})
    loso_summary = loso.get("summary", loso) if isinstance(loso, dict) else {}
    failed_series_folds = int(loso_summary.get("failed_folds") or 0)
    positive_match_count = int(window.get("positive_residual_match_count") or 0)

    if nonfinals_safe:
        product_policy = MINION_POLICY_NONFINALS_BASELINE_0E
    else:
        product_policy = "none"

    return {
        "product_safe_policy": product_policy,
        "default_policy_should_remain": "none",
        "experimental_policy_safe_for_default": not experimental_error and failed_series_folds == 0,
        "source_target_reward_status": "context_only",
        "reasons": [
            (
                "non-Finals baseline 0x0E has 100% precision on current complete truth rows"
                if nonfinals_safe
                else "non-Finals baseline 0x0E is not yet safe on current truth rows"
            ),
            (
                "low-mixed-ratio experimental gate has at least one accepted error"
                if experimental_error
                else "low-mixed-ratio experimental gate has no accepted error in direct validation"
            ),
            (
                "cross-validation still has failed folds, so metric gates look overfit-prone"
                if failed_series_folds
                else "cross-validation did not show failed series folds"
            ),
            (
                f"positive residual source-target-reward windows are concentrated in {positive_match_count} match(es)"
            ),
        ],
    }


def build_hackedglory_minion_validation(
    truth_path: str,
    *,
    byte_window: int = 96,
) -> Dict[str, object]:
    """Build a compact decision report for HackedGlory-inspired minion research."""
    nonfinals_validation = validate_minion_policy(truth_path, MINION_POLICY_NONFINALS_BASELINE_0E)
    experimental_validation = validate_minion_policy(
        truth_path,
        MINION_POLICY_NONFINALS_OR_LOW_MIXED_RATIO_EXPERIMENTAL,
    )
    cross_validation = build_minion_policy_cross_validation(truth_path)
    window_report = build_minion_window_fixture_report(truth_path, byte_window=byte_window)

    nonfinals_summary = _validation_summary(nonfinals_validation)
    experimental_summary = _validation_summary(experimental_validation)
    cv_summary = {
        "row_count": cross_validation.get("row_count"),
        "series_count": cross_validation.get("series_count"),
        "replay_count": cross_validation.get("replay_count"),
        "fixed_policy_reference": _fixed_policy_summary(cross_validation),
        "leave_one_series_out": cross_validation.get("leave_one_series_out", {}).get("summary", {}),
        "leave_one_replay_out": cross_validation.get("leave_one_replay_out", {}).get("summary", {}),
    }
    window_summary = _window_summary(window_report)

    return {
        "schema_version": "decoder_v2.hackedglory_minion_validation.v1",
        "truth_path": str(Path(truth_path).resolve()),
        "hackedglory_reference": (
            "HackedGlory models CS as source-target minion interactions followed by reward pulses. "
            "This report checks whether local .vgr baseline 0x0E counts and nearby reward/context windows "
            "are safe enough to export."
        ),
        "options": {"byte_window": byte_window},
        "assessment": _assessment(
            nonfinals_summary,
            experimental_summary,
            cv_summary,
            window_summary,
        ),
        "policy_validation": {
            MINION_POLICY_NONFINALS_BASELINE_0E: nonfinals_summary,
            MINION_POLICY_NONFINALS_OR_LOW_MIXED_RATIO_EXPERIMENTAL: experimental_summary,
        },
        "cross_validation": cv_summary,
        "source_target_reward_window": window_summary,
    }


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Summarize HackedGlory-inspired minion source-target-reward validation."
    )
    parser.add_argument("--truth", default="vg/output/tournament_truth.json", help="Truth JSON path")
    parser.add_argument("--byte-window", type=int, default=96, help="Byte radius around minion target events")
    parser.add_argument("-o", "--output", help="Optional output JSON path")
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        documents = prepare_truth_inputs(args.truth)
        validate_report_outputs(documents.inputs, [args.output] if args.output else [])
        selected = [row for row in documents.matches if "Incomplete" not in Path(row.get("replay_file", "")).parent.name]
        replays = truth_replay_files(selected, args.truth)
        prepared = prepare_truth_inputs(args.truth, replays)
        documents.inputs.recheck()
        validate_report_outputs(prepared.inputs, [args.output] if args.output else [])
        report = build_hackedglory_minion_validation(args.truth, byte_window=args.byte_window)
        payload = json.dumps(report, indent=2, ensure_ascii=False)
        if args.output:
            output_path = Path(args.output)
            write_report_output(prepared.inputs, output_path, payload)
            print(f"HackedGlory minion validation saved to {output_path}")
        else:
            prepared.inputs.recheck()
            print(payload)
    except (OSError, ValueError, TypeError) as exc:
        print(f"hackedglory_minion_validation: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
