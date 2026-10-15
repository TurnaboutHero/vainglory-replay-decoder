"""Synthetic offline request fixtures; not captured traffic or runtime evidence."""
from dataclasses import FrozenInstanceError
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

from vg.core.outgoing_requests import (
    INPUT_FORMAT, REFERENCE_CLIENT_SHA256, REQUEST_SCHEMAS, MalformedRequestFrame,
    RequestDecodeError, UnsupportedInputFormat, UnsupportedRequestOpcode,
    decode_outgoing_request, request_schema_document,
)


def frame(opcode, payload):
    return struct.pack(">HH", len(payload) + 2, opcode) + payload


def decode(data):
    return decode_outgoing_request(data, input_format=INPUT_FORMAT)


# Independent literal payload sizes and field order, including asymmetric words
# so accidental little-endian decoding does not pass.
CASES = (
    (0x03f4, "0102030480010203", ("destination_component_0_bits", "destination_component_2_bits"), (0x01020304, 0x80010203)),
    (0x03f5, "0102030480010203", ("destination_component_0_bits", "destination_component_2_bits"), (0x01020304, 0x80010203)),
    (0x03f6, "0102030480010203", ("destination_component_0_bits", "destination_component_2_bits"), (0x01020304, 0x80010203)),
    (0x0424, "12345678a5", ("target_actor_id", "raw_flag"), (0x12345678, 0xa5)),
    (0x0411, "f1234567ff", ("target_actor_id_or_sentinel", "ability_array_index"), (0xf1234567, 0xff)),
    (0x0412, "01020304800102037fc12345ab", ("vector_component_0_bits", "vector_component_1_bits", "vector_component_2_bits", "ability_array_index"), (0x01020304, 0x80010203, 0x7fc12345, 0xab)),
    (0x0413, "1122334401020304800102037fc12345ab", ("raw_target_word", "vector_component_0_bits", "vector_component_1_bits", "vector_component_2_bits", "ability_array_index"), (0x11223344, 0x01020304, 0x80010203, 0x7fc12345, 0xab)),
    (0x0448, "f1234567", ("item_instance_id",), (0xf1234567,)),
    (0x0449, "11223344f1234567", ("target_actor_id", "item_instance_id"), (0x11223344, 0xf1234567)),
    (0x044a, "01020304800102037fc12345f1234567", ("vector_component_0_bits", "vector_component_1_bits", "vector_component_2_bits", "item_instance_id"), (0x01020304, 0x80010203, 0x7fc12345, 0xf1234567)),
)


class OutgoingRequestTests(unittest.TestCase):
    def test_all_ten_exact_payloads_and_unsigned_big_endian_fields(self):
        self.assertEqual(set(REQUEST_SCHEMAS), {case[0] for case in CASES})
        for opcode, payload_hex, names, values in CASES:
            with self.subTest(opcode=opcode):
                payload = bytes.fromhex(payload_hex)
                data = frame(opcode, payload)
                result = decode(data)
                self.assertEqual(result.opcode, opcode)
                self.assertEqual(tuple(f.name for f in result.fields), names)
                self.assertEqual(tuple(f.value for f in result.fields), values)
                output = result.to_dict()
                self.assertEqual(output["payload_size"], len(payload))
                self.assertEqual(output["content_size"], len(payload) + 2)
                self.assertEqual(output["frame_size"], len(data))
                self.assertEqual(output["provenance"]["input_sha256"], hashlib.sha256(data).hexdigest())
                for f in result.fields:
                    expected_kind = "f32_bits" if f.name.endswith("_bits") else (
                        "u8" if f.name in ("raw_flag", "ability_array_index") else "u32")
                    self.assertEqual(f.kind, expected_kind)
                json.dumps(output, allow_nan=False)

    def test_format_is_required_and_unknown_encrypted_formats_are_rejected(self):
        data = frame(0x0448, bytes(4))
        with self.assertRaises(TypeError):
            decode_outgoing_request(data)
        for wrong_format in (None, "", "auto", "vgr", "encrypted", "blowfish", INPUT_FORMAT + "-unknown"):
            with self.subTest(input_format=wrong_format), self.assertRaises(UnsupportedInputFormat):
                decode_outgoing_request(data, input_format=wrong_format)
        for bad_input in (None, "0006044800000000", 8, [0] * 8):
            with self.assertRaises(TypeError):
                decode(bad_input)
        self.assertEqual(decode(data), decode(bytearray(data)))
        self.assertEqual(decode(data), decode(memoryview(data)))

    def test_every_truncation_suffix_and_schema_length_mismatch_is_rejected(self):
        for opcode, payload_hex, _, _ in CASES:
            payload = bytes.fromhex(payload_hex)
            data = frame(opcode, payload)
            for size in range(len(data)):
                with self.subTest(opcode=opcode, truncation=size), self.assertRaises(RequestDecodeError):
                    decode(data[:size])
            for extra in (b"\x00", bytes(6), data):
                with self.subTest(opcode=opcode, extra=len(extra)), self.assertRaises(RequestDecodeError):
                    decode(data + extra)
            # Repaired outer lengths must not permit short payloads or VGR suffixes.
            for size in range(22):
                if size != len(payload):
                    with self.subTest(opcode=opcode, payload_size=size), self.assertRaises(RequestDecodeError):
                        decode(frame(opcode, bytes(size)))
            for declared in (0, 1, len(payload) + 1, len(payload) + 3, 0xffff):
                with self.assertRaises(MalformedRequestFrame):
                    decode(struct.pack(">H", declared) + data[2:])

    def test_endianness_unknown_opcode_and_block_rounded_frames(self):
        data = frame(0x0448, bytes.fromhex("11223344"))
        with self.assertRaises(MalformedRequestFrame):
            decode(data[:2][::-1] + data[2:])
        with self.assertRaises(UnsupportedRequestOpcode):
            decode(data[:2] + data[2:4][::-1] + data[4:])
        for opcode in (0, 0xffff, 0x03f1, 0x044c):
            with self.assertRaises(UnsupportedRequestOpcode):
                decode(frame(opcode, b""))
        # Conditional transformed frames have block-rounded content lengths.
        # Even a coincidental supported opcode cannot make these valid plaintext.
        for opcode, payload_hex, _, _ in CASES:
            content = struct.pack(">H", opcode) + bytes.fromhex(payload_hex)
            padded_size = (len(content) + 7) & ~7
            padded = content.ljust(padded_size, b"\x00")
            with self.assertRaises(RequestDecodeError):
                decode(struct.pack(">H", padded_size) + padded)

    def test_float_bit_patterns_are_preserved_without_numeric_or_unit_claims(self):
        for bits in (0, 0x80000000, 0x3f800000, 0xbf800000, 0x7f800000,
                     0xff800000, 0x7fc12345, 0x7f812345, 0xffffffff):
            result = decode(frame(0x0412, struct.pack(">IIIB", bits, bits, bits, 255)))
            for f in result.fields[:3]:
                self.assertEqual((f.kind, f.value), ("f32_bits", bits))
            json.dumps(result.to_dict(), allow_nan=False)
        for value in (0, 1, 2, 255):
            self.assertEqual(decode(frame(0x0424, struct.pack(">IB", 0xffffffff, value))).field("raw_flag").value, value)
            self.assertEqual(decode(frame(0x0411, struct.pack(">IB", 0xffffffff, value))).field("ability_array_index").value, value)
        self.assertEqual(decode(frame(0x0411, b"\xff" * 5)).field("target_actor_id_or_sentinel").value, 0xffffffff)

    def test_schema_is_immutable_contiguous_and_build_scoped(self):
        with self.assertRaises(TypeError):
            REQUEST_SCHEMAS[0] = REQUEST_SCHEMAS[0x0448]
        for schema in REQUEST_SCHEMAS.values():
            offset = 0
            for f in schema.fields:
                self.assertEqual(f.offset, offset)
                offset += f.width
            self.assertEqual(offset, schema.payload_size)
            with self.assertRaises(FrozenInstanceError):
                schema.note = "changed"
        doc = request_schema_document()
        self.assertEqual(doc["provenance"]["reference_client_sha256"], REFERENCE_CLIENT_SHA256)
        doc["schemas"].clear()
        self.assertEqual(len(request_schema_document()["schemas"]), 10)
        result = decode(frame(0x0449, struct.pack(">II", 7, 2000)))
        self.assertEqual(result.field("item_instance_id").value, 2000)
        with self.assertRaises(KeyError):
            result.field("item_slot")
        provenance = result.to_dict()["provenance"]
        self.assertEqual(provenance["source_client_build"], "unverified")
        self.assertEqual(provenance["plaintext"], "caller_declared")
        self.assertEqual(provenance["server_acceptance"], "unverified")
        self.assertEqual(provenance["request_response_correlation"], "unestablished")

    def test_vgr_layouts_and_incoming_item_message_are_separate(self):
        from vg.analysis.event_timeline import decode_fields
        from vg.core.vgr_records import iter_records
        from tests.test_native_inventory import packet

        for opcode, payload, suffix in (
            (0x0448, struct.pack(">I", 2000), bytes(2)),
            (0x0449, struct.pack(">II", 7, 2000), bytes(6)),
            (0x044a, struct.pack(">IIII", 1, 2, 3, 2000), bytes(6)),
        ):
            recorded = packet(1, opcode, payload + suffix)
            # Neither the full VGR record nor its opcode/payload with a repaired
            # BE16 prefix belongs to the compact outgoing request format.
            with self.assertRaises(RequestDecodeError):
                decode(recorded)
            with self.assertRaises(RequestDecodeError):
                decode(frame(opcode, payload + suffix))
            row = decode_fields(next(iter_records(recorded)))
            self.assertEqual(row["native_semantic_scope"], "serializer_prefix")
            if opcode != 0x0448:
                self.assertIn("native_request_arguments", row)
                self.assertNotIn("native_item_instance_id", row)
            self.assertEqual(decode(frame(opcode, payload)).field("item_instance_id").value, 2000)
        incoming = struct.pack(">IIIffB", 7, 2000, 9, 1.25, -2.5, 0) + b"\xaa"
        row = decode_fields(next(iter_records(packet(1, 0x044c, incoming))))
        self.assertEqual(row["native_type"], "item_activation_message")
        self.assertEqual(row["native_semantic_scope"], "receiver_prefix")
        with self.assertRaises(RequestDecodeError):
            decode(frame(0x044c, incoming))
        with self.assertRaises(UnsupportedRequestOpcode):
            decode(frame(0x044c, bytes(4)))

    def test_cli_schema_hex_file_and_failure_without_partial_output(self):
        command = [sys.executable, "-B", "-m", "vg.core.outgoing_requests"]
        result = subprocess.run(command + ["--schema"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), request_schema_document())
        data = frame(0x0449, struct.pack(">II", 7, 2000))
        args = ["--input-format", INPUT_FORMAT]
        result = subprocess.run(command + args + ["--hex", data.hex()], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), decode(data).to_dict())
        failures = [
            ["--hex", data.hex()], args + ["--hex", "not hex"],
            args + ["--hex", data[:-1].hex()], args + ["--hex", "ff" * 100],
            ["--input-format", "encrypted", "--hex", data.hex()],
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "request.bin"
            path.write_bytes(data)
            result = subprocess.run(command + args + ["--frame", str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), decode(data).to_dict())
            self.assertEqual(path.read_bytes(), data)
            path.write_bytes(data + bytes(100))
            failures += [args + ["--frame", str(path)], args + ["--frame", str(path) + ".missing"]]
            for case in failures:
                result = subprocess.run(command + case, capture_output=True, text=True)
                self.assertEqual(result.returncode, 2, (case, result.stderr))
                self.assertEqual(result.stdout, "")
                self.assertIn("error:", result.stderr)


if __name__ == "__main__":
    unittest.main()
