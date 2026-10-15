"""Stream lossless event rows with verified native labels from numbered VGR sections."""

import argparse
from collections.abc import Iterable, Iterator, Sequence
from contextlib import nullcontext
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import sys
from typing import Final, NotRequired, TextIO

# Re-export the established decoding API for existing consumers.
from vg.analysis.native_event_fields import (
    ATTRIBUTE_STATS, DEFAULT_OPCODES, DecodedFields, END_MATCH_EVIDENCE,
    END_MATCH_EVIDENCE_SHA256, EXPECTED_CONTENT_LENGTH, KnownOpcode,
    NATIVE_EVIDENCE, NATIVE_EVIDENCE_SHA256, decode_fields,
)
from vg.core.definition_catalog import (
    CatalogError, DefinitionCatalog, enrich_definition, load_catalog, supported_build_profile,
)
from vg.core.entity_identity import EntityResolver
from vg.core.vgr_records import VGRRecord, VGRRecordError, iter_records


APPLE_DOUBLE_MAGIC: Final = b"\x00\x05\x16\x07"
SECTION_NAME: Final = re.compile(r"^(?P<prefix>.+)\.(?P<frame>\d+)\.vgr$")


class TimelineRow(DecodedFields):
    frame_idx: int
    record_index: int
    record_offset: int
    timestamp: float
    content_length: int
    opcode: int
    payload_hex: str
    ref0_identity: NotRequired[dict[str, object]]
    ref1_identity: NotRequired[dict[str, object]]


@dataclass(frozen=True, slots=True)
class TimelineInputError(ValueError):
    path: Path
    reason: str

    def __str__(self) -> str:
        return f"{self.path}: {self.reason}"


def _is_apple_double(path: Path) -> bool:
    with path.open("rb") as stream:
        return stream.read(4) == APPLE_DOUBLE_MAGIC


def _discover_sections(replay_file: Path) -> list[tuple[int, Path]]:
    path = Path(replay_file)
    if not path.exists():
        raise TimelineInputError(path=path, reason="input path does not exist")
    if not path.is_file():
        raise TimelineInputError(path=path, reason="input path is not a file")

    match = SECTION_NAME.fullmatch(path.name)
    if match is None:
        raise TimelineInputError(
            path=path,
            reason="input must be a numbered .vgr section such as replay.0.vgr",
        )
    if _is_apple_double(path):
        raise TimelineInputError(path=path, reason="input is AppleDouble metadata")

    prefix = match.group("prefix")
    sections: list[tuple[int, Path]] = []
    for candidate in path.parent.iterdir():
        candidate_match = SECTION_NAME.fullmatch(candidate.name)
        if (
            not candidate.is_file()
            or candidate_match is None
            or candidate_match.group("prefix") != prefix
        ):
            continue
        if _is_apple_double(candidate):
            continue
        sections.append((int(candidate_match.group("frame")), candidate))

    sections.sort(key=lambda section: (section[0], section[1].name))
    return sections


def iter_timeline(
    replay_file: str | Path,
    opcodes: Iterable[int] | None = None,
    entity_ids: Iterable[int] | None = None,
    *,
    catalog: DefinitionCatalog | None = None,
    build_sha256: str | None = None,
) -> Iterator[TimelineRow]:
    """Yield selected records in numeric frame and original record order.

    Optional identities retain prior spawn observations and separate lifecycle
    action evidence, never current life or kill-credit claims. build_sha256
    asserts this recording's build; the VGR stream itself cannot authenticate
    its originating executable.
    """
    selected_opcodes = DEFAULT_OPCODES if opcodes is None else frozenset(opcodes)
    selected_entities = None if entity_ids is None else frozenset(entity_ids)

    sections = _discover_sections(Path(replay_file))
    if (catalog is None) != (build_sha256 is None):
        raise CatalogError("catalog and build_sha256 must be supplied together")
    recording_id = str(Path(replay_file).resolve().with_name(
        Path(replay_file).name.rsplit(".", 2)[0]))
    resolver = (EntityResolver(recording_id, catalog, build_sha256)
                if catalog is not None else None)
    for frame_idx, frame_path in sections:
        data = frame_path.read_bytes()
        for record_index, record in enumerate(iter_records(data)):
            if resolver is not None:
                try:
                    resolver.observe(record, frame_idx)
                except ValueError as error:
                    raise TimelineInputError(frame_path, str(error)) from error
            if record.opcode not in selected_opcodes:
                continue
            fields = decode_fields(record)
            if selected_entities is not None and (
                fields.get("ref0") not in selected_entities
                and fields.get("ref1") not in selected_entities
            ):
                continue
            row: TimelineRow = {
                "frame_idx": frame_idx,
                "record_index": record_index,
                "record_offset": record.offset,
                "timestamp": record.timestamp,
                "content_length": record.content_length,
                "opcode": record.opcode,
                "payload_hex": record.payload.hex(),
                **fields,
            }
            if resolver is not None:
                for ref in ("ref0", "ref1"):
                    if ref not in fields:
                        continue
                    entity = fields[ref]
                    prior = None if entity == 0xFFFFFFFF else resolver.latest_observed(entity)
                    identity = (
                        {"evidence_scope": "prior_spawn_observation", **asdict(prior)}
                        if prior is not None else {
                            "recording_id": recording_id, "entity_id": entity,
                            "status": "sentinel" if entity == 0xFFFFFFFF else "unobserved",
                            "evidence_scope": "prior_spawn_observation",
                            "definition_name": None, "kind": "unknown",
                            "owner_entity_id": None, "credited_player_id": None,
                        })
                    identity["lifecycle"] = asdict(resolver.lifecycle_evidence(entity))
                    row[ref + "_identity"] = identity
            yield row


def _integer(value: str) -> int:
    try:
        return int(value, 0)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"invalid integer: {value}") from error


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stream verified native VGR event structures as lossless JSONL.")
    parser.add_argument("path", type=Path, help="numbered .vgr replay section")
    parser.add_argument("-o", "--output", type=Path, help="write JSONL to this path")
    parser.add_argument("--opcode", action="append", type=_integer,
                        help="opcode integer; repeat to select more (default includes 0x0430 ActionActorDie, "
                             "item activation requests/messages, sell requests, buy rejection notifications and raw cooldown/charge events)")
    parser.add_argument("--entity", action="append", type=_integer, help="ref0/ref1 integer, including ActorDie victim/raw source; repeat to select more")
    parser.add_argument("--manifest", type=Path, help="user-owned definition manifest")
    parser.add_argument("--executable", type=Path, help="user-owned paired game executable")
    parser.add_argument("--build-sha256", help="expected executable hash and asserted recording build")
    parser.add_argument("--manifest-sha256", help="expected hash of the independently paired manifest")
    parser.add_argument("--entity-resource", nargs=3, action="append",
                        metavar=("INDEX", "PATH", "SHA256"),
                        help="enrich one definition from an owned actor CFF resource; repeat for more")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        sections = _discover_sections(args.path)
        catalog = None
        catalog_args = (args.manifest, args.executable, args.build_sha256, args.manifest_sha256)
        resource_paths: list[Path] = []
        if any(value is not None for value in catalog_args) or args.entity_resource:
            if not all(value is not None for value in catalog_args):
                raise CatalogError("catalog mode requires --manifest, --executable, --build-sha256 and --manifest-sha256")
            profile = supported_build_profile(args.build_sha256, args.manifest_sha256)
            executable = args.executable.read_bytes()
            catalog = load_catalog(args.manifest.read_bytes(), executable, profile)
            seen_indices: set[int] = set()
            for raw_index, raw_path, resource_hash in args.entity_resource or []:
                try:
                    index = int(raw_index, 0)
                except ValueError as error:
                    raise CatalogError(f"invalid entity resource index: {raw_index}") from error
                if index in seen_indices:
                    raise CatalogError(f"duplicate entity resource index: {index}")
                seen_indices.add(index)
                resource_path = Path(raw_path)
                resource_paths.append(resource_path)
                catalog = enrich_definition(catalog, index, resource_path.read_bytes(), executable,
                                            resource_hash)
        if args.output is not None:
            output_path = args.output.resolve()
            output_match = SECTION_NAME.fullmatch(args.output.name)
            target_match = SECTION_NAME.fullmatch(output_path.name)
            input_prefix = args.path.name.rsplit(".", 2)[0]
            if (
                (output_match is not None
                 and output_match.group("prefix") == input_prefix
                 and args.output.parent.resolve() == args.path.parent.resolve())
                or (target_match is not None
                    and target_match.group("prefix") == input_prefix
                    and output_path.parent == args.path.parent.resolve())
            ):
                raise TimelineInputError(
                    path=args.output,
                    reason="output names a sibling input .vgr section",
                )
            output_exists = args.output.exists()
            for asset in (args.manifest, args.executable, *resource_paths):
                if asset is not None and (
                    output_path == asset.resolve()
                    or (output_exists and args.output.samefile(asset))
                ):
                    raise TimelineInputError(args.output, "output path is a catalog source asset")
            if any(
                output_path == section_path.resolve()
                or (output_exists and args.output.samefile(section_path))
                for _, section_path in sections
            ):
                raise TimelineInputError(
                    path=args.output,
                    reason="output path is an input .vgr section",
                )

        output_context = (args.output.open("w", encoding="utf-8", newline="\n")
                          if args.output is not None else nullcontext(sys.stdout))
        with output_context as stream:
            rows = iter_timeline(args.path, opcodes=args.opcode, entity_ids=args.entity,
                                 catalog=catalog, build_sha256=args.build_sha256)
            _write_jsonl(rows, stream)
    except (OSError, CatalogError, TimelineInputError, VGRRecordError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


def _write_jsonl(rows: Iterable[TimelineRow], stream: TextIO) -> None:
    for row in rows:
        stream.write(json.dumps(row, allow_nan=False, sort_keys=True) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
