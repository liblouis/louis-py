import os
import pathlib
from collections.abc import Sequence

class Direction:
    FORWARD: Direction
    BACKWARD: Direction
    def __int__(self) -> int: ...

class TranslationResult:
    output: str
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
    ) -> None: ...
    @staticmethod
    def from_table_source(
        table: str,
        direction: Direction = ...,
    ) -> Translator: ...
    def translate(self, text: str) -> str: ...
    def translate_with_options(
        self,
        text: str,
        *,
        # TranslationMode flags. COMPBRL_AT_CURSOR, COMPBRL_LEFT_CURSOR,
        # NO_UNDEFINED and PARTIAL_TRANS take effect; the others are ignored.
        mode: int = ...,
        emphasis: list[tuple[str, int, int]] | None = ...,
        cursor_position: int | None = ...,
    ) -> TranslationResult: ...

class LouisError(Exception): ...

class TableParseError(LouisError):
    # One message per table that could not be found, read or parsed.
    errors: list[str]

class TableCompileError(LouisError):
    # The table of the rule that failed to compile, or None for table source
    # given in memory.
    path: pathlib.Path | None
    # The line of that rule, counting from 1.
    line: int

__version__: str
