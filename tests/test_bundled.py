import shutil
import subprocess
import sys
from pathlib import Path

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


def test_louis_py_works_inside_another_package(tmp_path):
    """A host can bundle louis_py as a subpackage of its own."""

    import louis_py

    host = tmp_path / "host"
    shutil.copytree(
        Path(louis_py.__file__).parent,
        host / "louis_py",
        ignore=shutil.ignore_patterns("__pycache__", "*.pdb"),
    )
    (host / "__init__.py").write_text("")
    result = subprocess.run(
        [sys.executable, "-c", SCRIPT],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    # The types report the host's subpackage as their module, so they pickle
    # there too.
    assert result.stdout.split() == ["a", "host.louis_py"]
