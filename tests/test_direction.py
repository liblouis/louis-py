import enum

import pytest


def test_direction_is_an_enum():
    from louis_py import Direction

    assert issubclass(Direction, enum.Enum)
    assert list(Direction) == [Direction.FORWARD, Direction.BACKWARD]


def test_direction_is_hashable():
    from louis_py import Direction

    names = {Direction.FORWARD: "forward", Direction.BACKWARD: "backward"}
    assert names[Direction.BACKWARD] == "backward"


@pytest.mark.parametrize("direction", [0, 1, "BACKWARD"])
def test_direction_must_be_a_direction(direction):
    from louis_py import Translator

    with pytest.raises(TypeError):
        Translator(["mini.ctb"], direction)
