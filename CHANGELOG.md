# Changelog

All notable changes to louis-py are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This changelog covers the Python bindings only. Changes to translation itself
are listed in the
[louis-rs changelog](https://github.com/liblouis/louis-rs/blob/main/CHANGELOG.md).
Each release names the louis-rs version it is built on.

<!-- next-header -->

## [Unreleased] - ReleaseDate

This is the first release of louis-py, the Python bindings for the
[louis-rs](https://github.com/liblouis/louis-rs) braille translator. It is
built on louis-rs 0.4.1.

### Added

- `Translator`, whose `translate` and `translate_with_options` release the GIL.
- `search_path=` on `Translator` lists the directories in which table names
  and their `include` lines are looked up, in order. The default, `None`,
  reads `LOUIS_TABLE_PATH`. A host that manages its own table directories
  passes them here. It does not have to change the environment variable
  around every constructor call. Only the listed directories are searched. A
  table's own directory counts only when it is listed. An absolute table name
  resolves against any non-empty search path.
- `Translator.from_table_source(table, direction=Direction.FORWARD)` builds a
  translator from raw table source text held in memory. It does not resolve
  `include` lines. Table text that contains one raises `TableParseError`.
- `BrailleEncoding` sets which characters stand for the braille cells, such as
  ASCII braille. It loads a liblouis display table (`.dis`) by name, with the
  same `search_path=` lookup as `Translator`.
  `BrailleEncoding.from_table_source` loads one from table source text
  instead. Pass the encoding as `braille_encoding=` to `Translator` or
  `Translator.from_table_source`. Without one, braille is Unicode braille.
- `Direction` (`enum.Enum`) and `TranslationMode` (`enum.Flag`).
  `Translator.translate_with_options` takes the modes as `mode=`:
  - `COMPBRL_AT_CURSOR` shows the word at the cursor uncontracted, in computer
    braille. `COMPBRL_LEFT_CURSOR` does this for the part of that word before
    the cursor.
  - `NO_CONTRACTIONS` translates without contractions.
  - `NO_UNDEFINED` drops characters and cells that the tables do not define.
  - `PARTIAL_TRANS` back-translates braille that may end in the middle of a
    word, such as the cells typed so far.
- The `TranslationResult` and `EmphasisSpan` result types.
- `emphasis=` on `Translator.translate_with_options` takes
  `(class, start, end)` spans over the input, such as `EmphasisSpan`s. A class
  the tables do not declare is ignored. Back-translation returns the emphasis
  the braille indicates in `TranslationResult.emphasis`. The spans are sorted
  by class, then by start. After forward translation, `emphasis` is `None`.
- `Translator.emphasis_classes` lists the emphasis classes the tables declare
  with `emphclass`, in declaration order.
- The `TranslationResult` from `Translator.translate_with_options` maps
  positions between input and output. Both mappings count characters, so they
  index the input and output strings directly.
  - `output_positions[i]` is the index of the braille cell that input
    character `i` translated to.
  - `input_positions[j]` is the index of the input character that braille cell
    `j` came from.
  - `cursor_position` is the translated position of the cursor passed as
    `cursor_position=`. It is `None` when no cursor is passed. A cursor past
    the end of the input maps past the end of the output.
- `louis_py.metadata` finds tables by the `#+key: value` metadata they carry.
  `Index` reads the tables on `search_path=`, or on `LOUIS_TABLE_PATH` when
  none is given. `Index.find` returns the tables that carry every pair of a
  query, sorted by path. A query is a `Query`, a string such as
  `"language:de grade:2"`, or `(key, value)` pairs. `MetadataError` has two
  subclasses:
  - `InvalidQueryError` is also a `ValueError`. Its `pair` is the part that is
    not `key:value`.
  - `MetadataIOError` is also an `OSError`. It is raised when a directory
    cannot be read.
- `LouisError` has two subclasses. Translating itself cannot fail.
  - `TableParseError` is raised when a table cannot be found, read or parsed.
  - `TableCompileError` is raised when a rule refers to something no rule
    defines.
- `TableParseError.errors` lists every problem as a `TableError`. Its `kind` is
  a `TableErrorKind`. Where they apply, it also has the table's `path`, the
  `line`, the `paths` of an include cycle, the include `depth` limit and the
  `emphasis_class` of a conflicting `endmodephrase`.
- `TableCompileError.path` and `.line` say where the rule is. `path` is `None`
  for table source given in memory. The error's `kind` is a
  `CompileErrorKind`. Where they apply, it also has the undefined `character`,
  the undefined `base` character with its `derived` one, or the undefined
  `swap_class`.
- Warnings from louis-rs go to Python's `logging`, under the `louis` logger.
- `LOUIS_RS_VERSION` holds the version of louis-rs that louis-py is built with.
- Type stubs (`_louis_py.pyi`) and a `py.typed` marker.
- Built with maturin for `abi3-py311`, so one wheel per platform serves Python
  3.11 and later.

<!-- next-url -->
[Unreleased]: https://github.com/liblouis/louis-py/compare/5ca872bf133effa74e3d2e16b7a4647c8a57a4b4...HEAD
