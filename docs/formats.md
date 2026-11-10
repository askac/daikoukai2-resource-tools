# Resource formats and update strategy

The supported formats are internal game resources. File extensions alone do not
identify a compatible layout. A file with unexpected headers, bounds or content
is rejected before an output is written.

## Text banks

A big-endian offset table precedes the records. Its first offset also gives the
table length. Offsets must increase strictly and point inside the file. The CLI
requires the offset width and record kind explicitly.

Message and scenario records contain one NUL-terminated CP932 string followed by
zero padding. Menu records begin with two bytes: declared string width and string
count, followed by the corresponding NUL-terminated strings and zero padding.
Unclassified nonzero bytes are not silently discarded.

Exported JSON preserves record identity and a digest of the supplied source.
Edit only the `texts` arrays. Import reparses the original source, verifies that
it still matches the export, checks string count and known control tokens, then
writes each edited record within its existing allocation. No offset moves.

An unencodable character is an error. This first toolkit does not include a
replacement character map or a font-generation workflow. A fuller localization
workflow would need those separate inputs and appropriate font rights.

## Image collections

A big-endian four-byte offset table points to frames. Each frame includes
dimensions, a small word dictionary and row-oriented compressed four-plane pixel
data. The current codec accepts dimensions up to 640 by 400. Changed frames must
have widths divisible by four for the available encoder.

BMP exchange preserves the 0-15 color indices. Its grayscale palette is generated
mathematically; it is not the game's palette. The importer accepts uncompressed
8-bit Windows BMP with a 40-byte information header and the exported 256-entry
palette. Image editors must preserve that format and palette ordering.

An unchanged frame retains its original encoded bytes. A changed frame is encoded
into exactly its original slot. If the encoder cannot fit or fill that slot,
the update fails. Frame offsets, dimension flags and unrelated frames are kept.
Pixels outside a manually edited area are the editor's responsibility; the tool
preserves other frames, not an inferred text region inside the selected frame.

## Internal archives

LW11 has named entries; LS10 and LS11 have indexed entries. Their headers include
a 256-byte literal dictionary and a directory of compressed lengths, decompressed
lengths and offsets. Compressed entries use a Wyle-coded LZSS stream. LW11 also
supports raw entries when the compressed and decompressed lengths are equal.
Compression is a file-format operation in these codecs; no key input or outer
package decryption is implemented.

The directory is checked for bounds, ordering and overlaps. Archive names are
displayed as metadata and are never used to construct output paths. Users select
an entry by index and supply the output path themselves.

Replacement data must retain its decompressed length. The encoded replacement
must fit the old compressed allocation. Only its compressed-length field and
payload are updated. Unreferenced trailing bytes remain untouched, so the file
length and every other entry offset remain stable. Subsequent decoding verifies
the selected result before writing.

## Limits of verification

Successful format validation and readback show that the tool performed its stated
resource operation. They do not prove that modified text fits a runtime window,
that a font has a desired glyph, or that a particular game path will behave
correctly. This is a resource editor, not a game installer.
