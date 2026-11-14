import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = """\
import pickle

from host.louis_py import Direction, TableParseError, TranslationMode, Translator

t = Translator.from_table_source("space \\\\s 0\\nlowercase a 1\\n", Direction.BACKWARD)
print(t.translate_with_options("\\u2801", mode=TranslationMode.NO_UNDEFINED).output)
try:
    Translator(["definitely-not-a-real-table.ctb"])
except TableParseError as error:
    print(type(pickle.loads(pickle.dumps(error))).__module__)
"""

RELOAD_SCRIPT = """\
import importlib
import logging
import sys

records = []
handler = logging.Handler()
handler.emit = records.append
logging.getLogger("louis").addHandler(handler)


def use():
    louis_py = importlib.import_module("host.louis_py")
    table ="space \\\\s 0\\nlowercase a 1\\nlowercase b 3456\\nnumsign 3456\\n"
    t = louis_py.Translator.from_table_source(table, louis_py.Direction.BACKWARD)
    mode = louis_py.TranslationMode.NO_UNDEFINED
    print(t.translate_with_options("\\u2801", mode=mode).output)


use()
for name in [name for name in sys.modules if name.split(".")[0] == "host"]:
    del sys.modules[name]
records.clear()
use()
print("warned" if records else "silent")
"""


@pytest.fixture
def host(tmp_path):
    """A directory holding the package ``host``, which bundles louis_py as
    ``host.louis_py``."""

    import louis_py

    shutil.copytree(
        Path(louis_py.__file__).parent,
        tmp_path / "host" / "louis_py",
        ignore=shutil.ignore_patterns("__pycache__", "*.pdb"),
    )
    (tmp_path / "host" / "__init__.py").write_text("")
    return tmp_path


def run(script, cwd):
    """The lines ``script`` prints when run in a new interpreter in ``cwd``."""

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.split()


def test_louis_py_works_inside_another_package(host):
    """A host can bundle louis_py as a subpackage of its own."""

    # The types report the host's subpackage as their module, so they pickle
    # there too.
    assert run(SCRIPT, host) == ["a", "host.louis_py"]


def test_louis_py_works_after_importing_it_again(host):
    assert run(RELOAD_SCRIPT, host) == ["a", "a", "warned"]
