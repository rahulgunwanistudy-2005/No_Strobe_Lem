/* Generated from HazardTrack JSON Schema. Do not edit. */

export type Id = string;
export type Kind = "luma_flash" | "red_flash" | "extended_flashing";
export type PeakAreaFraction = number;
export type PeakChangesPerS = number;
export type PeakDeltaCdM2 = number | null;
export type Regime = "absolute" | "relative" | "red";
export type Severity = "fail" | "warn";
export type TEnd = number;
export type TStart = number;
export type Events = HazardEvent[];
export type Format = "hazardtrack";
export type FormatVersion = "1.0";
export type GeneratedAt = string;
export type ContentId = string;
export type DurationS = number;
export type Fps = number;
export type Height = number;
export type SourceSha256 = string;
export type Transfer = "sdr";
export type Width = number;
export type Profile = "broadcast" | "local" | "kids";
export type MeanAlpha = number;
export type VeiledFractionOfRuntime = number;
export type Alpha = number;
export type Covers = string[];
export type Gray = number;
export type Id1 = string;
export type RampInS = number;
export type RampOutS = number;
export type TOff = number;
export type TOn = number;
export type Veils = VeilCue[];
export type EngineVersion = string;
export type OffsetsCheckedS = number[];
export type ParamsHash = string;
export type Passes = boolean;
export type ResidualEvents = HazardEvent[];

export interface HazardTrack {
  events: Events;
  format: Format;
  format_version: FormatVersion;
  generated_at: GeneratedAt;
  media: MediaInfo;
  profile: Profile;
  stats: TrackStats;
  veils: Veils;
  verifier: VerifierResult;
  [k: string]: unknown;
}
export interface HazardEvent {
  id: Id;
  kind: Kind;
  peak_area_fraction: PeakAreaFraction;
  peak_changes_per_s: PeakChangesPerS;
  peak_delta_cd_m2: PeakDeltaCdM2;
  regime: Regime;
  severity: Severity;
  t_end: TEnd;
  t_start: TStart;
  [k: string]: unknown;
}
export interface MediaInfo {
  content_id: ContentId;
  duration_s: DurationS;
  fps: Fps;
  height: Height;
  source_sha256: SourceSha256;
  transfer: Transfer;
  width: Width;
  [k: string]: unknown;
}
export interface TrackStats {
  mean_alpha: MeanAlpha;
  n_events_by_kind: NEventsByKind;
  veiled_fraction_of_runtime: VeiledFractionOfRuntime;
  [k: string]: unknown;
}
export interface NEventsByKind {
  [k: string]: number;
}
export interface VeilCue {
  alpha: Alpha;
  covers: Covers;
  gray: Gray;
  id: Id1;
  ramp_in_s: RampInS;
  ramp_out_s: RampOutS;
  t_off: TOff;
  t_on: TOn;
  [k: string]: unknown;
}
export interface VerifierResult {
  engine_version: EngineVersion;
  offsets_checked_s: OffsetsCheckedS;
  params_hash: ParamsHash;
  passes: Passes;
  residual_events: ResidualEvents;
  [k: string]: unknown;
}
