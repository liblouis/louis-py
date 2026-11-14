# louis-py

Python bindings for [louis](https://github.com/liblouis/louis-rs), a pure-Rust
braille translator.

```python
from louis_py import Translator, Direction

t = Translator(["en-us-g1.ctb"], Direction.FORWARD)
print(t.translate("hello world"))  # ⠓⠑⠇⠇⠕⠀⠺⠕⠗⠇⠙
```

`translate_with_options` additionally reports where every character ended up:

```python
r = t.translate_with_options("Hello", cursor_position=1)
r.output  # the braille text
r.output_positions  # for each input character, the index of its braille cell
r.input_positions  # for each braille cell, the index of its input character
r.cursor_position  # index in r.output of the cursor passed in
```

It also takes liblouis's translation modes, such as showing the word at the
cursor in computer braille:

```python
from louis_py import TranslationMode

r = t.translate_with_options(
    "hello world", mode=TranslationMode.COMPBRL_AT_CURSOR, cursor_position=1
)
```

Emphasis is passed as `(class, start, end)` spans over the input, and
back-translation returns the emphasis its braille indicates the same way.
`t.emphasis_classes` lists the class names the tables declare:

```python
from louis_py import EmphasisSpan

t.emphasis_classes  # e.g. ["italic", "underline", "bold"]
t.translate_with_options("Hello", emphasis=[EmphasisSpan("bold", 0, 5)])
```

Table names and their `include` lines are looked up in the directories given as
`search_path=`, in order, or in `LOUIS_TABLE_PATH` when it is omitted. Nothing
else is searched, so a host that manages its own table directories lists them
all:

```python
t = Translator(["en-ueb-g2.ctb"], search_path=[nvda_tables, addon_tables])
```

Braille is read and written as Unicode braille. To use other characters for
the cells, such as ASCII braille, load a liblouis display table as a
`BrailleEncoding` and pass it to the translator:

```python
from louis_py import BrailleEncoding

brf = BrailleEncoding("en-us-brf.dis")
t = Translator(["en-us-g2.ctb"], braille_encoding=brf)
t.translate("the")  # "!"
```

Warnings from louis-rs, such as an indicator it ignores when back-translating,
go to Python's `logging`, to loggers named after the louis-rs module, under
`louis`.

See `python/louis_py/_louis_py.pyi` for the full API.

## Releasing

1. Run `cargo release <level> --execute`, where `<level>` is `patch`, `minor`
   or `major`. Without `--execute` it only shows what it would do. It raises
   the version in `Cargo.toml`, dates the `[Unreleased]` section of the
   changelog, commits, tags `vX.Y.Z` and pushes. It does not publish to
   crates.io.
2. Publish a GitHub Release for the new tag. The `python-wheels` workflow then
   uploads the wheels and the sdist to PyPI.
