import pickle
from pathlib import Path

import pytest


@pytest.fixture
def tables(tmp_path):
    """A directory of three tables that carry language and grade metadata."""

    (tmp_path / "b.utb").write_text("#+language: de\n#+grade: 2\n")
    (tmp_path / "a.utb").write_text("#+language: de\n#+grade: 2\n")
    (tmp_path / "c.utb").write_text("#+language: de\n#+grade: 1\n")
    return tmp_path


def test_index_finds_the_tables_carrying_every_pair_sorted(tables):
    from louis_py.metadata import Index, Query

    index = Index(search_path=[tables])
    expected = [tables / "a.utb", tables / "b.utb"]
    assert index.find(Query.parse("language:de grade:2")) == expected
    assert index.find("language:de grade:2") == expected
    assert index.find({"language": "de", "grade": "2"}.items()) == expected
    assert index.find({"language": "de", "grade": "2"}) == expected
    assert all(isinstance(path, Path) for path in index.find("grade:2"))


def test_index_finds_nothing_for_a_pair_no_table_carries(tables):
    from louis_py.metadata import Index

    assert Index(search_path=[tables]).find("language:fr") == []


def test_find_with_a_bad_query_raises_invalid_query_error(tables):
    from louis_py.metadata import Index, InvalidQueryError

    with pytest.raises(InvalidQueryError) as excinfo:
        Index(search_path=[tables]).find("language=de")
    assert excinfo.value.pair == "language=de"


def test_index_reads_the_table_path_variable(tables, monkeypatch):
    from louis_py.metadata import Index

    monkeypatch.setenv("LOUIS_TABLE_PATH", str(tables))
    assert Index().find("grade:1") == [tables / "c.utb"]


def test_index_on_a_missing_directory_raises_metadata_io_error(tmp_path):
    from louis_py import LouisError
    from louis_py.metadata import Index, MetadataIOError

    with pytest.raises(MetadataIOError) as excinfo:
        Index(search_path=[tmp_path / "does-not-exist"])
    assert isinstance(excinfo.value, OSError)
    assert isinstance(excinfo.value, LouisError)


def test_query_parses_pairs_separated_by_whitespace():
    from louis_py.metadata import Query

    query = Query.parse("grade:2 language:de")
    assert query == Query([("grade", "2"), ("language", "de")])
    assert query == Query(
        (key, value) for key, value in [("grade", "2"), ("language", "de")]
    )
    assert query == Query({"grade": "2", "language": "de"})
    assert str(query) == "grade:2 language:de"


def test_query_pairs_is_a_mapping_or_key_value_pairs():
    from collections.abc import Iterable, Mapping

    from louis_py.metadata import QueryPairs

    assert QueryPairs == Mapping[str, str] | Iterable[tuple[str, str]]


def test_query_prints_its_pairs_sorted():
    from louis_py.metadata import Query

    assert str(Query([("language", "de"), ("grade", "2")])) == "grade:2 language:de"


def test_query_without_key_value_pair_raises_invalid_query_error():
    from louis_py import LouisError
    from louis_py.metadata import InvalidQueryError, MetadataError, Query

    with pytest.raises(InvalidQueryError) as excinfo:
        Query.parse("grade:2 language=de")

    exc = excinfo.value
    assert isinstance(exc, MetadataError)
    assert isinstance(exc, LouisError)
    assert isinstance(exc, ValueError)
    assert exc.pair == "language=de"
    assert str(exc) == '"language=de" is not a key:value pair'


def test_invalid_query_error_survives_pickling():
    from louis_py.metadata import InvalidQueryError, Query

    with pytest.raises(InvalidQueryError) as excinfo:
        Query.parse("language:")

    exc = pickle.loads(pickle.dumps(excinfo.value))
    assert type(exc) is InvalidQueryError
    assert str(exc) == str(excinfo.value)
    assert exc.pair == "language:"
