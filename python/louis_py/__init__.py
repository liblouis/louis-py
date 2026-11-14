"""Python bindings for the louis braille translator."""

import enum
from typing import NamedTuple

from ._louis_py import (
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


__all__ = [
    "BrailleEncoding",
    "Direction",
    "EmphasisSpan",
    "LouisError",
    "TableCompileError",
    "TableParseError",
    "TranslationMode",
    "TranslationResult",
    "Translator",
    "__version__",
]
