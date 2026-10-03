"""Protect numbered replay inputs when publishing a decoder result."""
from collections.abc import Collection
from dataclasses import dataclass
from fnmatch import fnmatch
import os
from pathlib import Path
import tempfile


@dataclass(frozen=True, slots=True)
class ReplayOutputError(ValueError):
    path: Path
    reason: str

    def __str__(self) -> str:
        return f"{self.path}: {self.reason}"


def validate_output_sources(sources: Collection[Path], output: Path) -> None:
    """Reject direct, symbolic, and hard-link aliases of consumed input files."""
    resolved = output.resolve()
    for source in sources:
        if resolved == source.resolve() or (output.exists() and source.exists() and output.samefile(source)):
            raise ReplayOutputError(output, "output path aliases an input file")


def validate_replay_output(replay: Path, output: Path) -> None:
    """Reject replay aliases and names consumed by lexical sibling discovery."""
    pattern = f"{replay.stem.rsplit('.', 1)[0]}.*.vgr"
    resolved = output.resolve()
    for candidate in (output, resolved):
        if candidate.parent.resolve() == replay.parent.resolve() and fnmatch(candidate.name, pattern):
            raise ReplayOutputError(output, "output names a sibling input .vgr section")
    validate_output_sources((replay, *replay.parent.glob(pattern)), output)


def validate_replay_outputs(replays: Collection[Path], output: Path) -> None:
    """Protect every discovered replay family in a batch, including future sections."""
    for replay in replays:
        validate_replay_output(replay, output)


def write_replay_output(replay: Path, output: Path, payload: str) -> None:
    """Publish a single-match report through the shared batch-safe writer."""
    write_replay_outputs((replay,), output, payload)


def write_replay_outputs(replays: Collection[Path], output: Path, payload: str) -> None:
    """Publish atomically so failed writes preserve existing results and inputs."""
    validate_replay_outputs(replays, output)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=output.parent,
            prefix=f".{output.name}.", suffix=".tmp", delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
        os.replace(temporary, output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
