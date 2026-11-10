"""Inspect and update internal LW11 and LS10/LS11 resource archives."""

from collections import defaultdict, deque
from itertools import islice
import struct


WINDOW_SIZE = 8191
MATCH_CANDIDATES = 64
MAX_ENTRY_BYTES = 16 * 1024 * 1024


def decode_stream(source, dictionary, size, *, zero_history=False):
    if len(dictionary) != 256 or len(set(dictionary)) != 256 or not 0 < size <= MAX_ENTRY_BYTES:
        raise ValueError("Invalid Wyle dictionary or output size")
    position = 0

    def bit():
        nonlocal position
        if position >= len(source) * 8:
            raise ValueError("Truncated Wyle stream")
        value = source[position // 8] >> (7 - position % 8) & 1
        position += 1
        return value

    def code():
        prefix = count = 0
        while True:
            value = bit()
            prefix = prefix << 1 | value
            count += 1
            if count > 16:
                raise ValueError("Oversized Wyle code")
            if not value:
                break
        suffix = 0
        for _ in range(count):
            suffix = suffix << 1 | bit()
        return prefix + suffix

    output = bytearray()
    while len(output) < size:
        value = code()
        if value < 256:
            output.append(dictionary[value])
        else:
            distance, length = value - 256, code() + 3
            if zero_history and distance == 0:
                distance = WINDOW_SIZE + 1
            limit = WINDOW_SIZE + 1 if zero_history else min(WINDOW_SIZE, len(output))
            if not 0 < distance <= limit or len(output) + length > size:
                raise ValueError("Invalid Wyle reference")
            for _ in range(length):
                output.append(output[-distance] if distance <= len(output) else 0)
    return bytes(output)


def encode_stream(data, dictionary):
    data = bytes(data)
    if len(dictionary) != 256 or len(set(dictionary)) != 256:
        raise ValueError("Expected a complete literal dictionary")
    literals = {value: i for i, value in enumerate(dictionary)}
    output, accumulator, bit_count = bytearray(), 0, 0

    def emit(value):
        nonlocal accumulator, bit_count
        count = (value + 2).bit_length() - 1
        prefix = (1 << count) - 2
        accumulator = accumulator << (count * 2) | prefix << count | (value - prefix)
        bit_count += count * 2
        while bit_count >= 8:
            bit_count -= 8
            output.append(accumulator >> bit_count & 255)
        accumulator &= (1 << bit_count) - 1

    def cost(value):
        return 2 * ((value + 2).bit_length() - 1)

    literal_costs = [0]
    for value in data:
        literal_costs.append(literal_costs[-1] + cost(literals[value]))
    matches, pos = defaultdict(deque), 0
    while pos < len(data):
        candidates = matches[data[pos:pos + 3]]
        while candidates and pos - candidates[0] > WINDOW_SIZE:
            candidates.popleft()
        best_length, best_distance, best_gain = 1, 0, 0
        for previous in islice(reversed(candidates), MATCH_CANDIDATES):
            distance = pos - previous
            length = 3
            while pos + length < len(data) and data[pos + length] == data[pos + length - distance]:
                length += 1
            literal_cost = literal_costs[pos + length] - literal_costs[pos]
            gain = literal_cost - cost(distance + 256) - cost(length - 3)
            if gain > best_gain:
                best_length, best_distance, best_gain = length, distance, gain
            if pos + length == len(data):
                break
        if best_distance:
            emit(best_distance + 256)
            emit(best_length - 3)
        else:
            emit(literals[data[pos]])
        for index in range(pos, pos + best_length):
            if index + 3 <= len(data):
                matches[data[index:index + 3]].append(index)
        pos += best_length
    if bit_count:
        output.append(accumulator << (8 - bit_count))
    result = bytes(output)
    if decode_stream(result, dictionary, len(data)) != data:
        raise ValueError("Wyle stream does not roundtrip")
    return result


def read_archive(data):
    if len(data) < 288 or data[:4] not in (b"LW11", b"LS10", b"LS11"):
        raise ValueError("Expected an internal LW11, LS10 or LS11 archive")
    dictionary = data[16:272]
    if len(set(dictionary)) != 256:
        raise ValueError("Invalid archive literal dictionary")
    named = data[:4] == b"LW11"
    row_size = 32 if named else 12
    entries, position = [], 272
    while True:
        if position + 4 > len(data):
            raise ValueError("Missing archive directory terminator")
        if data[position:position + 4] == b"\0" * 4:
            directory_end = position + 4
            break
        if position + row_size > len(data):
            raise ValueError("Truncated archive directory")
        field = position + (16 if named else 0)
        size, unpacked, offset = struct.unpack_from(">III", data, field)
        limit = MAX_ENTRY_BYTES if named else 65535
        if not 0 < size or not 0 < unpacked <= limit or offset + size > len(data):
            raise ValueError("Invalid archive entry bounds")
        name = data[position:position + 16].split(b"\0", 1)[0].decode("cp932") if named else None
        entries.append({"index": len(entries), "name": name, "size": size,
                        "unpacked": unpacked, "offset": offset, "field": field})
        position += row_size
    if not entries:
        raise ValueError("Archive has no entries")
    previous_end = directory_end
    for entry in entries:
        if entry["offset"] < previous_end:
            raise ValueError("Overlapping or unordered archive entries")
        previous_end = entry["offset"] + entry["size"]
    return entries


def extract_entry(data, index):
    entries = read_archive(data)
    if not 0 <= index < len(entries):
        raise ValueError("Archive entry index is out of range")
    entry = entries[index]
    payload = data[entry["offset"]:entry["offset"] + entry["size"]]
    named = data[:4] == b"LW11"
    if named and entry["size"] == entry["unpacked"]:
        return payload
    return decode_stream(payload, data[16:272], entry["unpacked"], zero_history=named)


def replace_entry(data, index, replacement):
    original = extract_entry(data, index)
    entry = read_archive(data)[index]
    if len(replacement) != len(original):
        raise ValueError("Replacement must retain the decompressed entry length")
    if replacement == original:
        return data
    payload = encode_stream(replacement, data[16:272])
    if data[:4] == b"LW11" and len(payload) >= len(replacement):
        payload = replacement
    if len(payload) > entry["size"]:
        raise ValueError("Replacement exceeds the original archive allocation")
    output = bytearray(data)
    struct.pack_into(">I", output, entry["field"], len(payload))
    output[entry["offset"]:entry["offset"] + len(payload)] = payload
    output = bytes(output)
    if len(output) != len(data) or extract_entry(output, index) != replacement:
        raise ValueError("Updated archive failed verification")
    return output
