import pytest

MINI_TABLE = "space \\s 0\nletter a 1\nletter b 12\n"


def test_from_table_source_translates():
    from louis_py import Translator

    t = Translator.from_table_source(MINI_TABLE)
    assert t.translate("ab") == "⠁⠃"


def test_from_table_source_accepts_direction():
    from louis_py import Direction, Translator

    t = Translator.from_table_source(MINI_TABLE, Direction.BACKWARD)
    assert t.translate("⠁⠃") == "ab"


def test_from_table_source_rejects_include():
    from louis_py import TableErrorKind, TableParseError, Translator

    with pytest.raises(TableParseError) as excinfo:
        Translator.from_table_source("include mini.ctb\n")

    [error] = excinfo.value.errors
    assert error.kind is TableErrorKind.INCLUDES_NOT_SUPPORTED_IN_MEMORY
    assert (error.path, error.line) == (None, None)
