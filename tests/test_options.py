import pytest


def test_translate_with_options_output():
    from louis_py import Translator

    t = Translator(["mini.ctb"])
    r = t.translate_with_options("abc")
    assert r.output == "⠁⠃⠉"


def test_forward_translation_reports_no_emphasis():
    """Forward, the emphasis comes with the input, so the result has none."""

    from louis_py import Translator

    t = Translator(["mini.ctb"])
    r = t.translate_with_options("abc")
    assert r.emphasis is None


def test_repr_shows_python_values():
    from louis_py import Translator

    t = Translator(["mini.ctb"])
    r = t.translate_with_options("ab", cursor_position=1)
    assert repr(r) == (
        "TranslationResult(output='⠁⠃', emphasis=None, output_positions=(0, 1), "
        "input_positions=(0, 1), cursor_position=1)"
    )


def test_result_attributes_cannot_be_changed():
    from louis_py import Translator

    t = Translator(["mini.ctb"])
    r = t.translate_with_options("abc")
    with pytest.raises(AttributeError):
        r.output_positions.append(3)
    with pytest.raises(TypeError):
        r.input_positions[0] = 1


def test_result_attributes_are_built_once():
    from louis_py import Translator

    t = Translator(["mini.ctb"])
    r = t.translate_with_options("abc")
    assert r.output is r.output
    assert r.output_positions is r.output_positions
    assert r.input_positions is r.input_positions
