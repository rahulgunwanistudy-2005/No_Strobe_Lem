"""Seeded S1 primitives extended without altering their original truth."""

from dataclasses import replace

import numpy as np

from nostrobe.synth.generator import ClipSpec, Primitive, smoke_specs


def boundary_specs(seed: int, fps_values: list[int]) -> list[ClipSpec]:
    base = smoke_specs(seed)
    base += [
        ClipSpec("dark_150", "full_flash", dark_cd_m2=150, delta_cd_m2=21),
        ClipSpec("dark_170", "full_flash", dark_cd_m2=170, delta_cd_m2=21),
        ClipSpec("spacing_034", "full_flash", rate=1 / 0.34),
        ClipSpec("spacing_038", "full_flash", rate=1 / 0.38),
        ClipSpec("red_below", "red", rgb_b=(255, 0, 210)),
        ClipSpec("red_above", "red", rgb_b=(255, 0, 220)),
        ClipSpec("quadrant", "regional_rect", area=0.25),
        ClipSpec("glitch", "full_flash", rate=8, duty=0.3),
    ]
    return [
        replace(spec, name=f"{spec.name}_{fps}", fps=fps, seed=seed)
        for fps in fps_values
        for spec in base
    ]


def shape_specs(seed: int, count: int, fps_values: list[int]) -> list[ClipSpec]:
    rng = np.random.default_rng(seed)
    primitives: tuple[Primitive, ...] = (
        "full_flash",
        "regional_rect",
        "regional_tiles",
        "moving_bar",
        "camera_burst",
        "police",
        "lightning",
        "isolated",
        "checker",
        "red",
    )
    result = []
    for index in range(count):
        primitive = primitives[index % len(primitives)]
        fps = int(rng.choice(fps_values))
        dark = float(rng.choice([40, 70, 100, 150, 170]))
        delta = float(rng.choice([19, 21, 28]))
        area = float(rng.choice([0.10, 0.24, 0.26, 0.5, 1]))
        rate = float(rng.choice([2, 3, 3.5, 5, 8]))
        if primitive == "moving_bar":
            area = 0.10  # Existing S1 oracle's supported traversal family.
        result.append(
            ClipSpec(
                name=f"shape_{index:03d}",
                primitive=primitive,
                fps=fps,
                seed=seed + index,
                dark_cd_m2=dark,
                delta_cd_m2=delta,
                area=area,
                rate=rate,
                n_flashes=int(rng.integers(1, 4)),
                duty=float(rng.choice([0.3, 0.5, 0.7])),
            )
        )
    return result
