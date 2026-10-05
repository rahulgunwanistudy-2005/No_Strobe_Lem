"""Shared array types without detector/kernel import cycles."""

import numpy as np
from numpy.typing import NDArray

BoolArray = NDArray[np.bool_]
IntArray = NDArray[np.int64]
