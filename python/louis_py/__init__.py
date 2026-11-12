"""Python bindings for the louis braille translator."""

import enum
from typing import NamedTuple

from ._louis_py import (
    BrailleEncoding,
    Direction,
    LouisError,
    TableCompileError,
    TableParseError,
    TranslationResult,
    Translator,
    __version__,
)


class TranslationMode(enum.IntFlag):
    """The liblouis translation modes, passed as ``mode=``.

    Modes louis-rs does not implement yet are accepted and ignored.
    """

    NO_CONTRACTIONS = 1 << 0
    """Not implemented yet: ignored."""

    COMPBRL_AT_CURSOR = 1 << 1
    """Forward, with ``cursor_position=``: the word at the cursor is shown
    uncontracted, in computer braille without begcomp and endcomp."""

    DOTS_IO = 1 << 2
    """Not implemented yet: ignored. Braille is Unicode braille, or the
    characters of a ``BrailleEncoding``."""

    COMPBRL_LEFT_CURSOR = 1 << 3
    """Like ``COMPBRL_AT_CURSOR``, but only the part of the word before the
    cursor."""

    UC_BRL = 1 << 4
    """Not implemented yet: ignored."""

    NO_UNDEFINED = 1 << 5
    """Drop characters, or backward cells, the tables do not define."""

    PARTIAL_TRANS = 1 << 6
    """Backward: the braille may end in the middle of a word, such as the cells
    typed so far, so rules for whole words or word ends do not apply."""


class EmphasisSpan(NamedTuple):
    class_: str
    start: int  # inclusive
    end: int  # exclusive


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
