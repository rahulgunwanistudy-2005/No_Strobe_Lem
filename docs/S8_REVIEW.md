# S8 engineering review

Reviewed the product engine, TV state transitions, ingest adapter/policy and
extracted reference source. The portable `engine/src` and `spec` tracked files
match the reference repository across all 66 compared paths. Separate Ubuntu
CI verifies the extracted library rather than relying on the product tests.

| Requested edge | Behavior and verification |
|---|---|
| Zero-length video | Zero-byte and corrupt files raise typed DecodeError; invalid zero/negative/nonfinite frame rates are refused. `engine/tests/decode/test_hardening.py` covers five malformed rates and actual bad files. |
| VFR video | Existing `test_variable_frame_rate_timestamps` decodes an encoded VFR sample with monotonic original timestamps. Rational integer PTS regressions cover 24/30/60 fps boundaries. |
| 4K input | Actual 3840×2160 silent input decodes two frames into bounded 640×360 Y/RGB planes; original source dimensions remain intact in metadata. |
| Missing audio | The encoded 4K sample and bundled native demo have no audio; analysis and actual VVD playback succeed. Audio is not a detector input. |
| Corrupt file | Actual malformed bytes and failed probe paths raise typed errors, rather than emitting playable output. |
| HLS catalog URL | Unit checks retain the exact HTTPS playlist/signed URL and source binding while refusing credentials, fragments, whitespace and backslashes. No actual HLS stream playback is claimed. |
| Profile without events | `test_analyze_verify_report_default_profiles_and_binding` analyzes flat video in all three profiles, emits no veils, verifies JSON/WebVTT equality, and writes a trace-only report. |
| Unresolved/veiled overlap | TV regressions traverse mixed chained overlaps and clamp at the end. Invalid/unresolved sidecars still refuse protected playback entirely. Diagnostic skip mapping is not a playable fallback. |
| Seek storms | Thirty same-turn remote events issue one native seek; premature completion is ignored. Native exceptions stay covered. A media error cancels deferred native dispatch; removing that guard makes the regression fail. Actual VVD skip reaches 12 seconds; fresh-clone native scrubber seeks remain usable. |

Findings fixed in separate commits: zero-denominator probe exceptions; React
state-only seek serialization; native-seek exceptions and queued dispatch after
media error; permissive catalog credentials/fragments; nonfinite ingest limits;
size checks trusting only declared ContentLength; image-check orphan cleanup;
and unsupported dependency versions with compatible published fixes.

The ingest review retains checksum/ETag binding, verified-only publication,
streamed limits, decoded-storage preflight, catalog conflict relisting and
failure propagation. S3 anonymous read applies only to `public/*`; source
review does not establish the deployed policy. [Security findings](SECURITY.md)
record the remaining advisories and live AWS boundary.

The complete engine suite passes 431 tests, infra 16, TV 53 and extracted
reference Ubuntu CI 429. The clean checkout uses new Python/Node environments
on the existing host, with its own Release package installed and launched on
VVD. A first unchanged TV wait timed out under concurrent work; isolated repeat
and final checks pass, with both receipts preserved. [Evidence](evidence/s8/)
separates screenshots, unit/quality output, local-container checks and historical
device calibration.

No detector thresholds, seeds, truth, profile protection or test assertions
were weakened to obtain a result. Current functional snapshots do not replace
timing/compositing measurements. Full evaluation/determinism and the remaining
submission gates are recorded in [S8_REPORT.md](S8_REPORT.md).
