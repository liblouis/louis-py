import os
from pathlib import Path

import pytest


@pytest.mark.skipif(
    os.name != "nt",
    reason="Windows uses ';' as LOUIS_TABLE_PATH separator; POSIX uses ':'",
)
def test_semicolon_separated_table_path(monkeypatch):
    """Validates search_path handling of Windows-style semicolon-separated
    paths."""

    from louis_py import Translator

    tables = str(Path(__file__).parent / "tables")
    monkeypatch.setenv("LOUIS_TABLE_PATH", f"C:\\does-not-exist;{tables}")
    t = Translator(["mini.ctb"])
    assert t.translate("abc") == "⠁⠃⠉"


def test_unset_table_path_searches_the_working_directory(monkeypatch):
    from louis_py import BrailleEncoding, Translator

    monkeypatch.delenv("LOUIS_TABLE_PATH")
    monkeypatch.chdir(Path(__file__).parent / "tables")
    assert Translator(["mini.ctb"]).translate("abc") == "⠁⠃⠉"
    BrailleEncoding("mini.dis")


@pytest.mark.skipif(
    os.name == "nt",
    reason="Windows deletes a variable set to an empty string",
)
def test_empty_table_path_searches_nowhere(monkeypatch):
    from louis_py import BrailleEncoding, TableParseError, Translator

    monkeypatch.setenv("LOUIS_TABLE_PATH", "")
    monkeypatch.chdir(Path(__file__).parent / "tables")
    with pytest.raises(TableParseError):
        Translator(["mini.ctb"])
    with pytest.raises(TableParseError):
        BrailleEncoding("mini.dis")


def test_table_path_is_read_at_each_construction(monkeypatch):
    from louis_py import TableParseError, Translator

    tables = Path(__file__).parent / "tables"
    monkeypatch.setenv("LOUIS_TABLE_PATH", str(tables / "including"))
    with pytest.raises(TableParseError):
        Translator(["mini.ctb"])
    monkeypatch.setenv("LOUIS_TABLE_PATH", str(tables))
    assert Translator(["mini.ctb"]).translate("abc") == "⠁⠃⠉"
