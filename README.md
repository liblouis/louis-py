# louis-py

Python bindings for [louis-rs](https://github.com/liblouis/louis-rs), a
pure-Rust braille translator.

louis-py needs Python 3.11 or newer. Install it from PyPI:

```
pip install louis-py
```

Or add it to an uv-managed project:

```
uv add louis-py
```

louis-py comes without tables. Point `LOUIS_TABLE_PATH` at a set of tables,
such as the `tables` directory of [liblouis](https://github.com/liblouis/liblouis),
and translate something:

```python
from louis_py import Translator, Direction

t = Translator(["en-us-g1.ctb"], Direction.FORWARD)
print(t.translate("hello world"))  # ⠓⠑⠇⠇⠕⠀⠺⠕⠗⠇⠙
```

`translate_with_options` also reports where each character ended up:

```python
r = t.translate_with_options("Hello", cursor_position=1)
r.output  # the braille text
r.output_positions  # for each input character, the index of its braille cell
r.input_positions  # for each braille cell, the index of its input character
r.cursor_position  # index in r.output of the cursor passed in
```

It also takes translation modes, such as showing the word at the cursor in
computer braille:

```python
from louis_py import TranslationMode

r = t.translate_with_options(
    "hello world", mode=TranslationMode.COMPBRL_AT_CURSOR, cursor_position=1
)
```

Emphasis goes in as `(class, start, end)` spans over the input.
Back-translation returns the emphasis its braille indicates in the same form.
`t.emphasis_classes` lists the class names the tables declare:

```python
from louis_py import EmphasisSpan

t.emphasis_classes  # e.g. ["italic", "underline", "bold"]
t.translate_with_options("Hello", emphasis=[EmphasisSpan("bold", 0, 5)])
```

louis-py looks up table names and their `include` lines in the directories
given as `search_path=`, in order. Without `search_path=`, it uses
`LOUIS_TABLE_PATH`. Nothing else is searched, so a host that manages its own
table directories lists them all:

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

`louis_py.metadata` finds tables by the `#+key: value` metadata they carry. An
`Index` reads the tables on the search path. Its `find` returns the tables that
carry every pair of a query:

```python
from louis_py.metadata import Index

Index().find("language:de grade:2")  # paths of de-g2-detailed.ctb and de-g2.ctb
```

Warnings from louis-rs go to Python's `logging`. For example, louis-rs warns
when it ignores an indicator during back-translation. Each warning goes to the
logger named after its louis-rs module, under `louis`.

`louis_py.LOUIS_RS_VERSION` is the version of louis-rs that louis-py is built
with.

The full API is documented in `python/louis_py/`:

- the classes in `_louis_py.pyi`
- the enums and table errors in `__init__.py`
- the metadata errors in `metadata.py`
