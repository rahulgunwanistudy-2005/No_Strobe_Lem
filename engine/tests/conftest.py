from datetime import UTC, datetime
from pathlib import Path

import pytest

from nostrobe.config import Settings
from nostrobe.domain.models import (
    HazardEvent,
    HazardTrack,
    MediaInfo,
    TrackStats,
    VeilCue,
    VerifierResult,
)
from nostrobe.domain.profiles import get_profile


@pytest.fixture
def track() -> HazardTrack:
    event = HazardEvent(
        id="evt_0001",
        kind="luma_flash",
        severity="fail",
        t_start=1,
        t_end=2,
        peak_changes_per_s=8,
        peak_area_fraction=1,
        peak_delta_cd_m2=60,
        regime="absolute",
    )
    return HazardTrack(
        format="hazardtrack",
        format_version="1.0",
        profile="broadcast",
        media=MediaInfo(
            content_id="example",
            duration_s=3,
            fps=25,
            width=640,
            height=360,
            transfer="sdr",
            source_sha256="0" * 64,
        ),
        events=[event],
        veils=[
            VeilCue(
                id="veil_0001",
                t_on=0.75,
                t_off=2.25,
                ramp_in_s=0.5,
                ramp_out_s=0.5,
                alpha=0.5,
                gray=0.25,
                covers=[event.id],
            )
        ],
        verifier=VerifierResult(
            passes=True,
            offsets_checked_s=[-0.15, 0, 0.15],
            residual_events=[],
            engine_version="0.1.0",
            params_hash=get_profile("broadcast").params_hash(),
        ),
        generated_at=datetime(2026, 10, 4, tzinfo=UTC),
        stats=TrackStats(
            veiled_fraction_of_runtime=0.5, mean_alpha=0.5, n_events_by_kind={"luma_flash": 1}
        ),
    )


@pytest.fixture
def config(tmp_path: Path) -> Settings:
    return Settings(repo_root=tmp_path)
