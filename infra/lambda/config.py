"""Deployment configuration read only at the handler boundary."""

import math
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    bucket: str
    public_base_url: str
    max_input_bytes: int = 512 * 1024 * 1024
    max_duration_s: float = 120
    storage_reserve_bytes: int = 512 * 1024 * 1024

    def __post_init__(self) -> None:
        if self.max_input_bytes <= 0 or self.storage_reserve_bytes < 0:
            raise ValueError("input/storage limits must be nonnegative with a positive input limit")
        if not math.isfinite(self.max_duration_s) or self.max_duration_s <= 0:
            raise ValueError("duration limit must be finite and positive")

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            bucket=os.environ["MEDIA_BUCKET"],
            public_base_url=os.environ["PUBLIC_BASE_URL"].rstrip("/"),
            max_input_bytes=int(os.environ.get("MAX_INPUT_BYTES", 512 * 1024 * 1024)),
            max_duration_s=float(os.environ.get("MAX_DURATION_S", 120)),
        )
