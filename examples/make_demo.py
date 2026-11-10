#!/usr/bin/env python3
"""Create small, original sample resources without any game installation."""

from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from resource_tool import write_new
from resource_tools.archives import encode_stream


def demo_files():
    blocks = [b"DEMO ONE\0" + bytes(16), b"VALUE %02d\0" + bytes(16)]
    message = struct.pack(">HH", 4, 4 + len(blocks[0])) + b"".join(blocks)
    frame = struct.pack("<HH8H", 8, 4, *([0] * 8)) + bytes(8)
    graphics = struct.pack(">II", 8, 8 + len(frame)) + frame + frame
    dictionary = bytes(range(256))
    compressed = encode_stream(graphics, dictionary) + bytes(64)
    archive = b"LS11" + bytes(12) + dictionary
    archive += struct.pack(">III", len(compressed), len(graphics), 288) + bytes(4) + compressed
    return {"MESSAGE.DAT": message, "GRAPHICS.BIN": graphics, "GRAPHICS.LZW": archive}


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python examples/make_demo.py OUTPUT_DIRECTORY")
    output = Path(sys.argv[1])
    output.mkdir(parents=True, exist_ok=False)
    for name, data in demo_files().items():
        write_new(output / name, data)
    print(f"Created original demo resources in {output}")


if __name__ == "__main__":
    main()
