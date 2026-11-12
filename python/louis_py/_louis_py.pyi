import os
import pathlib
from collections.abc import Sequence

class Direction:
    FORWARD: Direction
    BACKWARD: Direction
    def __int__(self) -> int: ...

class TranslationResult:
    output: str
    # Backward, the emphasis of `output` as the braille's emphasis indicators
    # give it (liblouis's typeform): (class, start, end) spans, sorted by
    # class and then by start, with touching spans of a class merged. The
    # space that ends an emphasized word is not emphasized. Forward, where the
    # emphasis comes with the input, always None.
    emphasis: list[tuple[str, int, int]] | None
    # output_positions[i] is the index in `output` of the cell that the input
    # character at index i translated to. One entry per input character.
    output_positions: list[int]
    # input_positions[j] is the index in the input text of the character that
    # `output[j]` came from. One entry per output cell.
    input_positions: list[int]
    # The position of the `cursor_position=` argument translated into
    # `output`, or None when no cursor was passed. Equals len(output) for a
    # cursor past the end of the input.
    cursor_position: int | None

# Which characters stand for the braille cells, such as ASCII braille, loaded
# from a liblouis display table (`.dis`). One encoding can serve translators
# in both directions.
class BrailleEncoding:
    def __init__(
        self,
        table: str | os.PathLike,
        *,
        # Looked up as for Translator.
        search_path: Sequence[str | os.PathLike] | None = ...,
    ) -> None: ...
    @staticmethod
    def from_table_source(table: str) -> BrailleEncoding: ...

class Translator:
    def __init__(
        self,
        tables: Sequence[str | os.PathLike],
        direction: Direction = ...,
        *,
        # Directories searched, in order, for each table name and every
        # `include`. None reads LOUIS_TABLE_PATH (`.` when unset). Nothing else
        # is searched: a table's own directory only when listed, and an
        # absolute table name resolves against any non-empty search path.
        search_path: Sequence[str | os.PathLike] | None = ...,
        # Read and write braille in this encoding. None means Unicode braille.
        # A display table in `tables` is ignored, unlike in liblouis.
        braille_encoding: BrailleEncoding | None = ...,
    ) -> None: ...
    @staticmethod
    def from_table_source(
        table: str,
        direction: Direction = ...,
        *,
        braille_encoding: BrailleEncoding | None = ...,
    ) -> Translator: ...
    # The emphasis classes the tables declare with `emphclass`, in the order
    # they declare them: the class names emphasis spans can use.
    @property
    def emphasis_classes(self) -> list[str]: ...
    def translate(self, text: str) -> str: ...
    def translate_with_options(
        self,
        text: str,
        *,
        # TranslationMode flags. COMPBRL_AT_CURSOR, COMPBRL_LEFT_CURSOR,
        # NO_UNDEFINED and PARTIAL_TRANS take effect; the others are ignored.
        mode: int = ...,
        # (class, start, end) spans over the input, such as EmphasisSpan.
        # Classes the tables do not declare are ignored.
        emphasis: list[tuple[str, int, int]] | None = ...,
        cursor_position: int | None = ...,
    ) -> TranslationResult: ...

class LouisError(Exception): ...

class TableParseError(LouisError):
    # One message per problem: a table that could not be found or read, or a
    # line that could not be parsed.
    errors: list[str]

class TableCompileError(LouisError):
    # The table of the rule that failed to compile, or None for table source
    # given in memory.
    path: pathlib.Path | None
    # The line of that rule, counting from 1.
    line: int

__version__: str
