"""Deployment configuration read only at the handler boundary."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    bucket: str
    public_base_url: str
    max_input_bytes: int = 512 * 1024 * 1024
    max_duration_s: float = 120
    storage_reserve_bytes: int = 512 * 1024 * 1024

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            bucket=os.environ["MEDIA_BUCKET"],
            public_base_url=os.environ["PUBLIC_BASE_URL"].rstrip("/"),
            max_input_bytes=int(os.environ.get("MAX_INPUT_BYTES", 512 * 1024 * 1024)),
            max_duration_s=float(os.environ.get("MAX_DURATION_S", 120)),
        )
