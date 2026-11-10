"""Read and update offset-indexed CP932 text resources."""

import hashlib
import re


CONTROL = re.compile(r"\x1b[A-Za-z][0-9]+|%[-+ #0]*\d*(?:\.\d+)?[lh]?[a-zA-Z]|"
                     r"\$(?:[ns]|[dr]\d{2})|[\x01-\x09\x0b-\x1f]|\u00a7")


def read_bank(data, width, kind):
    if width not in (2, 4) or kind not in ("menu", "message", "scenario"):
        raise ValueError("Unsupported text-bank layout")
    if len(data) < width:
        raise ValueError("Truncated offset table")
    table_size = int.from_bytes(data[:width], "big")
    if not width <= table_size <= len(data) or table_size % width:
        raise ValueError("Invalid offset table size")
    offsets = [int.from_bytes(data[i:i + width], "big")
               for i in range(0, table_size, width)]
    if any(a >= b for a, b in zip(offsets, offsets[1:])):
        raise ValueError("Offsets must be strictly increasing")
    if any(not table_size <= offset < len(data) for offset in offsets):
        raise ValueError("Offset outside payload")
    records = []
    for index, (start, end) in enumerate(zip(offsets, offsets[1:] + [len(data)])):
        block = data[start:end]
        prefix = block[:2] if kind == "menu" else b""
        if kind == "menu" and len(prefix) != 2:
            raise ValueError("Truncated menu header")
        count = prefix[1] if prefix else 1
        position = len(prefix)
        texts = []
        for _ in range(count):
            terminator = block.find(b"\x00", position)
            if terminator < 0:
                raise ValueError("Missing string terminator")
            texts.append(block[position:terminator].decode("cp932"))
            position = terminator + 1
        padding = block[position:]
        if any(padding):
            raise ValueError("Unclassified nonzero bytes after strings")
        records.append({
            "index": index, "source_offset": start, "source_size": len(block),
            "prefix_hex": prefix.hex(), "source_texts": texts,
            "padding_hex": padding.hex(),
        })
    return {"offset_width": width, "kind": kind, "records": records}


def rebuild_bank(bank):
    width = bank["offset_width"]
    payload = bytearray()
    table = bytearray()
    table_size = len(bank["records"]) * width
    for record in bank["records"]:
        table.extend((table_size + len(payload)).to_bytes(width, "big"))
        payload.extend(bytes.fromhex(record["prefix_hex"]))
        for value in record["source_texts"]:
            payload.extend(value.encode("cp932") + b"\x00")
        payload.extend(bytes.fromhex(record["padding_hex"]))
    return bytes(table + payload)


def export_text(data, width, kind):
    bank = read_bank(data, width, kind)
    if rebuild_bank(bank) != data:
        raise ValueError("Text resource cannot be reconstructed without changes")
    return {
        "schema": "pc98-text-v1", "source_sha256": hashlib.sha256(data).hexdigest(),
        "offset_width": width, "kind": kind,
        "records": [{"index": record["index"], "texts": record["source_texts"]}
                    for record in bank["records"]],
    }


def import_text(data, document):
    if document.get("schema") != "pc98-text-v1":
        raise ValueError("Unsupported text document schema")
    if document.get("source_sha256") != hashlib.sha256(data).hexdigest():
        raise ValueError("Source changed after export; export it again before editing")
    bank = read_bank(data, document["offset_width"], document["kind"])
    if rebuild_bank(bank) != data:
        raise ValueError("Text resource cannot be reconstructed without changes")
    edits = document["records"]
    if not isinstance(edits, list) or len(edits) != len(bank["records"]):
        raise ValueError("Text record count changed")
    output = bytearray(data)
    for old, edit in zip(bank["records"], edits):
        texts = edit["texts"]
        if (type(edit["index"]) is not int or edit["index"] != old["index"]
                or not isinstance(texts, list) or len(texts) != len(old["source_texts"])):
            raise ValueError("Text record index or string count changed")
        block = bytearray.fromhex(old["prefix_hex"])
        for original, text in zip(old["source_texts"], texts):
            if not isinstance(text, str) or "\0" in text:
                raise ValueError("Expected a string without embedded NUL")
            if CONTROL.findall(original) != CONTROL.findall(text):
                raise ValueError(f"Control tokens changed in record {old['index']}")
            encoded = text.encode("cp932")
            if bank["kind"] == "menu" and len(encoded) > block[0]:
                raise ValueError(f"Menu text exceeds its declared width in record {old['index']}")
            block.extend(encoded + b"\0")
        if len(block) > old["source_size"]:
            raise ValueError(f"Text exceeds the original capacity in record {old['index']}")
        start = old["source_offset"]
        output[start:start + old["source_size"]] = block.ljust(old["source_size"], b"\0")
    output = bytes(output)
    checked = read_bank(output, bank["offset_width"], bank["kind"])
    if (len(output) != len(data) or [r["source_texts"] for r in checked["records"]]
            != [r["texts"] for r in edits]):
        raise ValueError("Updated text resource failed verification")
    return output
