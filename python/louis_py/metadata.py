"""Find tables by the ``#+key: value`` metadata they carry, instead of by file
name."""

from . import LouisError
from ._louis_py import Index, Query


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
]
