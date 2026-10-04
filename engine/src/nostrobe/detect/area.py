"""Typed scaffold for a gated later session."""

import numpy as np
from numpy.typing import NDArray

from nostrobe.domain.profiles import ProfileParams


def area_fraction(mask: NDArray[np.bool_], params: ProfileParams) -> float:
    raise NotImplementedError("area rules begin in S2")
