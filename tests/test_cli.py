import pytest

from pipeline.__main__ import parse_years


def test_range():
    assert parse_years("2019-2021") == [2019, 2020, 2021]


def test_single_year_range():
    assert parse_years("2024-2024") == [2024]


@pytest.mark.parametrize("bad", ["2024-2019", "abc", "2019", "2019-20x4", ""])
def test_bad_input(bad):
    with pytest.raises(ValueError):
        parse_years(bad)