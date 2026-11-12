from pathlib import Path

import pytest

TABLES = Path(__file__).parent / "tables"
LETTERS = "display a 1\ndisplay b 12\n"


def test_encoding_writes_and_reads_the_cells():
    from louis_py import BrailleEncoding, Direction, Translator

    encoding = BrailleEncoding.from_table_source(LETTERS)
    forward = Translator(["mini.ctb"], braille_encoding=encoding)
    # The space cell has no display rule, so it stays Unicode braille.
    assert forward.translate("ab ba") == "ab⠀ba"
    backward = Translator(["mini.ctb"], Direction.BACKWARD, braille_encoding=encoding)
    assert backward.translate("ab⠀ba") == "ab ba"


def test_encoding_with_translator_from_table_source():
    from louis_py import BrailleEncoding, Translator

    encoding = BrailleEncoding.from_table_source("display x 1\ndisplay y 12\n")
    t = Translator.from_table_source(
        "lowercase a 1\nlowercase b 12\n",
        braille_encoding=encoding,
    )
    assert t.translate("ab") == "xy"


def test_without_encoding_braille_is_unicode():
    from louis_py import Translator

    assert Translator(["mini.ctb"]).translate("ab") == "⠁⠃"


def test_encoding_from_search_path(monkeypatch):
    from louis_py import BrailleEncoding, Translator

    monkeypatch.setenv("LOUIS_TABLE_PATH", str(Path(__file__).parent / "nowhere"))
    encoding = BrailleEncoding("mini.dis", search_path=[TABLES])
    t = Translator(["mini.ctb"], search_path=[TABLES], braille_encoding=encoding)
    assert t.translate("abc") == "abc"


def test_encoding_from_table_path_variable():
    # conftest points LOUIS_TABLE_PATH at the tables directory.
    from louis_py import BrailleEncoding, Translator

    t = Translator(["mini.ctb"], braille_encoding=BrailleEncoding("mini.dis"))
    assert t.translate("abc") == "abc"


def test_missing_encoding_raises_table_parse_error():
    from louis_py import BrailleEncoding, TableParseError

    with pytest.raises(TableParseError) as excinfo:
        BrailleEncoding("definitely-not-a-real-table.dis")
    assert "definitely-not-a-real-table.dis" in str(excinfo.value)


def test_encoding_source_rejects_include():
    from louis_py import BrailleEncoding, TableParseError

    with pytest.raises(TableParseError):
        BrailleEncoding.from_table_source("include mini.dis\n")
