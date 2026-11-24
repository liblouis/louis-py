import pytest


def test_import_and_version():
    import louis_py

    assert isinstance(louis_py.__version__, str)
    assert louis_py.__version__


@pytest.mark.parametrize(
    "name",
    [
        "BrailleEncoding",
        "LouisError",
        "TableCompileError",
        "TableParseError",
        "TranslationResult",
        "Translator",
    ],
)
def test_public_types_name_the_package_as_their_module(name):
    import louis_py

    assert getattr(louis_py, name).__module__ == "louis_py"


def test_version_matches_distribution_metadata():
    import importlib.metadata

    import louis_py

    assert louis_py.__version__ == importlib.metadata.version("louis-py")


def test_louis_rs_version_matches_the_locked_louis_rs():
    import tomllib
    from pathlib import Path

    import louis_py

    lock = tomllib.loads((Path(__file__).parent.parent / "Cargo.lock").read_text())
    (locked,) = (p["version"] for p in lock["package"] if p["name"] == "louis-rs")
    assert louis_py.LOUIS_RS_VERSION == locked
