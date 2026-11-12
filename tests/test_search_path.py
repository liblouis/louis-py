from pathlib import Path

import pytest

TABLES = Path(__file__).parent / "tables"
INCLUDING = TABLES / "including"
BOGUS = Path(__file__).parent / "does-not-exist"


def test_search_path_replaces_table_path_variable():
    """search_path= is used instead of LOUIS_TABLE_PATH, which conftest
    points at the valid tables directory."""

    from louis_py import TableParseError, Translator

    with pytest.raises(TableParseError):
        Translator(["mini.ctb"], search_path=[str(BOGUS)])


def test_search_path_finds_table_without_table_path_variable(monkeypatch):
    from louis_py import Translator

    monkeypatch.setenv("LOUIS_TABLE_PATH", str(BOGUS))
    t = Translator(["mini.ctb"], search_path=[str(TABLES)])
    assert t.translate("abc") == "⠁⠃⠉"


def test_include_resolves_across_search_path_directories():
    from louis_py import Translator

    t = Translator(["top.ctb"], search_path=[str(INCLUDING), str(TABLES)])
    assert t.translate("a.") == "⠁⠲"


def test_include_not_found_outside_search_path():
    from louis_py import TableParseError, Translator

    with pytest.raises(TableParseError):
        Translator(["top.ctb"], search_path=[str(INCLUDING)])


def test_pathlike_tables_and_search_path_entries():
    from louis_py import Translator

    t = Translator([Path("mini.ctb")], search_path=[TABLES])
    assert t.translate("abc") == "⠁⠃⠉"


def test_absolute_table_resolves_against_unrelated_search_path():
    from louis_py import Translator

    t = Translator([str(TABLES / "mini.ctb")], search_path=[str(BOGUS)])
    assert t.translate("abc") == "⠁⠃⠉"
