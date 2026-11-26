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

## Coming from the liblouis Python bindings

The [`louis` module](https://github.com/liblouis/liblouis/blob/master/python/louis/__init__.py.in)
of liblouis takes the tables with every call. The liblouis manual describes it
under [Python bindings](https://liblouis.io/documentation/liblouis/Python-bindings.html).
louis-py compiles the tables once into a `Translator`, which translates in one
direction. Build one with `t = Translator(tables)` and use it for each string.

The liblouis names below are written as if imported with `from louis import ...`.

| liblouis                                        | louis-py                                                                        |
|-------------------------------------------------|---------------------------------------------------------------------------------|
| `translateString(tables, text)`                 | `t.translate(text)`                                                             |
| `translate(tables, text, cursorPos=c)`          | `t.translate_with_options(text, cursor_position=c)`                             |
| `backTranslateString`, `backTranslate`          | the same, with `Translator(tables, Direction.BACKWARD)`                         |
| the tuple from `translate` and `backTranslate`  | the result's `output`, `input_positions`, `output_positions`, `cursor_position` |
| `mode=`                                         | `mode=` with `TranslationMode` members                                          |
| `typeform=`                                     | `emphasis=` with `EmphasisSpan`s                                                |
| the `typeform` list that back-translation fills | the result's `emphasis`                                                         |
| `getTypeformForEmphClass`                       | not needed: a span names its class                                              |
| a display table in the table list               | `braille_encoding=`                                                             |
| `dotsIO`, `ucBrl`                               | not needed: braille is Unicode braille by default                               |
| `checkTable(tables)`                            | `Translator(tables)`                                                            |
| `findTables({"language": "de"})`                | `Index().find({"language": "de"})`                                              |
| `registerLogCallback`, `setLogLevel`            | the `louis` logger in `logging`                                                 |
| `version()`                                     | `LOUIS_RS_VERSION`                                                              |
| `charSize()`                                    | not needed: text is a `str`                                                     |
| the environment variable `LOUIS_TABLEPATH`      | the environment variable `LOUIS_TABLE_PATH`, or `search_path=`                  |

Each liblouis mode except `dotsIO` and `ucBrl` has a `TranslationMode` member,
such as `COMPBRL_AT_CURSOR` for `compbrlAtCursor`. Combine members with `|`.

A typeform has a bit per emphasis class. `emph_1` is the first class in
`t.emphasis_classes`, `emph_2` the second, and so on.

`Index().find` returns the paths of the tables that carry every pair of the
query, sorted by path. `find` also takes a string, such as `"language:de"`.
louis-rs does not rank partial matches yet, so `findTable` has no
counterpart.

Building a `Translator` raises `TableParseError` or `TableCompileError` where
liblouis raises `RuntimeError`. Both derive from `LouisError`, so
`except RuntimeError` does not catch them.

`LOUIS_TABLEPATH` separates its directories with commas. `LOUIS_TABLE_PATH`
separates them like `PATH`. Without `LOUIS_TABLE_PATH` or `search_path=`,
louis-py looks for tables in the current directory.

louis-py has no counterpart for:

- `hyphenate`, `charToDots` and `dotsToChar`
- `compileString`
- `getTableInfo` and `listTables`
- the `no_translate` and `no_contract` typeforms
