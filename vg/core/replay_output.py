"""Protect numbered replay inputs when publishing a decoder result."""
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


def validate_replay_output(replay: Path, output: Path) -> None:
    """Reject replay aliases and names consumed by lexical sibling discovery."""
    pattern = f"{replay.stem.rsplit('.', 1)[0]}.*.vgr"
    resolved = output.resolve()
    for candidate in (output, resolved):
        if candidate.parent.resolve() == replay.parent.resolve() and fnmatch(candidate.name, pattern):
            raise ReplayOutputError(output, "output names a sibling input .vgr section")
    for source in (replay, *replay.parent.glob(pattern)):
        if resolved == source.resolve() or (output.exists() and source.exists() and output.samefile(source)):
            raise ReplayOutputError(output, "output path aliases an input replay")


def write_replay_output(replay: Path, output: Path, payload: str) -> None:
    """Publish atomically so failed writes preserve existing results and inputs."""
    validate_replay_output(replay, output)
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
