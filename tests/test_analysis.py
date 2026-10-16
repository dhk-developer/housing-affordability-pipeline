import math

import pytest

from pipeline.analysis import log_decompose


def test_parts_add_up():
    d_ratio, d_price, d_earn = log_decompose(200_000, 260_000, 30_000, 33_000)
    assert d_ratio == pytest.approx(d_price - d_earn)


def test_no_change_gives_zeros():
    assert log_decompose(250_000, 250_000, 35_000, 35_000) == pytest.approx((0, 0, 0))


def test_price_doubling_with_flat_pay():
    d_ratio, d_price, d_earn = log_decompose(100_000, 200_000, 30_000, 30_000)
    assert d_price == pytest.approx(math.log(2))
    assert d_earn == pytest.approx(0)
    assert d_ratio == pytest.approx(math.log(2))