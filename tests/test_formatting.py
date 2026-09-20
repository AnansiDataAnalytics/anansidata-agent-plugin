from anansi_mcp.format import clean, display, display_pct


def test_clean_rounds_by_magnitude_and_stays_numeric():
    assert clean(198540960.0) == 198540960
    assert clean(123041.82363531466) == 123042
    assert clean(6.165544509887695) == 6.17
    assert clean(0.00123456) == 0.0012
    assert clean(None) is None


def test_display_adds_thousands_separators():
    assert display(198540960) == "198,540,960"
    assert display(6.165544509887695) == "6.17"
    assert display(123041.82) == "123,042"
    assert display(None) is None


def test_display_pct_is_signed_and_rounded():
    assert display_pct(2.5) == "+2.50%"
    assert display_pct(-1.234) == "-1.23%"
    assert display_pct(None) is None
