"""Inject a source replay into the live temp replay slot using vgrplay."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, TypedDict

from vg.core.replay_archive import ArchiveError, replacement, select_family
from vg.core.replay_input import ReplayInputError
from vg.core.replay_output import ReportInputs, ReplayOutputError, validate_report_outputs, validate_replay_output, write_report_output


DEFAULT_VGRPLAY = (
    r"D:\Desktop\My Folder\Game\VG\vg replay\vaingloryreplay-master\windows_amd64\vgrplay.exe"
)


class FrameSummary(TypedDict):
    frame_count: int
    min_frame: int | None
    max_frame: int | None
    frame0_path: str | None
    frame0_mtime: float | None
    latest_file: str | None
    latest_mtime: float | None


class LiveReplay(FrameSummary):
    oname: str
    selected_by: str
    candidate_count: int


class Verification(TypedDict):
    source_frame_count: int
    target_frame_count: int
    source_min_frame: int | None
    source_max_frame: int | None
    target_min_frame: int | None
    target_max_frame: int | None
    missing_target_frames: list[int]
    extra_target_frames: list[int]
    size_mismatch_count: int
    size_mismatches: list[dict[str, int]]
    hash_mismatch_count: int
    hash_mismatches: list[dict[str, str | int]]
    verified_frame_count: int
    ok: bool


class InjectionReport(TypedDict):
    captured_at: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    source_dir: str
    replay_name: str
    temp_dir: str
    live_replay: LiveReplay
    target_after: FrameSummary
    changed_files: list[str]
    changed_count: int
    verification: Verification
    source_scope: str
    recovery: str
    success_scope: str


def _replay_name_from_vgr(path: Path) -> Optional[str]:
    if path.suffix != ".vgr":
        return None
    stem = path.stem
    name, dot, frame = stem.rpartition(".")
    if not dot or not frame.isdigit():
        return None
    return name


def _frame_index(path: Path) -> Optional[int]:
    if path.suffix != ".vgr":
        return None
    frame = path.stem.rsplit(".", 1)[-1]
    return int(frame) if frame.isdigit() else None


def _group_replay_frames(directory: Path) -> Dict[str, Dict[int, Path]]:
    groups: Dict[str, Dict[int, Path]] = {}
    for path in directory.glob("*.vgr"):
        name = _replay_name_from_vgr(path)
        frame = _frame_index(path)
        if name is None or frame is None:
            continue
        groups.setdefault(name, {})[frame] = path
    return groups


def _frame_summary(frames: Dict[int, Path]) -> FrameSummary:
    latest = max(frames.values(), key=lambda item: item.stat().st_mtime) if frames else None
    frame0 = frames.get(0)
    return {
        "frame_count": len(frames),
        "min_frame": min(frames) if frames else None,
        "max_frame": max(frames) if frames else None,
        "frame0_path": str(frame0.resolve()) if frame0 else None,
        "frame0_mtime": frame0.stat().st_mtime if frame0 else None,
        "latest_file": str(latest.resolve()) if latest else None,
        "latest_mtime": latest.stat().st_mtime if latest else None,
    }


def find_live_temp_replay(temp_dir: str, replay_name: Optional[str] = None) -> LiveReplay:
    selected_path = select_family(Path(temp_dir), replay_name, recursive=False)
    oname = selected_path.name[:-6]
    groups = _group_replay_frames(Path(temp_dir))
    return {**_frame_summary(groups[oname]), "oname": oname,
            "selected_by": "explicit_replay_name" if replay_name else "only_replay",
            "candidate_count": len(groups)}


def _build_frame_inventory(directory: Path, replay_name: str) -> Dict[int, Path]:
    return _group_replay_frames(directory).get(replay_name, {})


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_injected_frames(
    source_dir: str,
    source_name: str,
    target_dir: str,
    target_name: str,
) -> Verification:
    source = _build_frame_inventory(Path(source_dir), source_name)
    target = _build_frame_inventory(Path(target_dir), target_name)
    source_indexes = set(source)
    target_indexes = set(target)
    common_indexes = sorted(source_indexes & target_indexes)
    size_mismatches = []
    hash_mismatches = []
    for frame in common_indexes:
        source_size = source[frame].stat().st_size
        target_size = target[frame].stat().st_size
        if source_size != target_size:
            size_mismatches.append(
                {
                    "frame": frame,
                    "source_size": source_size,
                    "target_size": target_size,
                }
            )
            continue
        source_hash = _sha256(source[frame])
        target_hash = _sha256(target[frame])
        if source_hash != target_hash:
            hash_mismatches.append(
                {
                    "frame": frame,
                    "source_sha256": source_hash,
                    "target_sha256": target_hash,
                }
            )
    missing_target = sorted(source_indexes - target_indexes)
    extra_target = sorted(target_indexes - source_indexes)
    return {
        "source_frame_count": len(source),
        "target_frame_count": len(target),
        "source_min_frame": min(source_indexes) if source_indexes else None,
        "source_max_frame": max(source_indexes) if source_indexes else None,
        "target_min_frame": min(target_indexes) if target_indexes else None,
        "target_max_frame": max(target_indexes) if target_indexes else None,
        "missing_target_frames": missing_target,
        "extra_target_frames": extra_target,
        "size_mismatch_count": len(size_mismatches),
        "size_mismatches": size_mismatches[:20],
        "hash_mismatch_count": len(hash_mismatches),
        "hash_mismatches": hash_mismatches[:20],
        "verified_frame_count": len(common_indexes) - len(size_mismatches) - len(hash_mismatches),
        "ok": (
            bool(source)
            and len(source) == len(target)
            and not missing_target
            and not extra_target
            and not size_mismatches
            and not hash_mismatches
        ),
    }


def inject_replay_with_vgrplay(
    source_dir: str,
    replay_name: str,
    temp_dir: str,
    vgrplay_path: str = DEFAULT_VGRPLAY,
    live_replay_name: Optional[str] = None,
    *, output: str | None = None, timeout: float = 120.0,
) -> InjectionReport:
    source = select_family(Path(source_dir), replay_name)
    live = find_live_temp_replay(temp_dir, replay_name=live_replay_name)
    target = Path(temp_dir).absolute() / f"{live['oname']}.0.vgr"
    source_inputs = ReportInputs(replays=(source,))
    output_path = Path(output) if output is not None else None
    if output_path is not None:
        validate_report_outputs(source_inputs, (output_path,))
        validate_report_outputs(ReportInputs(replays=(target,)), (output_path,))
    report_inputs = ReportInputs(files=(output_path,) if output_path is not None else ())
    before_files = {p.name: p.stat().st_mtime_ns for p in target.parent.glob(f"{live['oname']}.*.vgr")}
    cmd = [vgrplay_path, "-source", str(source.parent), "-sname", replay_name,
           "-overwrite", temp_dir, "-oname", str(live["oname"])]
    with replacement(source, target) as transaction:
        if output_path is not None:
            transaction.prepare_report(output_path)
        transaction.begin()
        try:
            completed = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired as error:
            raise ArchiveError('subprocess_timeout', target, str(error), transaction.operation) from error
        if completed.returncode:
            raise ArchiveError('subprocess_failed', target, f'vgrplay exited {completed.returncode}: {completed.stderr}', transaction.operation)
        transaction.verify()
        source_inputs.recheck()
        after_files = {p.name: p.stat().st_mtime_ns for p in target.parent.glob(f"{live['oname']}.*.vgr")}
        changed = sorted(name for name, mtime in after_files.items()
                         if name not in before_files or before_files[name] != mtime)
        report: InjectionReport = {"captured_at": datetime.now().isoformat(), "command": cmd,
                  "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr,
                  "source_dir": str(source.parent), "replay_name": replay_name,
                  "temp_dir": str(target.parent), "live_replay": live,
                  "target_after": _frame_summary(_build_frame_inventory(target.parent, str(live["oname"]))),
                  "changed_files": changed, "changed_count": len(changed),
                  "verification": verify_injected_frames(str(source.parent), replay_name, str(target.parent), str(live["oname"])),
                  "source_scope": transaction.source.scope, "recovery": str(transaction.operation),
                  "success_scope": "filesystem_only"}
        try:
            if output_path is not None:
                report_inputs.recheck()
                validate_replay_output(target, output_path)
                recovery_files = tuple(p for p in transaction.operation.rglob('*') if p.is_file())
                validate_report_outputs(ReportInputs(files=recovery_files, replays=(source, target)), (output_path,))
                payload = json.dumps(report, indent=2, ensure_ascii=False)
                transaction.prepare_report(output_path, payload)
                protected = ReportInputs(files=tuple(p for p in transaction.operation.rglob('*') if p.is_file()),
                                         replays=(source, target))
                source_inputs.recheck()
                write_report_output(protected, output_path, payload)
            transaction.commit()
        except (TypeError, UnicodeError, OSError) as error:
            raise ArchiveError('publication_failed', output_path or target, str(error), transaction.operation) from error
        return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Inject a replay into the current temp replay slot via vgrplay.")
    parser.add_argument("--source-dir", required=True, help="Replay source directory")
    parser.add_argument("--replay-name", required=True, help="Replay name used by vgrplay -sname")
    parser.add_argument("--temp-dir", default=str(Path.home() / "AppData" / "Local" / "Temp"), help="Temp replay directory")
    parser.add_argument("--vgrplay", default=DEFAULT_VGRPLAY, help="Path to vgrplay.exe")
    parser.add_argument("--live-replay-name", "--target-name", help="Explicit temp replay group name to overwrite")
    parser.add_argument("-o", "--output", help="Optional output JSON path")
    args = parser.parse_args()

    try:
        report = inject_replay_with_vgrplay(
            source_dir=args.source_dir, replay_name=args.replay_name, temp_dir=args.temp_dir,
            vgrplay_path=args.vgrplay, live_replay_name=args.live_replay_name, output=args.output,
        )
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    except (ReplayInputError, ReplayOutputError, OSError, ValueError) as error:
        print(json.dumps({"success": False, "error_code": getattr(error, "code", "archive_failed"),
                          "error": str(error), "recovery": str(getattr(error, "recovery", "") or "")}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
