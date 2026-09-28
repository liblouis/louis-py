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
r = t.translate_with_options("Hello", cursor_pos=1)
r.output  # the braille text
r.output_positions  # for each input character, the index of its braille cell
r.input_positions  # for each braille cell, the index of its input character
r.cursor_pos  # index in r.output of the cursor passed in
```

Table names and their `include` lines are looked up in the directories given as
`search_path=`, in order, or in `LOUIS_TABLE_PATH` when it is omitted. Nothing
else is searched, so a host that manages its own table directories lists them
all:

```python
t = Translator(["en-ueb-g2.ctb"], search_path=[nvda_tables, addon_tables])
```

See `python/louis_py/_louis_py.pyi` for the full API.

## Releasing

1. Run `cargo release <level> --execute`, where `<level>` is `patch`, `minor`
   or `major`. Without `--execute` it only shows what it would do. It raises
   the version in `Cargo.toml`, dates the `[Unreleased]` section of the
   changelog, commits, tags `vX.Y.Z` and pushes. It does not publish to
   crates.io.
2. Publish a GitHub Release for the new tag. The `python-wheels` workflow then
   uploads the wheels and the sdist to PyPI.
