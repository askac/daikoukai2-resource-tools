#!/usr/bin/env python3
"""Inspect, export and update user-supplied internal game resources."""

import argparse
import json
import os
from pathlib import Path
import struct

from resource_tools.archives import extract_entry, read_archive, replace_entry
from resource_tools.bitmap import decode_bitmap, encode_bitmap
from resource_tools.images import export_image, import_image
from resource_tools.text_banks import export_text, import_text


MAX_INPUT_BYTES = 64 * 1024 * 1024


def read_input(path):
    with path.open("rb") as handle:
        data = handle.read(MAX_INPUT_BYTES + 1)
    if len(data) > MAX_INPUT_BYTES:
        raise ValueError("Input exceeds the supported resource size")
    return data


def write_new(path, data):
    """Never overwrite an existing path, including an input file or symlink."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x+b") as handle:
        try:
            if handle.write(data) != len(data):
                raise OSError("Incomplete output write")
            handle.flush()
            os.fsync(handle.fileno())
            handle.seek(0)
            if handle.read() != data:
                raise OSError("Output readback differs")
        except BaseException:
            handle.close()
            path.unlink()
            raise


def execute(args):
    data = read_input(args.source)
    if args.command == "archive-list":
        print(json.dumps(read_archive(data), indent=2, ensure_ascii=True))
        return
    if args.command == "text-export":
        document = export_text(data, args.width, args.kind)
        output = (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    elif args.command == "text-import":
        document = json.loads(read_input(args.edits).decode("utf-8-sig"))
        output = import_text(data, document)
    elif args.command == "image-export":
        output = encode_bitmap(*export_image(data, args.index))
    elif args.command == "image-import":
        output = import_image(data, args.index, *decode_bitmap(read_input(args.edits)))
    elif args.command == "archive-extract":
        output = extract_entry(data, args.index)
    elif args.command == "archive-replace":
        output = replace_entry(data, args.index, read_input(args.edits))
    else:
        raise ValueError("Unknown command")
    write_new(args.output, output)
    print(json.dumps({"output": str(args.output), "bytes": len(output), "verified": True}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("text-export", "text-import", "image-export", "image-import",
                 "archive-list", "archive-extract", "archive-replace"):
        command = commands.add_parser(name)
        command.add_argument("source", type=Path)
        if name.startswith(("image-", "archive-")) and name != "archive-list":
            command.add_argument("index", type=int, help="Zero-based entry or frame index")
        if name in ("text-import", "image-import", "archive-replace"):
            command.add_argument("edits", type=Path)
        if name != "archive-list":
            command.add_argument("-o", "--output", type=Path, required=True)
        if name == "text-export":
            command.add_argument("--width", type=int, choices=(2, 4), required=True)
            command.add_argument("--kind", choices=("menu", "message", "scenario"), required=True)
    args = parser.parse_args()
    try:
        execute(args)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, struct.error) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    main()
