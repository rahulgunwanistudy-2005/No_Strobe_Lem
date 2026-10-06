# S8 evidence

Actual local receipts only. Current screenshots are native SDK rendered images,
not mocks. `player.png` is an initial black/loading diagnostic; use
`playback-ready.png` for visible playback. Neither is timing calibration.
`catalog.png` and `settings.png` show current Release UI. Original request and
SDK timestamps are in their adjacent JSON files. `profile-kids.png`, `kids-playback.png`, `skip-focus.png` and `skipped.png`
show the native Kids policy and actual skip to the 12-second end. Their input
receipts retain dispatch/receipt times; the focus sequence includes two Up
presses before OK. `kids-source-unavailable.png` shows covered source-fetch
failure. `fresh-playback.png` and `fresh-seek.png` use the final 53-test clean
checkout's Release package; reinstall resets the household to Broadcast.
Earlier performance measurements remain under S5/S6 with their own provenance.

- `engine-tests.txt`: complete product quality checkpoint (431 tests).
- `infra-tests.txt`: 16 pipeline/configuration regressions against reference v0.1.1.
- `container-validation.json`: checksum-pinned wheel in actual read-only image,
  three bound profiles/VTT equality and size; in-memory S3, not AWS.
- `sam-build.txt`: actual updated image/SAM build.
- `release-contents.txt`: native Release excludes calibration stimuli.
- `demo-verification.txt`: analyzed source at current engine version and offsets.
- `*-audit.json`: live published advisory responses, with unresolved TV findings.
- `secrets-*.json`: redacted Gitleaks results; empty arrays mean no finding in
  the specified history/compiled tracked-file scope, not absolute assurance.
- `fresh-clone.json` and `fresh-*.txt`: new environments, full quality gates and
  actual native install/launch; existing host/toolchain, not a new operating system.
- `fresh-tv-first-run.txt` preserves the catalog wait timeout (51/52);
  `fresh-tv-retry.txt` the isolated 52/52 repeat; `fresh-tv-final.txt` passes 53/53
  after the queued-seek cancellation guard. Assertions/timeouts are unchanged.
- `seek-guard-negative.txt`: deliberately removed guard causes the new
  regression to fail; restored source passes the full final TV suite.
- `submission-metrics.json`: current passing evaluation and public-table
  checksums; `copy-check.txt` confirms equal tables, links and friction fields.
- `product-ci-final.json`, `product-ci-final-quality.txt`,
  `ci-container-validation.json`: independently passing Ubuntu product checks
  and actual corrected read-only image receipt.
- Determinism receipts are added after the complete repeat.

The first image validation on the 12 s moving demo hit the unchanged utility
300 s timeout. The retry on the existing constant-gray source passes the same
assertions. Do not use either run as a live Lambda speed/cost observation.

The initial Linux CI artifact `ci-container-validation-initial.json` contains an
incorrect hard-coded Apple Silicon environment label from the old helper. The
job URL and runner logs establish Ubuntu x86_64; its assertions and source/image
checks are valid. The helper now records actual host_system/host_machine and the
corrected CI receipt is retained separately. Original bytes are preserved.
