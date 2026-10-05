"""Versioned product profiles; conservative choices are not standards."""

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Literal

from nostrobe.domain.models import ProfileId
from nostrobe.errors import ProfileError

PARAMS_VERSION = "1.1"


@dataclass(frozen=True)
class ProfileParams:
    profile: ProfileId
    area_rule: Literal["global", "local"]
    max_changes_per_s: int
    veil_warn: bool
    red_rule: bool = True
    area_threshold: float = 0.25
    min_ramp_s: float = 0.5
    lead_s: float = 0.25
    tail_s: float = 0.25
    merge_gap_s: float = 1.0
    sync_tolerance_s: float = 0.26887499999999925  # eval/sync_calibration.json, VVD S5.
    gray_candidates: tuple[float, ...] = (0.0, 0.25, 0.5)
    alpha_step: float = 0.02
    max_alpha: float = 0.85
    leading_edge_spacing_s: float = 0.36  # Conservative product generalization.
    extended_duration_s: float = 5.0
    extended_changes_per_s: int = 3
    extended_area: float = 0.25  # Product choice; see docs/INTERPRETATIONS.md.

    def params_hash(self) -> str:
        payload = {"params_version": PARAMS_VERSION, "params": asdict(self)}
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
        return hashlib.sha256(canonical.encode()).hexdigest()


def get_profile(profile: str) -> ProfileParams:
    match profile:
        case "broadcast":
            return ProfileParams("broadcast", "global", 6, False)
        case "local":
            return ProfileParams("local", "local", 6, False)
        case "kids":
            return ProfileParams("kids", "local", 4, True)
        case _:
            raise ProfileError(f"unknown profile: {profile}")


def params_hash(params: ProfileParams) -> str:
    return params.params_hash()
