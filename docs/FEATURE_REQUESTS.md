# Feature requests

Only requests tied to observed friction are included; no assertion is made about untested platform features.

| Priority | Request | Why / actual observation |
|---|---|---|
| Critical | Remove deleted raw assets when producing incremental Release packages | FL-004: Debug calibration media persisted after source removal; application-level cleanup and content checks now compensate. |
| Important | Provide a supported VVD screenshot/recording CLI with original acquisition timestamps and pacing | FL-005: AVFoundation, screenshooter and QMP did not yield usable rendered evidence. The SDK controller eventually did, with substantial discovery and acquisition work. |
| Important | Align storage documentation and template dependencies with the SDK's RN compatibility map | FL-008: legacy storage silently lost Kids/Off after restart; the supported extension passed the same native test. |
| Important | Improve native media URI error messages and complete media manifest examples | FL-002/003/006: omitted player-session/system-audio permissions and insecure-URI refusal required runtime-log diagnosis; code 4 had an empty message. |
| Important | Publish SDK dependency remediation guidance and compatible patched template locks | S8 audit retains high findings with no available upstream patch for braces and a legacy manifest parser. Framework downgrades suggested by npm audit conflict with this SDK's tested mapping. |
