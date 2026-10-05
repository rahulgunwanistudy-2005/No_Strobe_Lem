"""Single-core state kernels; strict arithmetic, no fastmath or parallel workers."""

import math
from collections.abc import Callable
from typing import cast

import numpy as np
from numba import njit
from numpy.typing import NDArray

from nostrobe.detect.zigzag_types import BoolArray, IntArray
from nostrobe.luminance.curve import FloatArray


def _kernel[**P, R](function: Callable[P, R]) -> Callable[P, R]:
    return cast(Callable[P, R], njit(cache=True, fastmath=False, parallel=False)(function))


@_kernel
def color_features(values: FloatArray, xyz: FloatArray) -> tuple[FloatArray, BoolArray]:
    uv = np.empty((2, len(values)))
    saturated = np.empty(len(values), dtype=np.bool_)
    for i in range(len(values)):
        den = xyz[i, 0] + 15 * xyz[i, 1] + 3 * xyz[i, 2]
        uv[0, i] = 4 * xyz[i, 0] / den if den > 0 else 0
        uv[1, i] = 9 * xyz[i, 1] / den if den > 0 else 0
        total = values[i, 0] + values[i, 1] + values[i, 2]
        ratio = values[i, 0] / total if total > 0 else 0
        saturated[i] = ratio >= 0.8
    return uv, saturated


@_kernel
def sdr_crossings(
    values: FloatArray,
    extreme: FloatArray,
    anchor: FloatArray,
    direction: NDArray[np.signedinteger],
    delta: FloatArray,
) -> BoolArray:
    changes = np.empty(values.shape, dtype=np.bool_)
    for y in range(values.shape[0]):
        for x in range(values.shape[1]):
            v, e, a, d = values[y, x], extreme[y, x], anchor[y, x], direction[y, x]
            forward = (v - e) * d >= 0
            reference = a if forward else e
            if d == 0 and abs(v - e) > abs(v - a):
                reference = e
            signed = v - reference
            amplitude = abs(signed)
            delta[y, x] = amplitude
            change = amplitude >= 20 and min(v, reference) < 160
            changes[y, x] = change
            if change:
                d = 1 if signed > 0 else -1
                direction[y, x] = d
                anchor[y, x] = v
            if d == 0:
                anchor[y, x] = min(a, v)
                extreme[y, x] = max(e, v)
            elif forward or change:
                extreme[y, x] = v
    return changes


@_kernel
def red_crossings(
    uv: FloatArray,
    saturated: BoolArray,
    anchor: FloatArray,
    extreme: FloatArray,
    anchor_sat: BoolArray,
    extreme_sat: BoolArray,
    previous_direction: IntArray,
) -> tuple[BoolArray, IntArray]:
    changes = np.empty(saturated.shape, dtype=np.bool_)
    directions = np.empty(saturated.shape, dtype=np.int64)
    for y in range(saturated.shape[0]):
        for x in range(saturated.shape[1]):
            u, v = uv[0, y, x], uv[1, y, x]
            au, av = u - anchor[0, y, x], v - anchor[1, y, x]
            eu, ev = u - extreme[0, y, x], v - extreme[1, y, x]
            da = math.sqrt(au * au + av * av)
            de = math.sqrt(eu * eu + ev * ev)
            dominant = eu if abs(eu) >= abs(ev) else ev
            step = 1 if dominant > 0 else -1 if dominant < 0 else 0
            old = previous_direction[y, x]
            forward = step == old or step == 0
            unset = old == 0
            use_extreme = de > da if unset else not forward
            reference_sat = extreme_sat[y, x] if use_extreme else anchor_sat[y, x]
            change = (saturated[y, x] or reference_sat) and (de if use_extreme else da) > 0.2
            du, dv = (eu, ev) if use_extreme else (au, av)
            dominant = du if abs(du) >= abs(dv) else dv
            direction = 1 if dominant > 0 else -1 if dominant < 0 else 0
            changes[y, x], directions[y, x] = change, direction
            su = extreme[0, y, x] - anchor[0, y, x]
            sv = extreme[1, y, x] - anchor[1, y, x]
            span = math.sqrt(su * su + sv * sv)
            if (unset and not change and de > span and use_extreme) or change:
                anchor[0, y, x], anchor[1, y, x] = u, v
                anchor_sat[y, x] = saturated[y, x]
            if (
                (unset and not change and da > span and not use_extreme)
                or (forward and not unset)
                or change
            ):
                extreme[0, y, x], extreme[1, y, x] = u, v
                extreme_sat[y, x] = saturated[y, x]
            if change:
                previous_direction[y, x] = direction
    return changes, directions


@_kernel
def local_area(mask: BoolArray, height: int, width: int) -> float:
    table = np.zeros((mask.shape[0] + 1, mask.shape[1] + 1), dtype=np.int64)
    for y in range(mask.shape[0]):
        row = 0
        for x in range(mask.shape[1]):
            row += mask[y, x]
            table[y + 1, x + 1] = table[y, x + 1] + row
    maximum = 0
    for y in range(height, table.shape[0]):
        for x in range(width, table.shape[1]):
            total = (
                table[y, x]
                - table[y - height, x]
                - table[y, x - width]
                + table[y - height, x - width]
            )
            maximum = max(maximum, total)
    return maximum / (height * width)


@_kernel
def pair_edges(
    changes: BoolArray,
    direction: NDArray[np.signedinteger],
    t: float,
    spacing_s: float,
    previous_direction: NDArray[np.signedinteger],
    pending: BoolArray,
    lead: FloatArray,
    previous_lead: FloatArray,
    previous_tail: FloatArray,
    previous_counted: BoolArray,
    dense_flash: BoolArray,
) -> tuple[BoolArray, BoolArray, BoolArray, BoolArray]:
    edges = np.zeros(changes.shape, dtype=np.bool_)
    retro_lead = np.zeros(changes.shape, dtype=np.bool_)
    retro_tail = np.zeros(changes.shape, dtype=np.bool_)
    dense = np.zeros(changes.shape, dtype=np.bool_)
    for y in range(changes.shape[0]):
        for x in range(changes.shape[1]):
            d = direction[y, x]
            if not changes[y, x] or d == 0 or d == previous_direction[y, x]:
                continue
            edges[y, x] = True
            if not pending[y, x]:
                close = t - previous_lead[y, x] < spacing_s - 1e-9
                retro = close and not previous_counted[y, x]
                retro_lead[y, x] = retro and previous_lead[y, x] > t - 1 + 1e-9
                retro_tail[y, x] = retro and previous_tail[y, x] > t - 1 + 1e-9
                dense_flash[y, x] = close
                lead[y, x] = t
                dense[y, x] = close
                pending[y, x] = True
            else:
                dense[y, x] = dense_flash[y, x]
                previous_lead[y, x] = lead[y, x]
                previous_tail[y, x] = t
                previous_counted[y, x] = dense_flash[y, x]
                pending[y, x] = False
            previous_direction[y, x] = d
    return edges, retro_lead, retro_tail, dense
