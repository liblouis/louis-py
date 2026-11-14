import pytest

ITALIC_TABLE = (
    "space \\s 0\nlowercase a 1\nlowercase b 12\nemphclass italic\n"
    "emphletter italic 46-23\nbegemphword italic 46-2\nendemphword italic 46-3\n"
)


def test_emphasis_span_namedtuple():
    from louis_py import EmphasisSpan

    s = EmphasisSpan("italic", 0, 3)
    assert s.class_ == "italic"
    assert s.start == 0
    assert s.end == 3
    assert tuple(s) == ("italic", 0, 3)


def test_forward_emphasis_adds_indicators():
    from louis_py import EmphasisSpan, Translator

    t = Translator.from_table_source(ITALIC_TABLE)
    r = t.translate_with_options("ab", emphasis=[EmphasisSpan("italic", 0, 1)])
    assert r.output == "⠨⠆⠁⠃"


def test_undeclared_emphasis_class_is_ignored():
    from louis_py import EmphasisSpan, Translator

    t = Translator(["mini.ctb"])
    r = t.translate_with_options("abc", emphasis=[EmphasisSpan("italic", 0, 2)])
    assert r.output == "⠁⠃⠉"


def test_forward_result_has_no_emphasis():
    from louis_py import EmphasisSpan, Translator

    t = Translator.from_table_source(ITALIC_TABLE)
    r = t.translate_with_options("ab", emphasis=[EmphasisSpan("italic", 0, 1)])
    assert r.emphasis is None


@pytest.mark.parametrize(
    ("braille", "text", "spans"),
    [
        # A single emphasized letter.
        ("⠨⠆⠁⠃", "ab", (("italic", 0, 1),)),
        # A word up to its end indicator.
        ("⠃⠀⠨⠂⠁⠃⠨⠄⠁", "b aba", (("italic", 2, 4),)),
        # A word without an end indicator ends at the space, which is not
        # emphasized.
        ("⠨⠂⠁⠃⠀⠁", "ab a", (("italic", 0, 2),)),
        # No indicators, no spans.
        ("⠁⠃", "ab", ()),
    ],
)
def test_back_translation_returns_the_emphasis(braille, text, spans):
    from louis_py import Direction, EmphasisSpan, Translator

    t = Translator.from_table_source(ITALIC_TABLE, Direction.BACKWARD)
    r = t.translate_with_options(braille)
    assert r.output == text
    assert r.emphasis == spans
    assert tuple(EmphasisSpan(*span) for span in r.emphasis) == spans


def test_emphasis_accepts_a_tuple_of_spans():
    from louis_py import EmphasisSpan, Translator

    t = Translator.from_table_source(ITALIC_TABLE)
    r = t.translate_with_options("ab", emphasis=(EmphasisSpan("italic", 0, 1),))
    assert r.output == "⠨⠆⠁⠃"


def test_back_translated_emphasis_is_built_once():
    from louis_py import Direction, Translator

    t = Translator.from_table_source(ITALIC_TABLE, Direction.BACKWARD)
    r = t.translate_with_options("⠨⠆⠁⠃")
    assert r.emphasis is r.emphasis


def test_repr_shows_back_translated_emphasis_as_python_values():
    from louis_py import Direction, Translator

    t = Translator.from_table_source(ITALIC_TABLE, Direction.BACKWARD)
    r = t.translate_with_options("⠨⠆⠁⠃")
    assert "emphasis=(('italic', 0, 1),)," in repr(r)


def test_emphasis_classes_in_declaration_order():
    from louis_py import Translator

    table = "emphclass italic\nemphclass bold\nemphclass italic\nletter a 1\n"
    t = Translator.from_table_source(table)
    assert t.emphasis_classes == ["italic", "bold"]


def test_no_emphasis_classes():
    from louis_py import Translator

    assert Translator(["mini.ctb"]).emphasis_classes == []
