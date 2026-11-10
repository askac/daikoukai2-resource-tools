# Daikoukai2 Resource Tools

Small tools for inspecting and rebuilding internal resource files used by
Uncharted Waters II / Daikoukai Jidai II, with notes on the original package
architecture and text presentation. This is a local preparation snapshot, not a
complete localization installer or an official release.

For work with the original game, obtain your own legitimate copy from the
[official Steam listing](https://store.steampowered.com/app/628170/).
The tools start with separately prepared **internal game resource files**.
The downloaded Windows package is not a supported input. Preparing those inputs
is outside this project's workflow.

The repository contains Python source, original sample generators and notes.
It does not contain game data, translations, fonts, emulator binaries, disk
images, executable patches, package-unpacking routines or resource decryption.
An extracted local file can contain copyrighted material; exporting it does not
make that output part of this source repository or grant redistribution rights.

## Requirements

Python 3.10 or newer, using only the standard library. No package installation,
game installation, emulator or network connection is needed for the synthetic demo.
On Windows, `py -3` can be used instead of `python`.

## Synthetic demo

Run these commands from the repository directory. Each output path must be new.

```sh
python examples/make_demo.py work/demo
python resource_tool.py text-export work/demo/MESSAGE.DAT --width 2 --kind message -o work/text.json
```

Open `work/text.json` in a UTF-8 editor. Change the first record's `texts` value
from `DEMO ONE` to `EDITED`, leaving indices, schema, layout and source digest
intact. Then rebuild a separate file:

```sh
python resource_tool.py text-import work/demo/MESSAGE.DAT work/text.json -o work/message-edited.dat
```

To extract an indexed image for editing:

```sh
python resource_tool.py image-export work/demo/GRAPHICS.BIN 0 -o work/frame.bmp
python resource_tool.py image-import work/demo/GRAPHICS.BIN 0 work/frame.bmp -o work/graphics-edited.bin
```

BMP output uses a synthetic grayscale palette to show **indices**, not the game's
display colors. Keep its 8-bit indexed format, dimensions, palette and index
ordering when editing. RGB conversion, palette optimization and other BMP
variants are rejected. The importer preserves frame allocation and may reject a
valid-looking edit that cannot fit the original compressed slot.

Internal archives can be inspected and updated by zero-based entry index:

```sh
python resource_tool.py archive-list work/demo/GRAPHICS.LZW
python resource_tool.py archive-extract work/demo/GRAPHICS.LZW 0 -o work/extracted.bin
python resource_tool.py archive-replace work/demo/GRAPHICS.LZW 0 work/graphics-edited.bin -o work/archive-edited.lzw
```

The examples generate original ASCII labels and blank geometric pixel data.
They do not reconstruct or download any original game assets.

## Supported scope

| Input | Operations | Constraints |
| --- | --- | --- |
| Offset-indexed text banks | Export editable UTF-8 JSON; import CP932 text | Preserve record offsets, string counts, control tokens and capacities. |
| Indexed image collections | Export one frame as BMP; import one edited frame | Preserve dimensions, frame slots and all other frame bytes. |
| LW11 / LS10 / LS11 resource archives | List, extract and replace an entry | Preserve offsets, total file length and decompressed entry length; compressed replacement must fit. |

Known text layouts include `MENU.DAT` (`--width 2 --kind menu`), `MESSAGE.DAT`
(`--width 2 --kind message`) and `SNR*.MES` (`--width 4 --kind scenario`). These are
layout selections, not claims of compatibility with every similarly named file.
The tool validates the supplied structure before updating it.

Text import currently supports the resource's existing CP932 encoding. It does
not install new Traditional Chinese glyphs, generate fonts or introduce a custom
character mapping. A successfully encoded character is not proof that a
particular game font can display it. Executable strings, fixed name tables,
save files and runtime hooks are outside this initial scope.

## Output behavior and validation

All commands validate their input and construct the complete result before opening
an output. Existing files are never overwritten, including the input itself.
Writes are flushed and read back; a failed write is reported as an error and its
new partial output is removed. Keep the original input for recovery.

A text document's digest detects edits made against a different source file.
It is not a version whitelist. Format parsing, bounds, counts and reconstruction
checks determine whether the resource can be processed. There is no separate
runtime installer or emulator integration.

```sh
python -B -m unittest discover -s tests -v
```

Tests cover original synthetic fixtures, unchanged reconstruction, scoped edits,
invalid layouts, capacity failures, changed control tokens, stale input,
cross-directory CLI use and output preservation. This does not constitute
in-game, emulator or controller validation.

## Notes and rights

- [Package architecture](docs/architecture.md)
- [Resource formats and update strategy](docs/formats.md)
- [Typography observations](docs/typography.md)
- [Source provenance and licensing status](PROVENANCE.md)

The tools' license has not yet been selected. No open-source license is granted
by this preparation snapshot. This project is not affiliated with or endorsed by
the game's publisher. Names identify the subject of the tooling and observations.
