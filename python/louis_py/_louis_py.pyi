import os
import pathlib
from collections.abc import Sequence

from . import Direction, TranslationMode

class TranslationResult:
    output: str
    emphasis: list[tuple[str, int, int]] | None
    """Backward, the emphasis of ``output`` as the braille's emphasis indicators
    give it (liblouis's typeform): ``(class, start, end)`` spans, sorted by
    class and then by start, with touching spans of a class merged. The space
    that ends an emphasized word is not emphasized. Forward, where the emphasis
    comes with the input, always ``None``."""

    output_positions: list[int]
    """``output_positions[i]`` is the index in ``output`` of the cell that the
    input character at index ``i`` translated to. One entry per input
    character."""

    input_positions: list[int]
    """``input_positions[j]`` is the index in the input text of the character
    that ``output[j]`` came from. One entry per output cell."""

    cursor_position: int | None
    """The position of the ``cursor_position=`` argument translated into
    ``output``, or ``None`` when no cursor was passed. Equals ``len(output)``
    for a cursor past the end of the input."""

class BrailleEncoding:
    """Which characters stand for the braille cells, such as ASCII braille,
    loaded from a liblouis display table (``.dis``). One encoding can serve
    translators in both directions."""

    def __init__(
        self,
        table: str | os.PathLike,
        *,
        search_path: Sequence[str | os.PathLike] | None = ...,
    ) -> None:
        """Load the display table ``table``.

        :param search_path: Looked up as for ``Translator``.
        """

    @staticmethod
    def from_table_source(table: str) -> BrailleEncoding: ...

class Translator:
    def __init__(
        self,
        tables: Sequence[str | os.PathLike],
        direction: Direction = ...,
        *,
        search_path: Sequence[str | os.PathLike] | None = ...,
        braille_encoding: BrailleEncoding | None = ...,
    ) -> None:
        """Compile ``tables`` for translating in ``direction``.

        :param search_path: Directories searched, in order, for each table name
            and every ``include``. ``None`` reads ``LOUIS_TABLE_PATH`` (``.``
            when unset). Nothing else is searched: a table's own directory only
            when listed, and an absolute table name resolves against any
            non-empty search path.
        :param braille_encoding: Read and write braille in this encoding.
            ``None`` means Unicode braille. A display table in ``tables`` is
            ignored, unlike in liblouis.
        """

    @staticmethod
    def from_table_source(
        table: str,
        direction: Direction = ...,
        *,
        braille_encoding: BrailleEncoding | None = ...,
    ) -> Translator: ...
    @property
    def emphasis_classes(self) -> list[str]:
        """The emphasis classes the tables declare with ``emphclass``, in the
        order they declare them: the class names emphasis spans can use."""

    def translate(self, text: str) -> str: ...
    def translate_with_options(
        self,
        text: str,
        *,
        mode: TranslationMode = ...,
        emphasis: Sequence[tuple[str, int, int]] | None = ...,
        cursor_position: int | None = ...,
    ) -> TranslationResult:
        """Translate ``text`` with options, and report which input became which
        output.

        :param mode: The translation modes. No modes by default.
        :param emphasis: ``(class, start, end)`` spans over the input, such as
            ``EmphasisSpan``. Classes the tables do not declare are ignored.
        """

class LouisError(Exception): ...

class TableParseError(LouisError):
    errors: list[str]
    """One message per problem: a table that could not be found or read, or a
    line that could not be parsed."""

class TableCompileError(LouisError):
    path: pathlib.Path | None
    """The table of the rule that failed to compile, or ``None`` for table
    source given in memory."""

    line: int
    """The line of that rule, counting from 1."""

__version__: str
