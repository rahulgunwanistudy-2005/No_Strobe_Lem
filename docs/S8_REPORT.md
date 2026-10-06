# Session 8 — hardening and submission readiness

S8 implementation, documentation, evaluation and local verification are
complete, with reproducible receipts below. **Submission acceptance is not yet
complete:** the SDK dependency graph retains high advisories; authenticated
live AWS validation and its demo shot are unavailable; existing VVD video-drop
and unadjudicated natural-film limitations remain. A product `v1.0.0` tag is
withheld while these gates are open.

## Built

- Typed malformed-frame-rate refusal, including zero denominators; encoded 4K,
  silent, corrupt and zero-byte input regressions preserve bounded decoding.
- Synchronous seek serialization before React state updates, ignored premature
  completions, and covered native-seek errors; signed HTTPS/HLS URL acceptance
  with credentials/fragments/backslashes refused. HLS playback is unmeasured.
- Finite positive ingest configuration, streamed-size and disk-preflight
  regressions. Input/source/profile/verifier refusal is unchanged.
- Tested dependency overrides and a pinned `v0.1.1` reference wheel; source-build
  pins match. Image checks remove their own timed-out containers.
- Runtime-hook README, engine/TV/AWS quickstarts, architecture, source-linked
  prior art and a reproducible 20-second nonflashing schematic GIF.
- Consolidated per-tool feedback, 12 distinct reproduced friction entries with
  preserved historical detail, five evidence-backed feature requests, honest
  Devpost/Q&A drafts and shot-by-shot demo readiness/reviewer-access notes.
- Submission table generator refuses incomplete/stale engine provenance; copy
  checker binds result checksums, compares every public table, validates links,
  refuses prohibited claims and checks friction entry fields.

## Verification checkpoints

- Product engine: 431 tests pass; lint/format/strict types pass. The complete
  suite was run alongside evaluation; timings are not isolated benchmarks.
- Reference patch: independent Ubuntu CI passes 429 extracted tests, lint,
  format, strict types, schema, 500 browser timeline samples and wheel release.
  [Tagged CI](https://github.com/rahul-software-dev/hazardtrack/actions/runs/37448503294).
- TV: 53 tests / 9 suites, strict types, ESLint and all Release architecture
  builds pass after remediation. Native package content excludes calibration
  media. Current actual catalog/player/settings captures are in `evidence/s8/`.
- Infra: 16 tests, lint/format/strict types and SAM lint/build pass against the
  published dependency. The updated read-only amd64 image passes all three
  source-bound JSON/VTT profiles with no live AWS service; exact image/size is
  recorded in `evidence/s8/container-validation.json`.
- Python and root contract npm audits report no known findings. Gitleaks scans
  both reachable histories and the tracked archive with no reported leak.
  TV findings remain explicit in `SECURITY.md` and raw official audit reports.
- Fresh local clone: new locked Python/Node environments, 431 engine tests,
  strict types/lint/format/generated contracts and 53 TV tests pass; all Release
  architectures build. Its actual aarch64 package installs/launches and plays
  on VVD. First concurrent TV run had a timed catalog wait (51/52); isolated
  retry (52/52) and final post-guard suite (53/53) pass with unchanged assertions.
  This uses the existing host/toolchain, not a freshly installed OS.
- Current-provenance evaluation: all 978 outcomes complete; FN=FP=0 in all
  three profiles, 975/975 tracks verify at −268.875/0/+268.875 ms, unresolved=0.
  The 325 scored clips comprise 120 boundaries, 200 shapes and five composites;
  the full-film control's three outcomes remain outside confusion scores.
  Two complete default runs recomputed accuracy/mitigation/verification without
  --resume. Results JSON/Markdown and both numerical/image control traces are
  byte-identical. [Current determinism proof](../engine/eval/s8_determinism.json)
  preserves implementation/manifest/calibration hashes and timing policy.
  The first call began with the 0.1.1 changes before committing them; its
  recorded checkout HEAD is historical, while its implementation hash matches
  the current committed engine tree. Original S4 proof remains unchanged.
- Product independent Ubuntu CI passes all 431 engine tests, 16 infra tests,
  contracts, SAM validate/build and read-only image validation. The corrected
  helper records Linux x86_64, and local receipt records Darwin arm64.
  [Product CI](https://github.com/rahulgunwanistudy-2005/No_Strobe_Lem/actions/runs/37474690435).
- README, Devpost and Q&A tables match; copy/link/checksum checks and 12
  distinct friction entries pass.
- [Engineering review](S8_REVIEW.md) maps all requested edge cases to evidence.

## Review decisions and scope

The user's explicit commit authorization overrides the build pack's manual
commit default. Stage messages contain no attribution trailers; existing Git
history/tags are not rewritten. The original demo/Devpost/Q&A files are draft
source material: unsupported cloud/medical/novelty claims are not copied into
public submission text. Original source-corrected SDR interpretations and
independent ground truth remain unchanged.

The 12-second native demo is not a must-fail hazard example. Broadcast/Local
catalog veils are illustrative; Kids suppresses warning events. The numerical
report command performs real analysis rather than inventing a hazard count.
VVD restarted after becoming unavailable; rejected/black initial frames remain
diagnostic snapshots and cannot be used as calibration evidence. Current
functional checks do not replace S5 measurements or S6 drop reports.

The first image check on the moving 12-second sample exceeded its 300-second
utility timeout and left the Docker container running. Exact identity/mounts
were checked before removing that orphan. A repeated check on the existing
constant-gray source passed all unchanged assertions; it is an adapter/container
check, not a Lambda latency measurement. The helper now owns cleanup through a
container-id file in a finally block.

## Remaining acceptance gates

- Resolve the upstream braces advisory through a compatible published fix and
  repeat official audits/builds; no clean-security or final-release claim.
- Supply an authenticated AWS profile/region, deploy, upload an attributed
  sample, measure real timing/cost, test anonymous public/ingest access, exercise
  the deployed catalog on VVD, and tear down.
- Record/review the live cloud shot and final narrated/captioned demonstration;
  verify every edited frame before asserting no flashing and publish its URL.
- Keep physical-TV calibration, original-film adjudication, PEAT and the S6
  zero-drop objective visible as scope limits.

Product source is public on main and GitHub recognizes Apache-2.0, using the
existing owner Git account; no visibility/access-list change or invitation.
Frozen tables, numerical results, traces and the complete-repeat proof are
published with the final plain commits.
