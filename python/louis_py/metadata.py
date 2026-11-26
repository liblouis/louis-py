"""Find tables by the ``#+key: value`` metadata they carry, instead of by file
name."""

from collections.abc import Iterable, Mapping
from typing import TypeAlias

from . import LouisError
from ._louis_py import Index, Query

QueryPairs: TypeAlias = Mapping[str, str] | Iterable[tuple[str, str]]
"""The pairs of a query: a mapping of keys to values, or ``(key, value)``
pairs."""


class MetadataError(LouisError):
    """Base class for metadata errors."""


class InvalidQueryError(MetadataError, ValueError):
    """A part of a query is not a ``key:value`` pair."""

    pair: str
    """The part that is not a ``key:value`` pair."""


class MetadataIOError(MetadataError, OSError):
    """A directory on the search path could not be read."""


__all__ = [
    "Index",
    "InvalidQueryError",
    "MetadataError",
    "MetadataIOError",
    "Query",
    "QueryPairs",
]
