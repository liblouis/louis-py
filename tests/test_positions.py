# Position maps are indexed per character, which matches Python string indexing.
NUMBER_TABLE = "space \\s 0\nletter a 1\nlitdigit 4 145\nlitdigit 2 12\nnumsign 3456\n"
CAPS_TABLE = "lowercase h 125\nlowercase i 24\nbase uppercase H h\ncapsletter 6\n"
EMOJI = chr(0x1F600)


def test_positions_are_one_to_one_without_indicators():
    from louis_py import Translator

    t = Translator(["mini.ctb"])
    r = t.translate_with_options("abc")
    assert r.output_positions == [0, 1, 2]
    assert r.input_positions == [0, 1, 2]


def test_number_sign_shifts_later_positions():
    from louis_py import Translator

    t = Translator.from_table_source(NUMBER_TABLE)
    r = t.translate_with_options("a 42")
    assert r.output == "⠁⠀⠼⠙⠃"
    # The number sign occupies output cell 2, so "4" lands on 3 and "2" on 4.
    assert r.output_positions == [0, 1, 2, 4]
    # Both the number sign and "4" point back at input character 2.
    assert r.input_positions == [0, 1, 2, 2, 3]


def test_cursor_is_translated_only_when_given():
    from louis_py import Translator

    t = Translator.from_table_source(NUMBER_TABLE)
    assert t.translate_with_options("a 42").cursor_position is None
    assert t.translate_with_options("a 42", cursor_position=2).cursor_position == 2


def test_cursor_past_the_end_maps_past_the_end():
    from louis_py import Translator

    t = Translator.from_table_source(NUMBER_TABLE)
    r = t.translate_with_options("a 42", cursor_position=4)
    assert r.cursor_position == len(r.output) == 5


def test_backward_positions():
    from louis_py import Direction, Translator

    t = Translator.from_table_source(CAPS_TABLE, Direction.BACKWARD)
    r = t.translate_with_options("⠠⠓⠊")
    assert r.output == "Hi"
    assert r.output_positions == [0, 0, 1]
    # Backward, a consumed cell is claimed by the character that follows it, so
    # "H" covers the capital sign as well.
    assert r.input_positions == [0, 2]


def test_positions_count_characters_not_utf8_bytes():
    # Rust counts chars, Python counts code points, so the indices line up even
    # for characters outside the basic multilingual plane.
    from louis_py import Translator

    table = "space \\s 0\nletter a 1\nsign " + EMOJI + " 1234\n"
    t = Translator.from_table_source(table)
    text = "a" + EMOJI + "a"
    r = t.translate_with_options(text, cursor_position=2)
    assert len(text) == 3
    assert r.output_positions == [0, 1, 2]
    assert r.input_positions == [0, 1, 2]
    assert r.cursor_position == 2
