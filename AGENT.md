# Agent working agreement

English | [繁體中文（台灣）](AGENT.zh-TW.md)

These instructions apply to this standalone resource-tools repository. Read
`README.md` and `PROVENANCE.md` before changing its scope or distribution contents.
Follow the user's current instructions when they explicitly change a boundary;
do not infer expanded scope from the availability of neighboring research files.

## Collaboration and implementation

- Reply to the maintainer in Traditional Chinese (Taiwan), unless another language
  is requested. Keep code, comments, identifiers, logs and commit messages in
  English. Maintain public documentation in English and Traditional Chinese
  (Taiwan), using `.zh-TW.md` for translated counterparts and linking each pair.
  Update both versions when behavior or scope changes. Keep command examples,
  paths and schema identifiers unchanged. User-supplied resource text is data,
  not code.
- State important assumptions and give a short plan for multi-step work. Continue
  routine, reversible work within the authorized task without repeated approval.
- Make the smallest necessary change. Preserve existing CLI commands and JSON
  schemas unless the requested behavior requires a documented change.
- Keep this repository self-contained. Do not import code or require data from a
  parent directory, private research repository or machine-specific installation.
- Prefer the Python standard library. Never install dependencies into system
  Python; use a repository-local virtual environment if dependencies become
  necessary. Keep generated files in ignored working directories.
- Treat names, labels and extracted text as data. Select entries by structured
  indices and validated metadata, not by matching displayed prose.

## Public scope

- Inputs are separately prepared internal game resource files. The supported
  work is text/image export, manual editing and resource reconstruction.
- Keep Steam package unpacking, 98E resource decryption, executable patching,
  disk-image construction, emulator integration and save editing outside this
  repository. Do not add instructions or bundled utilities for obtaining inputs.
- Do not copy the private framework wholesale or leave excluded implementations
  present as commented-out code. Select only the format logic needed by this repo.
- Keep original game files, complete translations, emulator binaries, fonts,
  reusable glyph bitmaps, screenshots and credentials out of source and history.
  Use original synthetic fixtures or clearly labeled placeholders for examples.
- Do not access private credentials or download game assets for tests. An ignored
  local asset must not become a committed fixture or an encoded source-code blob.
- Text editing currently uses CP932. Do not silently add glyph mappings, replace
  unencodable characters or claim complete Traditional Chinese localization.

## Resource integrity

- Determine compatibility from actual headers, tables, bounds and codec behavior.
  File names and extensions alone are insufficient. Hashes identify source data
  and detect stale edits; they do not replace structural compatibility checks.
- Validate all prerequisites and construct the result before opening an output.
  Reject unsupported or ambiguous layouts with a useful error; do not guess an
  offset, silently truncate content or discard unclassified data.
- Preserve text record offsets, counts, control tokens and allocation limits.
  For images, preserve dimensions, dimension flags, frame allocation and other
  frames. For archives, preserve offsets, total size and decompressed entry length.
- Preserve palette indices during BMP exchange. The generated grayscale palette
  is an index visualization, not an original game palette or a color-accurate preview.
- Write only to a new output path. Refuse existing paths, including input aliases.
  Verify writes by readback and report failures accurately. Remove only partial
  outputs created by the failed operation; retain the original input for recovery.
- Do not broaden format acceptance by disabling validation. If a new layout is
  needed, establish its structure and add a focused test for it first.

## Validation

Run relevant checks from this repository's root. The current test command is:

```sh
python -B -m unittest discover -s tests -v
```

- For codec or output changes, cover unchanged reconstruction, the requested edit,
  preservation of unrelated data, invalid inputs and applicable capacity failures.
- Keep fixtures original and small. Use `examples/make_demo.py` for an independent
  demo; the test suite must work without the game or the private workspace.
- Verify CLI changes from a different working directory when path behavior changes.
- For documentation-only changes, check paths, examples and consistency; do not
  rerun unrelated gameplay or create tests that merely repeat the documentation.
- Report exactly what ran and any remaining gaps. Format roundtrips and successful
  writes are not proof of in-game behavior, font coverage or emulator compatibility.

## Documentation and provenance

- Separate observed package structure, verified tool behavior and hypotheses.
  Do not present another possible use of 98E as a tested capability.
- Explain Steam package architecture at the component level. Keep the documented
  resource-editor input boundary consistent with the actual implementation.
- Discuss typography using family-level terms such as Ming-style serif and
  Hei-style sans-serif. Describe size, weight, spacing and legibility without
  adding specific font vendor or product names to visual-experience notes.
- Record implementation provenance in `PROVENANCE.md` when selecting or adapting
  code. Keep the official purchase reference and accurately describe prerequisites.
- Do not claim legal clearance, zero risk or permission to redistribute assets
  based on a disclaimer, the documentation language or an absence of known cases.

## Git and publication

- Operate on this repository's Git root, not the surrounding research repository.
  Stage explicit intended files and inspect the staged diff. Ignore rules are not
  a substitute for checking file contents and history before publication.
- Use an imperative English commit subject of at most 60 characters. Add a body
  only when needed to explain the behavior, scope and meaningful validation.
- The original tool source, documentation and synthetic examples use the MIT
  License in `LICENSE`. Preserve its copyright and permission notices. Changes to
  licensing require the owner's decision; this license does not cover third-party
  game content, translations, fonts or emulator software.
- Creating or editing local files does not authorize a remote, push or release.
  Follow an explicit publication request; do not ask again for already authorized
  steps within that request.
- Before a formal release, commit the complete source, necessary scripts and
  configuration templates corresponding to the delivered output. Identify the
  release and version in the commit message; distinguish a local preparation
  snapshot from a formal release.
