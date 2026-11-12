def test_translate_with_options_output():
    from louis_py import Translator

    t = Translator(["mini.ctb"])
    r = t.translate_with_options("abc")
    assert r.output == "⠁⠃⠉"


def test_forward_translation_reports_no_emphasis():
    # Forward, the emphasis comes with the input, so the result has none.
    from louis_py import Translator

    t = Translator(["mini.ctb"])
    r = t.translate_with_options("abc")
    assert r.emphasis is None


def test_repr():
    from louis_py import Translator

    t = Translator(["mini.ctb"])
    r = t.translate_with_options("a")
    assert "TranslationResult" in repr(r)
