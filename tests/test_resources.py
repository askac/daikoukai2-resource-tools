"""Test resource updates, malformed inputs and output preservation."""

import copy
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from examples.make_demo import demo_files
from resource_tool import write_new
from resource_tools.archives import decode_stream, extract_entry, read_archive, replace_entry
from resource_tools.bitmap import decode_bitmap, encode_bitmap
from resource_tools.images import export_image, import_image
from resource_tools.text_banks import export_text, import_text, read_bank


ROOT = Path(__file__).resolve().parents[1]


class TextTests(unittest.TestCase):
    def setUp(self):
        self.source = demo_files()["MESSAGE.DAT"]
        self.document = export_text(self.source, 2, "message")

    def test_unchanged_export_import_is_exact(self):
        self.assertEqual(import_text(self.source, self.document), self.source)

    def test_edit_keeps_offsets_and_other_records(self):
        self.document["records"][0]["texts"] = ["EDITED"]
        output = import_text(self.source, self.document)
        second = int.from_bytes(self.source[2:4], "big")
        self.assertEqual(output[:4], self.source[:4])
        self.assertEqual(output[second:], self.source[second:])
        self.assertEqual(len(output), len(self.source))
        self.assertEqual(read_bank(output, 2, "message")["records"][0]["source_texts"], ["EDITED"])

    def test_invalid_edits_are_rejected(self):
        for text in ("X" * 200, "A\0B", "\U0001f600", "ADDED %s"):
            with self.subTest(text=text):
                document = copy.deepcopy(self.document)
                document["records"][0]["texts"] = [text]
                with self.assertRaises(ValueError):
                    import_text(self.source, document)
        self.document["records"][1]["texts"] = ["VALUE %s"]
        with self.assertRaisesRegex(ValueError, "Control tokens"):
            import_text(self.source, self.document)

    def test_stale_source_and_changed_indices_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Source changed"):
            import_text(self.source + b"\0", self.document)
        self.document["records"][0]["index"] = 1
        with self.assertRaises(ValueError):
            import_text(self.source, self.document)

    def test_menu_count_and_declared_width_are_preserved(self):
        source = b"\0\x02\x04\x02ONE\0TWO\0" + bytes(12)
        document = export_text(source, 2, "menu")
        document["records"][0]["texts"] = ["FOUR", "TWO"]
        self.assertEqual(import_text(source, document)[2:4], b"\x04\x02")
        document["records"][0]["texts"][0] = "FIVE!"
        with self.assertRaisesRegex(ValueError, "declared width"):
            import_text(source, document)

    def test_invalid_tables_and_unclassified_data_are_rejected(self):
        for source in (b"\0", b"\0\x03X", b"\0\x04\0\x04A\0", b"\0\x02A", b"\0\x02A\0B"):
            with self.subTest(source=source), self.assertRaises(ValueError):
                export_text(source, 2, "message")


class ImageTests(unittest.TestCase):
    def setUp(self):
        self.source = demo_files()["GRAPHICS.BIN"]

    def test_index_bitmap_roundtrip(self):
        pixels = bytes(range(16)) * 2
        self.assertEqual(decode_bitmap(encode_bitmap(8, 4, pixels)), (8, 4, pixels))

    def test_unchanged_import_is_exact(self):
        self.assertEqual(import_image(self.source, 0, *export_image(self.source, 0)), self.source)

    def test_edit_preserves_other_frame_and_flags(self):
        source = bytearray(self.source)
        source[9] |= 0x80
        source = bytes(source)
        width, height, pixels = export_image(source, 0)
        pixels = bytes([15]) + pixels[1:]
        output = import_image(source, 0, width, height, pixels)
        second = int.from_bytes(source[4:8], "big")
        self.assertEqual(output[:12], source[:12])
        self.assertEqual(output[second:], source[second:])
        self.assertEqual(export_image(output, 0), (width, height, pixels))

    def test_bad_dimensions_palette_and_bounds_are_rejected(self):
        bitmap = bytearray(encode_bitmap(8, 4, bytes(32)))
        bitmap[54] = 1
        with self.assertRaises(ValueError):
            decode_bitmap(bitmap)
        with self.assertRaises(ValueError):
            decode_bitmap(encode_bitmap(8, 4, bytes(32))[:-1])
        with self.assertRaises(ValueError):
            import_image(self.source, 0, 4, 8, bytes(32))
        with self.assertRaises(ValueError):
            export_image(self.source, -1)

    def test_update_that_cannot_fit_is_rejected(self):
        frame = struct.pack("<HH8H", 8, 4, *([0] * 8)) + b"\x01" * 4
        source = struct.pack(">I", 4) + frame
        with self.assertRaises(ValueError):
            import_image(source, 0, 8, 4, bytes(range(16)) * 2)


class ArchiveTests(unittest.TestCase):
    def test_known_literal_stream(self):
        self.assertEqual(decode_stream(b"\x18", bytes(range(256)), 3), b"\0\x01\x02")
        with self.assertRaisesRegex(ValueError, "Truncated"):
            decode_stream(b"", bytes(range(256)), 3)

    def test_compressed_entry_and_unchanged_replacement(self):
        files = demo_files()
        source = files["GRAPHICS.LZW"]
        self.assertEqual(extract_entry(source, 0), files["GRAPHICS.BIN"])
        self.assertEqual(replace_entry(source, 0, files["GRAPHICS.BIN"]), source)

    def test_named_raw_entry_can_be_replaced_without_moving_data(self):
        original = b"ORIGINAL SAMPLE!"
        header = b"LW11" + bytes(12) + bytes(range(256))
        directory = b"SAMPLE.TXT\0".ljust(16, b"\0")
        directory += struct.pack(">III", len(original), len(original), 308) + bytes(8)
        source = header + directory + original
        self.assertEqual(read_archive(source)[0]["name"], "SAMPLE.TXT")
        self.assertEqual(extract_entry(source, 0), original)
        replacement = b"X" * len(original)
        output = replace_entry(source, 0, replacement)
        self.assertEqual(len(output), len(source))
        self.assertEqual(output[:288], source[:288])
        self.assertEqual(output[292:308], source[292:308])
        self.assertEqual(extract_entry(output, 0), replacement)

    def test_bad_archive_or_replacement_is_rejected(self):
        source = demo_files()["GRAPHICS.LZW"]
        for invalid in (b"MZ" + source[2:], source[:280], source[:-1]):
            with self.subTest(source=invalid[:4]), self.assertRaises(ValueError):
                read_archive(invalid)
        with self.assertRaises(ValueError):
            replace_entry(source, 0, b"SHORT")
        with self.assertRaises(ValueError):
            extract_entry(source, -1)


class OutputTests(unittest.TestCase):
    def test_existing_output_and_source_are_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "source.bin"
            path.write_bytes(b"KEEP")
            with self.assertRaises(FileExistsError):
                write_new(path, b"REPLACE")
            self.assertEqual(path.read_bytes(), b"KEEP")

    def test_write_failure_does_not_leave_success_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "failed.bin"
            with patch("resource_tool.os.fsync", side_effect=OSError("Simulated failure")):
                with self.assertRaises(OSError):
                    write_new(path, b"DATA")
            self.assertFalse(path.exists())

    def test_cli_from_another_directory_and_failure_before_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "sample.dat"
            source.write_bytes(demo_files()["MESSAGE.DAT"])
            edits = root / "edits.json"
            output = root / "new.dat"
            command = [sys.executable, "-B", str(ROOT / "resource_tool.py")]
            result = subprocess.run(command + ["text-export", str(source), "--width", "2",
                "--kind", "message", "-o", str(edits)], cwd=root, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            document = json.loads(edits.read_text())
            document["records"][0]["texts"] = ["X" * 1000]
            edits.write_text(json.dumps(document), encoding="utf-8")
            result = subprocess.run(command + ["text-import", str(source), str(edits), "-o", str(output)],
                                    cwd=root, capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(output.exists())
            self.assertEqual(source.read_bytes(), demo_files()["MESSAGE.DAT"])


if __name__ == "__main__":
    unittest.main()
