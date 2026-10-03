"""Generic credit-event parsing for decoder_v2."""

from __future__ import annotations

import math
import struct
from collections import defaultdict
from typing import Dict, Iterable, List

from vg.core.vgr_records import VGRRecord, VGRRecordError, iter_records

from .completeness import load_frames
from .models import CreditEventRecord


def credit_event_from_record(record: VGRRecord, frame_idx: int) -> CreditEventRecord:
    """Decode an exact native resource record; preserve both legacy and owning offsets."""
    if record.opcode != 0x041D or record.content_length != 16:
        raise VGRRecordError(f"frame {frame_idx}: unsupported credit opcode/length {record.opcode:04x}/{record.content_length}", record.offset)
    entity_id = struct.unpack_from(">I", record.payload)[0]
    raw_value = struct.unpack_from(">f", record.payload, 4)[0]
    finite = math.isfinite(raw_value)
    return CreditEventRecord(
        frame_idx, entity_id, record.payload[8], raw_value if finite else None,
        record.offset + 7,
        (struct.pack(">BH", record.content_length, record.opcode) + record.payload[:9].tobytes()).hex(),
        entity_id <= 0xFFFF, finite, record.payload[9], record.offset,
    )


def iter_credit_events(replay_file: str) -> Iterable[CreditEventRecord]:
    """Yield strict owning 041d records, never signatures embedded in another payload."""
    for frame_idx, data in load_frames(replay_file):
        for record in iter_records(data):
            if record.opcode == 0x041D:
                yield credit_event_from_record(record, frame_idx)


def collect_credit_events_by_entity(replay_file: str) -> Dict[int, List[CreditEventRecord]]:
    """Collect credit events grouped by BE entity id."""
    grouped: Dict[int, List[CreditEventRecord]] = defaultdict(list)
    for event in iter_credit_events(replay_file):
        grouped[event.entity_id_be].append(event)
    return grouped
