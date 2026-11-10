"""Read and encode indexed four-plane resource frames."""

from collections import Counter
import struct


def image_slices(data):
    if len(data) < 4:
        raise ValueError("Truncated image directory")
    size = int.from_bytes(data[:4], "big")
    if size % 4 or not 4 <= size <= min(len(data), 4096):
        raise ValueError("Invalid image directory")
    offsets = struct.unpack_from(">" + "I" * (size // 4), data)
    if offsets[0] != size or list(offsets) != sorted(set(offsets)) or offsets[-1] >= len(data):
        raise ValueError("Invalid image offsets")
    return [(a, b) for a, b in zip(offsets, offsets[1:] + (len(data),))]


def decode_frame(data):
    if len(data) < 20:
        raise ValueError("Truncated frame")
    width, height = struct.unpack_from("<HH", data)
    width &= 0x7fff
    if not 0 < width <= 640 or not 0 < height <= 400:
        raise ValueError("Invalid frame dimensions")
    dictionary = struct.unpack_from("<8H", data, 4)
    stride = (width + 3) // 4
    groups = []
    pos = 20
    def byte():
        nonlocal pos
        if pos >= len(data):
            raise ValueError("Truncated graphics command")
        value = data[pos]
        pos += 1
        return value
    for y in range(height):
        x = 0
        while x < stride:
            op = byte()
            if op & 0x80:
                count = (op & 15) + 1
                distance = ((op >> 4) & 3) + 1
                if op & 0x40:
                    distance *= stride
                if x + count > stride or len(groups) < distance:
                    raise ValueError("Invalid graphics reference")
                for _ in range(count):
                    groups.append(groups[-distance])
            else:
                count, kind = (op & 7) + 1, op & 0x78
                if kind == 0:
                    value = 0
                elif kind & 0x40:
                    value = dictionary[kind >> 3 & 7]
                elif kind == 0x38:
                    value = byte() << 8 | byte()
                else:
                    v = byte()
                    value = {8: v, 16: (v & 15) | (v & 240) << 4,
                             24: (v & 15) | (v & 240) << 8, 32: v << 4,
                             40: (v & 15) << 4 | (v & 240) << 8, 48: v << 8}[kind]
                if x + count > stride:
                    raise ValueError("Graphics command crosses row")
                groups.extend([value] * count)
            x += count
    if pos != len(data):
        raise ValueError("Trailing graphics bytes")
    pixels = bytes(sum((groups[y * stride + x // 4] >> (p * 4 + 3 - x % 4) & 1) << p
                       for p in range(4)) for y in range(height) for x in range(width))
    return width, height, pixels


def encode_frame(pixels, width, height, size, palette_indices=(0, 7), *, compact_literals=False):
    if (not 0 < width <= 640 or not 0 < height <= 400 or width % 4
            or len(pixels) != width * height or set(pixels) - set(palette_indices)
            or set(palette_indices) - set(range(16))):
        raise ValueError("Expected complete four-pixel groups using the allowed palette indices")
    stride = width // 4
    groups = [sum((pixels[i + x] >> plane & 1) << (plane * 4 + 3 - x)
                  for x in range(4) for plane in range(4))
              for i in range(0, len(pixels), 4)]
    counts = Counter(value for value in groups if value)
    dictionary = [value for value, _ in counts.most_common(8)]
    dictionary += [0] * (8 - len(dictionary))
    lookup = {value: i for i, value in reversed(list(enumerate(dictionary)))}
    commands = []
    for row in range(height):
        start = row * stride
        costs, choice = [10**9] * (stride + 1), [None] * stride
        costs[-1] = 0
        for x in reversed(range(stride)):
            i, value = start + x, groups[start + x]
            if value == 0:
                op, payload = 0, b""
            elif value in lookup:
                op, payload = 0x40 | lookup[value] << 3, b""
            else:
                op, payload = 0x38, struct.pack(">H", value)
                if compact_literals:
                    for kind, low, high in ((8, 0, 4), (16, 0, 8), (24, 0, 12),
                                            (32, 4, 8), (40, 4, 12), (48, 8, 12)):
                        if not value & ~(15 << low | 15 << high):
                            op = kind
                            payload = bytes([(value >> low & 15) | (value >> high & 15) << 4])
                            break
            run = 1
            while run < min(8, stride - x) and groups[i + run] == value:
                run += 1
            for count in range(1, run + 1):
                cost = 1 + len(payload) + costs[x + count]
                if cost < costs[x]:
                    costs[x], choice[x] = cost, (count, op, payload)
            for vertical in (False, True):
                for distance_units in range(1, 5):
                    distance = distance_units * (stride if vertical else 1)
                    if i < distance:
                        continue
                    count = 0
                    while count < min(16, stride - x) and groups[i + count] == groups[i + count - distance]:
                        count += 1
                        if 1 + costs[x + count] < costs[x]:
                            base = 0x80 | (0x40 if vertical else 0) | (distance_units - 1) << 4
                            costs[x], choice[x] = 1 + costs[x + count], (count, base, b"")
        x = 0
        while x < stride:
            command = choice[x]
            commands.append(command)
            x += command[0]
    minimum = 20 + sum(1 + len(payload) for _, _, payload in commands)
    extra = 0 if size is None else size - minimum
    if extra < 0:
        raise ValueError(f"Frame does not fit its original slot: {minimum} > {size}")
    output = bytearray(struct.pack("<HH8H", width, height, *dictionary))
    for count, op, payload in commands:
        # Splitting a one-byte run adds exactly one byte without changing pixels.
        split = min(extra, count - 1) if not payload else 0
        output.extend(bytes([op]) * split)
        count -= split
        extra -= split
        output.append(op | count - 1)
        output.extend(payload)
    if extra:
        raise ValueError("Cannot fill the original frame slot without trailing data")
    if (size is not None and len(output) != size) or decode_frame(output) != (width, height, pixels):
        raise ValueError("Encoded frame does not roundtrip")
    return bytes(output), minimum


def export_image(data, index):
    slices = image_slices(data)
    if not 0 <= index < len(slices):
        raise ValueError("Image frame index is out of range")
    start, end = slices[index]
    return decode_frame(data[start:end])


def import_image(data, index, width, height, pixels):
    old_width, old_height, original = export_image(data, index)
    if (width, height) != (old_width, old_height):
        raise ValueError("Replacement image dimensions differ from the source")
    if pixels == original:
        return data
    start, end = image_slices(data)[index]
    encoded, _ = encode_frame(pixels, width, height, end - start, tuple(range(16)),
                              compact_literals=True)
    # Preserve the original dimension flags as well as every directory offset.
    encoded = data[start:start + 4] + encoded[4:]
    output = data[:start] + encoded + data[end:]
    if len(output) != len(data) or export_image(output, index) != (width, height, pixels):
        raise ValueError("Updated image resource failed verification")
    return output
