def test_import_and_version():
    import louis_py

    assert isinstance(louis_py.__version__, str)
    assert louis_py.__version__


def test_version_matches_distribution_metadata():
    import importlib.metadata

    import louis_py

    assert louis_py.__version__ == importlib.metadata.version("louis-py")
