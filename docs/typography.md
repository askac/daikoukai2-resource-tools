# Typography observations

Small bitmap text depends on more than the nominal font size. The useful
comparison is the visible ink inside a fixed cell and its relationship to nearby
labels and borders.

## Ming-style serif and Hei-style sans-serif families

A Ming-style serif face can have pronounced differences between thin and thick
strokes. At small raster sizes, thin strokes may become faint or disappear,
while its proportions can suit a traditional presentation. A Hei-style sans-serif
face often has more even strokes; a heavy weight can still close small counters
or merge neighboring strokes. These are tendencies, not a ranking of all faces
within either family.

For a useful comparison, keep the text, cell dimensions, foreground, background
and rendering conditions constant. Look at:

- Visible height and width, not just the requested point or pixel size.
- Distinction between dense characters and preservation of open spaces.
- Baseline alignment, punctuation placement and spacing between characters.
- Contrast and legibility against the actual background.
- Balance with adjacent labels and the original occupied area.

A nominally equal size can produce a smaller-looking subtitle. A modest size or
position adjustment may improve balance, but should be checked against clipping
and the available resource capacity. Enlarging a finished bitmap changes its
presentation size, not the detail available in the original character raster.

This note intentionally discusses family-level visual properties rather than
specific vendors or installed font names. It includes no font files, reusable
glyph bitmaps or game screenshots. Actual font conversion, embedding and
redistribution permissions depend on the selected font's license; visual
observations do not provide those permissions.
