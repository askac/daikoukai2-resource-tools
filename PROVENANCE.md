# Source provenance and licensing status

English | [繁體中文（台灣）](PROVENANCE.zh-TW.md)

This standalone repository was assembled on 2026-11-10 from locally developed
resource-format tooling. It starts a new Git history and has no runtime dependency
on the research workspace from which the format algorithms were selected.

| Module | Origin of the selected logic |
| --- | --- |
| `resource_tools/text_banks.py` | Offset-table reading and reconstruction from `catalog_localization.py`; fixed-allocation update checks adapted from `build_localization_poc.py`. |
| `resource_tools/images.py` | Frame indexing, decoding and encoding from `ending_cards.py`. |
| `resource_tools/archives.py` | Wyle stream codec from `opening_cards.py`; directory and raw-entry handling informed by `build_hdd.py`. |
| `resource_tools/bitmap.py` | New standard-library BMP exchange for synthetic index colors. |
| `resource_tool.py`, examples and tests | New standalone CLI, original fixtures and verification. |

Only the listed resource-format logic was selected. The source files were not
copied wholesale: host operations, decryption, executable patches, title-specific
translation data, glyph data and source-version hash constants were not included.
The implementation's source reference is research commit `e9fb138`; that private
history is not embedded in this repository.

The demo labels and pixel fixtures are newly constructed examples. Numeric
format markers, codec constants and control-token syntax describe the supported
formats; they are not a bundled original resource.

## License

The original tool source, documentation and synthetic examples are licensed under
the [MIT License](LICENSE), selected by the owner on 2026-11-10. This license does
not confer rights in third-party software, game content, translations or fonts.

No complete third-party dependency is vendored. The implementation uses Python's
standard library. This provenance inventory is not an independent legal opinion
or a forensic proof of authorship.
