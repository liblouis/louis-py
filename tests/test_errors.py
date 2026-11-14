import pytest


def test_bogus_table_raises_table_parse_error():
    from louis_py import LouisError, TableParseError, Translator

    with pytest.raises(TableParseError) as excinfo:
        Translator(["definitely-not-a-real-table.ctb"])

    exc = excinfo.value
    assert isinstance(exc, LouisError)
    assert "definitely-not-a-real-table.ctb" in str(exc)
    assert isinstance(exc.errors, list)
    assert len(exc.errors) >= 1
    assert all(isinstance(e, str) for e in exc.errors)


def test_table_parse_error_survives_pickling():
    """A worker process sends its exceptions back to the parent pickled."""

    import pickle

    from louis_py import TableParseError, Translator

    with pytest.raises(TableParseError) as excinfo:
        Translator(["definitely-not-a-real-table.ctb"])

    exc = pickle.loads(pickle.dumps(excinfo.value))
    assert type(exc) is TableParseError
    assert str(exc) == str(excinfo.value)
    assert exc.errors == excinfo.value.errors


def test_table_compile_error_survives_pickling():
    import pickle

    from louis_py import TableCompileError, Translator

    with pytest.raises(TableCompileError) as excinfo:
        Translator(["undefined-base.ctb"])

    exc = pickle.loads(pickle.dumps(excinfo.value))
    assert type(exc) is TableCompileError
    assert str(exc) == str(excinfo.value)
    assert exc.path == excinfo.value.path
    assert exc.line == excinfo.value.line


def test_exception_hierarchy():
    from louis_py import LouisError, TableCompileError, TableParseError

    assert issubclass(TableParseError, LouisError)
    assert issubclass(TableCompileError, LouisError)
    assert issubclass(LouisError, Exception)


def test_compile_error_in_table_source_has_line_but_no_path():
    from louis_py import TableCompileError, Translator

    with pytest.raises(TableCompileError) as excinfo:
        Translator.from_table_source("base uppercase A a\n")

    exc = excinfo.value
    assert str(exc) == "line 1: base character 'a' of 'A' not defined"
    assert exc.path is None
    assert exc.line == 1


def test_compile_error_in_table_file_names_the_table():
    from pathlib import Path

    from louis_py import TableCompileError, Translator

    with pytest.raises(TableCompileError) as excinfo:
        Translator(["undefined-base.ctb"])

    exc = excinfo.value
    assert isinstance(exc.path, Path)
    assert exc.path.name == "undefined-base.ctb"
    assert exc.line == 4
