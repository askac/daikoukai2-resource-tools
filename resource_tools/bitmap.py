"""Exchange palette indices using uncompressed 8-bit BMP files."""

import struct


PALETTE = b"".join(bytes([i * 17] * 3 + [0]) for i in range(16)) + bytes(240 * 4)


def encode_bitmap(width, height, pixels):
    if (not 0 < width <= 640 or not 0 < height <= 400 or len(pixels) != width * height
            or any(value > 15 for value in pixels)):
        raise ValueError("Expected a complete image with indices 0 through 15")
    stride = (width + 3) & ~3
    rows = b"".join(pixels[y * width:(y + 1) * width] + bytes(stride - width)
                    for y in reversed(range(height)))
    offset = 14 + 40 + len(PALETTE)
    header = struct.pack("<2sIHHI", b"BM", offset + len(rows), 0, 0, offset)
    info = struct.pack("<IiiHHIIiiII", 40, width, height, 1, 8, 0, len(rows), 0, 0, 256, 0)
    return header + info + PALETTE + rows


def decode_bitmap(data):
    if len(data) < 1078 or data[:2] != b"BM":
        raise ValueError("Expected an uncompressed 8-bit indexed BMP")
    total, _, _, offset = struct.unpack_from("<IHHI", data, 2)
    size, width, height, planes, bits, compression, image_size, _, _, colors, _ = struct.unpack_from(
        "<IiiHHIIiiII", data, 14)
    if (size != 40 or planes != 1 or bits != 8 or compression != 0 or colors not in (0, 256)
            or not 0 < width <= 640 or not 0 < abs(height) <= 400 or offset != 1078
            or data[54:1078] != PALETTE):
        raise ValueError("Keep the exported BMP dimensions, 8-bit format and index palette")
    stride = (width + 3) & ~3
    payload_size = stride * abs(height)
    if total != len(data) or offset + payload_size != len(data) or image_size not in (0, payload_size):
        raise ValueError("Invalid BMP pixel bounds")
    rows = [data[offset + y * stride:offset + y * stride + width] for y in range(abs(height))]
    pixels = b"".join(reversed(rows) if height > 0 else rows)
    if any(value > 15 for value in pixels):
        raise ValueError("BMP uses indices outside 0 through 15")
    return width, abs(height), pixels
