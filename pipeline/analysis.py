"""Analysis helpers shared by the notebooks and the tests."""
import numpy as np


def log_decompose(p0, p1, e0, e1):
    """Split the change in the price-to-earnings ratio into a price part and an earnings part.

    p0, p1: median price in the first and last year.
    e0, e1: median earnings in the first and last year.
    Returns (d_ratio, d_price, d_earn), where d_ratio = d_price - d_earn exactly.
    Works on single numbers or whole pandas columns.
    """
    d_price = np.log(p1) - np.log(p0)
    d_earn = np.log(e1) - np.log(e0)
    d_ratio = np.log(p1 / e1) - np.log(p0 / e0)
    return d_ratio, d_price, d_earn