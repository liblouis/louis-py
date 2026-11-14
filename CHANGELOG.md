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

First release of louis-py, Python bindings for the
[louis-rs](https://github.com/liblouis/louis-rs) braille translator, built on
louis-rs 0.3.1 with the later changes on its main branch, up to commit
[86ef185](https://github.com/liblouis/louis-rs/commit/86ef185acd6232dab184c9cb1195152558a5a7a0).
louis-py needs APIs that no louis-rs release has yet.

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
- `BrailleEncoding`: which characters stand for the braille cells, such as
  ASCII braille, loaded from a liblouis display table (`.dis`) by name, with
  the same `search_path=` lookup as `Translator`, or with
  `BrailleEncoding.from_table_source`. Pass it as `braille_encoding=` to
  `Translator` or `Translator.from_table_source`; without one, braille is
  Unicode braille. Unlike liblouis, a display table in the table list is not
  used.
- `Direction` (`enum.Enum`) and `TranslationMode` (`enum.Flag`), passed to
  `Translator.translate_with_options` as `mode=`. `COMPBRL_AT_CURSOR` and
  `COMPBRL_LEFT_CURSOR` show the word at the cursor, or its part before the
  cursor, uncontracted in computer braille. `NO_CONTRACTIONS` translates
  without contractions. `NO_UNDEFINED` drops characters and cells the tables
  do not define. `PARTIAL_TRANS` back-translates braille that may end in the
  middle of a word, such as the cells typed so far.
- `TranslationResult` and `EmphasisSpan` result types.
- Emphasis: `emphasis=` on `Translator.translate_with_options` takes
  `(class, start, end)` spans over the input, such as `EmphasisSpan`s; a class
  the tables do not declare is ignored. Back-translation returns the emphasis
  the braille indicates in `TranslationResult.emphasis`, like liblouis's
  typeform output, sorted by class and then by start; forward it is `None`.
- `Translator.emphasis_classes`: the emphasis classes the tables declare with
  `emphclass`, in declaration order, like liblouis's `lou_getEmphClasses`.
- Position mapping on `TranslationResult`, returned by
  `Translator.translate_with_options`. `output_positions[i]` is the index of
  the braille cell that the input character at index `i` translated to, and
  `input_positions[j]` is the index of the input character that the braille
  cell at index `j` came from. Both count characters, so they index the input
  and output strings directly. `cursor_position` holds the translated position
  of the cursor passed as `cursor_position=`, and stays `None` when none is
  passed; a cursor past the end of the input maps past the end of the output.
- Exception hierarchy: `LouisError`, with `TableParseError` when a table cannot
  be found, read or parsed, and `TableCompileError` when a rule refers to
  something no rule defines. `TableParseError.errors` lists every problem;
  `TableCompileError.path` and `.line` say where the rule is, `path` being
  `None` for table source given in memory. Translating itself cannot fail.
- Warnings from louis-rs go to Python's `logging`, under the `louis` logger.
- Type stubs (`_louis_py.pyi`) and `py.typed` marker.
- Built with maturin, `abi3-py311` (single wheel for Python 3.11+).

<!-- next-url -->
[Unreleased]: https://github.com/liblouis/louis-py/compare/5ca872bf133effa74e3d2e16b7a4647c8a57a4b4...HEAD
