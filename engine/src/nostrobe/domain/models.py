"""HazardTrack 1.0 contracts from the project bible §9."""

from datetime import UTC, datetime
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

HazardKind = Literal["luma_flash", "red_flash", "extended_flashing"]
Severity = Literal["fail", "warn"]
ProfileId = Literal["broadcast", "local", "kids"]
Nonnegative = Annotated[float, Field(ge=0)]
Fraction = Annotated[float, Field(ge=0, le=1)]


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore", allow_inf_nan=False)


class HazardEvent(FrozenModel):
    id: str
    kind: HazardKind
    severity: Severity
    t_start: Nonnegative
    t_end: Nonnegative
    peak_changes_per_s: Annotated[int, Field(ge=0)]
    peak_area_fraction: Fraction
    peak_delta_cd_m2: Nonnegative | None
    regime: Literal["absolute", "relative", "red"]

    @model_validator(mode="after")
    def ordered_times(self) -> Self:
        if self.t_end <= self.t_start:
            raise ValueError("t_end must exceed t_start")
        return self


class VeilCue(FrozenModel):
    id: str
    t_on: float
    t_off: float
    ramp_in_s: Annotated[float, Field(ge=0.5)]
    ramp_out_s: Annotated[float, Field(ge=0.5)]
    alpha: Fraction
    gray: Fraction
    covers: list[str]

    @model_validator(mode="after")
    def ordered_times(self) -> Self:
        if self.t_off <= self.t_on:
            raise ValueError("t_off must exceed t_on")
        return self


class VerifierResult(FrozenModel):
    passes: bool
    offsets_checked_s: list[float]
    residual_events: list[HazardEvent]
    engine_version: str
    params_hash: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]

    @model_validator(mode="after")
    def consistent_pass(self) -> Self:
        if self.passes and (self.residual_events or not self.offsets_checked_s):
            raise ValueError("passing verification requires checked offsets and no residual events")
        return self


class MediaInfo(FrozenModel):
    content_id: str
    duration_s: Annotated[float, Field(gt=0)]
    fps: Annotated[float, Field(gt=0)]
    width: Annotated[int, Field(gt=0)]
    height: Annotated[int, Field(gt=0)]
    transfer: Literal["sdr"]
    source_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class TrackStats(FrozenModel):
    veiled_fraction_of_runtime: Fraction
    mean_alpha: Fraction
    n_events_by_kind: dict[HazardKind, Annotated[int, Field(ge=0)]]
    mean_delta_cd_m2: Nonnegative = 0.0


class UnresolvedSegment(FrozenModel):
    start: Nonnegative
    end: Nonnegative
    covers: list[str]
    reason: Annotated[str, Field(min_length=1)]

    @model_validator(mode="after")
    def ordered_times(self) -> Self:
        if self.end <= self.start:
            raise ValueError("unresolved segment end must exceed start")
        return self


class HazardTrack(FrozenModel):
    format: Literal["hazardtrack"]
    format_version: Literal["1.0"]
    profile: ProfileId
    media: MediaInfo
    events: list[HazardEvent]
    veils: list[VeilCue]
    verifier: VerifierResult
    generated_at: datetime
    stats: TrackStats
    unresolved_segments: list[UnresolvedSegment] = Field(default_factory=list)

    @field_validator("generated_at")
    @classmethod
    def utc_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def event_references(self) -> Self:
        if self.verifier.passes and self.unresolved_segments:
            raise ValueError("passing tracks cannot contain unresolved segments")
        ids = [event.id for event in self.events]
        if len(set(ids)) != len(ids):
            raise ValueError("event ids must be unique")
        if len({cue.id for cue in self.veils}) != len(self.veils):
            raise ValueError("veil ids must be unique")
        if any(event.t_end > self.media.duration_s for event in self.events):
            raise ValueError("events must lie within the media timeline")
        if any(set(cue.covers) - set(ids) for cue in self.veils):
            raise ValueError("veil covers must reference existing event ids")
        return self
