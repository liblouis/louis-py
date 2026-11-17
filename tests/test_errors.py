from pathlib import Path

import pytest


def table_errors(tables, search_path=None):
    """The errors of the TableParseError that compiling ``tables`` raises."""

    from louis_py import TableParseError, Translator

    with pytest.raises(TableParseError) as excinfo:
        Translator(tables, search_path=search_path)
    return excinfo.value.errors


def source_errors(table):
    """The errors of the TableParseError that compiling ``table`` source
    raises."""

    from louis_py import TableParseError, Translator

    with pytest.raises(TableParseError) as excinfo:
        Translator.from_table_source(table)
    return excinfo.value.errors


def compile_error(table):
    """The TableCompileError that compiling ``table`` source raises."""

    from louis_py import TableCompileError, Translator

    with pytest.raises(TableCompileError) as excinfo:
        Translator.from_table_source(table)
    return excinfo.value


def test_bogus_table_raises_table_parse_error():
    from louis_py import LouisError, TableParseError, Translator

    with pytest.raises(TableParseError) as excinfo:
        Translator(["definitely-not-a-real-table.ctb"])

    exc = excinfo.value
    assert isinstance(exc, LouisError)
    assert "definitely-not-a-real-table.ctb" in str(exc)


def test_table_not_found():
    from louis_py import TableError, TableErrorKind

    [error] = table_errors(["definitely-not-a-real-table.ctb"])
    assert isinstance(error, TableError)
    assert error.kind is TableErrorKind.NOT_FOUND
    assert error.path == Path("definitely-not-a-real-table.ctb")
    assert error.line is None
    assert (
        str(error)
        == error.message
        == "cannot find table definitely-not-a-real-table.ctb"
    )


def test_syntax_error_in_table_source_has_line_but_no_path():
    from louis_py import TableErrorKind

    [error] = source_errors("letter a 1\nfoo b 2\n")
    assert error.kind is TableErrorKind.SYNTAX
    assert error.path is None
    assert error.line == 2
    assert str(error) == error.message
    assert error.message.startswith("line 2: ")


def test_syntax_error_in_table_file_names_the_table(tmp_path):
    from louis_py import TableErrorKind

    (tmp_path / "bad.ctb").write_text("letter a 1\nfoo b 2\n")
    [error] = table_errors(["bad.ctb"], [tmp_path])
    assert error.kind is TableErrorKind.SYNTAX
    assert error.path == tmp_path / "bad.ctb"
    assert error.line == 2


def test_table_not_readable(tmp_path):
    from louis_py import TableErrorKind

    (tmp_path / "latin1.ctb").write_bytes(b"letter \xe9 1\n")
    [error] = table_errors(["latin1.ctb"], [tmp_path])
    assert error.kind is TableErrorKind.NOT_READABLE
    assert error.path == tmp_path / "latin1.ctb"


def test_circular_include(tmp_path):
    from louis_py import TableErrorKind

    (tmp_path / "self.ctb").write_text("include self.ctb\n")
    [error] = table_errors(["self.ctb"], [tmp_path])
    assert error.kind is TableErrorKind.CIRCULAR_INCLUDE
    assert error.path is None
    assert isinstance(error.paths, tuple)
    assert [path.name for path in error.paths] == ["self.ctb", "self.ctb"]


def test_include_too_deep(tmp_path):
    from louis_py import TableErrorKind

    (tmp_path / "chain0.ctb").write_text("space \\s 0\n")
    for i in range(1, 65):
        (tmp_path / f"chain{i}.ctb").write_text(f"include chain{i - 1}.ctb\n")
    [error] = table_errors(["chain64.ctb"], [tmp_path])
    assert error.kind is TableErrorKind.INCLUDE_TOO_DEEP
    assert error.depth == 64


def test_hyphenation_table_not_found(tmp_path):
    from louis_py import TableErrorKind

    (tmp_path / "hyph.ctb").write_text("include missing.dic\n")
    [error] = table_errors(["hyph.ctb"], [tmp_path])
    assert error.kind is TableErrorKind.HYPHENATION_NOT_FOUND
    assert error.path == Path("missing.dic")


def test_hyphenation_table_not_readable(tmp_path):
    from louis_py import TableErrorKind

    (tmp_path / "hyph.ctb").write_text("include latin1.dic\n")
    (tmp_path / "latin1.dic").write_bytes(b"\xe9a1\n")
    [error] = table_errors(["hyph.ctb"], [tmp_path])
    assert error.kind is TableErrorKind.HYPHENATION_NOT_READABLE
    assert error.path == tmp_path / "latin1.dic"


def test_hyphenation_syntax_error(tmp_path):
    from louis_py import TableErrorKind

    (tmp_path / "hyph.ctb").write_text("include latin1.dic\n")
    (tmp_path / "latin1.dic").write_text("ISO8859-1\na1b\n")
    [error] = table_errors(["hyph.ctb"], [tmp_path])
    assert error.kind is TableErrorKind.HYPHENATION_SYNTAX
    assert error.path == tmp_path / "latin1.dic"
    assert error.line is None


@pytest.mark.parametrize(
    ("rule", "kind", "emphasis_class"),
    [
        ("endmodephrase foo", "CONFLICTING_ENDMODEPHRASE_POSITION", "foo"),
        ("endcapsphrase", "CONFLICTING_ENDCAPSPHRASE_POSITION", None),
    ],
)
def test_conflicting_phrase_end_position(tmp_path, rule, kind, emphasis_class):
    from louis_py import TableErrorKind

    (tmp_path / "before.ctb").write_text(f"{rule} before 2\n")
    (tmp_path / "after.ctb").write_text(f"{rule} after 2\n")
    (tmp_path / "top.ctb").write_text("include before.ctb\ninclude after.ctb\n")
    [error] = table_errors(["top.ctb"], [tmp_path])
    assert error.kind is TableErrorKind[kind]
    assert error.emphasis_class == emphasis_class
    assert error.path is None


def test_table_parse_error_survives_pickling():
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
    assert exc.kind is excinfo.value.kind
    assert (exc.base, exc.derived) == (excinfo.value.base, excinfo.value.derived)


def test_exception_hierarchy():
    from louis_py import LouisError, TableCompileError, TableParseError

    assert issubclass(TableParseError, LouisError)
    assert issubclass(TableCompileError, LouisError)
    assert issubclass(LouisError, Exception)


def test_compile_error_in_table_file_names_the_table():
    from louis_py import TableCompileError, Translator

    with pytest.raises(TableCompileError) as excinfo:
        Translator(["undefined-base.ctb"])

    exc = excinfo.value
    assert isinstance(exc.path, Path)
    assert exc.path.name == "undefined-base.ctb"
    assert exc.line == 4


def test_base_character_not_defined_in_table_source():
    from louis_py import CompileErrorKind

    exc = compile_error("base uppercase A a\n")
    assert str(exc) == "line 1: base character 'a' of 'A' not defined"
    assert exc.path is None
    assert exc.line == 1
    assert exc.kind is CompileErrorKind.BASE_CHARACTER_NOT_DEFINED
    assert (exc.base, exc.derived) == ("a", "A")
    assert (exc.character, exc.swap_class) == (None, None)


def test_implicit_character_not_defined():
    from louis_py import CompileErrorKind

    exc = compile_error("letter a 1\nalways b =\n")
    assert exc.kind is CompileErrorKind.IMPLICIT_CHARACTER_NOT_DEFINED
    assert exc.character == "b"
    assert (exc.base, exc.derived, exc.swap_class) == (None, None, None)
    assert exc.line == 2


def test_swap_class_not_defined():
    from louis_py import CompileErrorKind

    exc = compile_error('letter a 1\ncontext "a" %foo\n')
    assert exc.kind is CompileErrorKind.SWAP_CLASS_NOT_DEFINED
    assert exc.swap_class == "foo"
    assert (exc.base, exc.derived, exc.character) == (None, None, None)
    assert exc.line == 2
