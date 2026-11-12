import pytest

COMPBRL_TABLE = (
    "space \\s 0\nlowercase a 1\nlowercase b 12\nlowercase c 14\n"
    "always abc 123456\ncomp6 a 2\ncomp6 b 23\ncomp6 c 25\n"
    "begcomp 456-346\nendcomp 456-156\n"
)
"""Contracts "abc" to one cell, and gives each letter its computer braille."""

PARTIAL_TABLE = (
    "space \\s 0\nlowercase a 1\nlowercase b 12\nlowercase y 13456\n"
    "word about 1-12\njoinword by 356\n"
)
"""Has "about" as a whole word, and "by" joined to the word after it."""


def test_mode_flags_compose():
    from louis_py import TranslationMode

    combined = TranslationMode.NO_CONTRACTIONS | TranslationMode.UC_BRL
    assert combined & TranslationMode.NO_CONTRACTIONS
    assert int(TranslationMode.NO_CONTRACTIONS) == 1


def test_unknown_mode_bits_rejected():
    from louis_py import Translator

    t = Translator(["mini.ctb"])
    with pytest.raises(ValueError):
        t.translate_with_options("abc", mode=1 << 30)


@pytest.mark.parametrize(
    ("mode", "cursor", "expected"),
    [
        # The whole word at the cursor, without begcomp and endcomp.
        ("COMPBRL_AT_CURSOR", 5, "⠿⠀⠂⠆⠒⠀⠿"),
        # Only the part of the word before the cursor.
        ("COMPBRL_LEFT_CURSOR", 6, "⠿⠀⠂⠆⠉⠀⠿"),
        # Without either mode, the cursor changes nothing.
        ("NO_UNDEFINED", 5, "⠿⠀⠿⠀⠿"),
    ],
)
def test_computer_braille_at_cursor(mode, cursor, expected):
    from louis_py import TranslationMode, Translator

    t = Translator.from_table_source(COMPBRL_TABLE)
    r = t.translate_with_options(
        "abc abc abc",
        mode=TranslationMode[mode],
        cursor_position=cursor,
    )
    assert r.output == expected


def test_partial_trans_has_no_word_end():
    from louis_py import Direction, TranslationMode, Translator

    t = Translator.from_table_source(PARTIAL_TABLE, Direction.BACKWARD)
    assert t.translate_with_options("⠁⠃").output == "about"
    # The cells could still become a longer word, so `word about` waits.
    r = t.translate_with_options("⠁⠃", mode=TranslationMode.PARTIAL_TRANS)
    assert r.output == "ab"


@pytest.mark.parametrize(("braille", "expected"), [("⠴", "by"), ("⠴⠁", "by a")])
def test_partial_trans_applies_joinword(braille, expected):
    """A joinword applies, and puts its space back only once a word follows."""

    from louis_py import Direction, TranslationMode, Translator

    t = Translator.from_table_source(PARTIAL_TABLE, Direction.BACKWARD)
    r = t.translate_with_options(braille, mode=TranslationMode.PARTIAL_TRANS)
    assert r.output == expected


def test_no_undefined_drops_undefined_characters():
    from louis_py import TranslationMode, Translator

    t = Translator(["mini.ctb"])
    assert t.translate_with_options("a!b").output != "⠁⠃"
    r = t.translate_with_options("a!b", mode=TranslationMode.NO_UNDEFINED)
    assert r.output == "⠁⠃"


def test_no_undefined_drops_undefined_cells():
    from louis_py import Direction, TranslationMode, Translator

    t = Translator(["mini.ctb"], Direction.BACKWARD)
    assert t.translate_with_options("⠁⠿⠃").output != "ab"
    r = t.translate_with_options("⠁⠿⠃", mode=TranslationMode.NO_UNDEFINED)
    assert r.output == "ab"
