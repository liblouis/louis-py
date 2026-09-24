# Changelog

All notable changes to louis-py are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This changelog covers the Python bindings only. Changes to translation itself
are listed in the
[louis-rs changelog](https://github.com/liblouis/louis-rs/blob/main/CHANGELOG.md).

## [Unreleased]

First release of louis-py, Python bindings for the
[louis-rs](https://github.com/liblouis/louis-rs) braille translator, built on
louis-rs 0.3.0 from crates.io.

### Added

- `Translator` with GIL-released `translate` / `translate_with_options`.
- `search_path=` keyword on `Translator`: the directories, in order, in which
  table names and their `include` lines are looked up. `None` (the default)
  reads `LOUIS_TABLE_PATH`. A host that manages its own table directories
  passes them here instead of mutating the environment variable around every
  constructor call. Nothing beyond the given list is searched: a table's own
  directory only when listed, and an absolute table name resolves against any
  non-empty search path.
- `Translator.from_table_source(table, direction=Direction.FORWARD)`: build a
  translator from raw table source text held in memory. Does not resolve
  `include` directives; table text containing one raises `TableParseError`.
- `Direction` enum and `TranslationMode` flags (`enum.IntFlag`).
- `TranslationResult` and `EmphasisSpan` result types.
- Position mapping on `TranslationResult`, filled in by
  `Translator.translate_with_options`. `output_positions[i]` is the index of
  the braille cell that the input character at index `i` translated to, and
  `input_positions[j]` is the index of the input character that the braille
  cell at index `j` came from. Both count characters, so they index the input
  and output strings directly. `cursor_pos` holds the translated position of
  the cursor passed as `cursor_pos=`, and stays `None` when none is passed; a
  cursor past the end of the input maps past the end of the output.
- Exception hierarchy: `LouisError`, `TableParseError`, `TranslationError`.
- Type stubs (`_louis_py.pyi`) and `py.typed` marker.
- Built with maturin, `abi3-py311` (single wheel for Python 3.11+).
