import logging

COLLIDING_TABLE = "space \\s 0\nlowercase a 1\nlowercase b 3456\nnumsign 3456\n"
"""Gives the number sign the dots of the letter b, which louis-rs warns about
when it compiles the table backward."""


def test_louis_rs_warnings_reach_python_logging(caplog):
    from louis_py import Direction, Translator

    with caplog.at_level(logging.WARNING, logger="louis"):
        Translator.from_table_source(COLLIDING_TABLE, Direction.BACKWARD)
    records = [r for r in caplog.records if r.name.startswith("louis.")]
    assert records
    assert all(r.levelno == logging.WARNING for r in records)
    assert "numsign" in records[0].getMessage()
