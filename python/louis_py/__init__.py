"""Python bindings for the louis braille translator."""

import dataclasses
import enum
from pathlib import Path
from typing import NamedTuple

from ._louis_py import (
    LOUIS_RS_VERSION,
    BrailleEncoding,
    LouisError,
    TableCompileError,
    TableParseError,
    TranslationResult,
    Translator,
    __version__,
)


class Direction(enum.Enum):
    """Which way a ``Translator`` translates."""

    FORWARD = enum.auto()
    """From text to braille."""

    BACKWARD = enum.auto()
    """From braille to text."""


class TranslationMode(enum.Flag):
    """Translation modes, passed as ``mode=``."""

    NO_CONTRACTIONS = enum.auto()
    """Forward: no contracting rule applies, such as ``word``, ``always`` or
    ``match``. Backward: ignored."""

    COMPBRL_AT_CURSOR = enum.auto()
    """Forward, with ``cursor_position=``: the word at the cursor is shown
    uncontracted, in computer braille without begcomp and endcomp."""

    COMPBRL_LEFT_CURSOR = enum.auto()
    """Like ``COMPBRL_AT_CURSOR``, but only the part of the word before the
    cursor."""

    NO_UNDEFINED = enum.auto()
    """Drop characters, or backward cells, the tables do not define."""

    PARTIAL_TRANS = enum.auto()
    """Backward: the braille may end in the middle of a word, such as the cells
    typed so far, so rules for whole words or word ends do not apply."""


class EmphasisSpan(NamedTuple):
    class_: str
    start: int
    """The first emphasized character."""

    end: int
    """The character after the last emphasized one."""


class TableErrorKind(enum.Enum):
    """What went wrong in reading a table."""

    SYNTAX = enum.auto()
    """A line of a table could not be parsed."""

    INCLUDES_NOT_SUPPORTED_IN_MEMORY = enum.auto()
    """Table source given in memory has an ``include``."""

    NOT_READABLE = enum.auto()
    """A table was found but could not be read."""

    NOT_FOUND = enum.auto()
    """A table is not on the search path."""

    HYPHENATION_NOT_FOUND = enum.auto()
    """A hyphenation table is not on the search path."""

    HYPHENATION_NOT_READABLE = enum.auto()
    """A hyphenation table was found but could not be read."""

    HYPHENATION_SYNTAX = enum.auto()
    """A hyphenation table could not be parsed."""

    CIRCULAR_INCLUDE = enum.auto()
    """Tables include each other in a cycle."""

    INCLUDE_TOO_DEEP = enum.auto()
    """A chain of includes is deeper than the maximum."""

    CONFLICTING_ENDMODEPHRASE_POSITION = enum.auto()
    """The ``endmodephrase`` of an emphasis class is defined both before and
    after."""

    CONFLICTING_ENDCAPSPHRASE_POSITION = enum.auto()
    """``endcapsphrase`` is defined both before and after."""


class CompileErrorKind(enum.Enum):
    """What is wrong with a rule that failed to compile."""

    IMPLICIT_CHARACTER_NOT_DEFINED = enum.auto()
    """A rule uses a character's dots implicitly (``=``), but no rule defines
    that character."""

    BASE_CHARACTER_NOT_DEFINED = enum.auto()
    """A ``base`` rule's base character is not defined in either direction."""

    SWAP_CLASS_NOT_DEFINED = enum.auto()
    """A rule refers to a swap class that no rule defines."""


@dataclasses.dataclass(frozen=True)
class TableError:
    """A problem in reading a table, one of ``TableParseError.errors``."""

    kind: TableErrorKind
    """What went wrong."""

    message: str
    """What went wrong, in words."""

    path: Path | None = None
    """The table, or ``None`` for table source given in memory."""

    line: int | None = None
    """The line that could not be parsed, counting from 1."""

    paths: tuple[Path, ...] | None = None
    """The tables of a cycle, in the order of inclusion."""

    depth: int | None = None
    """The maximum depth of a chain of includes."""

    emphasis_class: str | None = None
    """The emphasis class of a conflicting ``endmodephrase``."""

    def __str__(self) -> str:
        return self.message


__all__ = [
    "LOUIS_RS_VERSION",
    "BrailleEncoding",
    "CompileErrorKind",
    "Direction",
    "EmphasisSpan",
    "LouisError",
    "TableCompileError",
    "TableError",
    "TableErrorKind",
    "TableParseError",
    "TranslationMode",
    "TranslationResult",
    "Translator",
    "__version__",
]
