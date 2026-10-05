# Friction log

Entries below describe reproduced issues only. SDK availability and test results are recorded in PRODUCT_FEEDBACK.md.

### FL-001 — CLI tool execution hides required argument schema
- Product / tool: Amazon Devices Builder Tools MCP CLI
- Date / version: 2026-10-04; 1.0.15; Node 24.19.0; macOS 26.3 arm64
- Task attempted: Retrieve installation workflows using the documented CLI `exec` route.
- Steps taken: 1. `npx -y @amazon-devices/amazon-devices-buildertools-mcp@1.0.15 --help`; 2. `npx -y @amazon-devices/amazon-devices-buildertools-mcp@1.0.15 exec --list`; 3. `npx -y @amazon-devices/amazon-devices-buildertools-mcp@1.0.15 exec list_documents --args '{"documentType":"WORKFLOW"}'`.
- Expected: Tool list/help exposes a complete input schema or a valid invocation example.
- Actual: `Schema validation failed: data must have required property 'target_platform'`. Follow-up validation establishes it is an object requiring an array `device_os`. The help lists tool descriptions but no argument schemas.
- Severity: Minor
- Workaround: `--args '{"documentType":"WORKFLOW","target_platform":{"device_os":["vega"]}}'` retrieves the workflow inventory. `read_document` uses `document_uri`, not `name`.
- Suggestion: Add `exec <tool> --schema` and print required argument types plus an example on validation failure.

## Session 2 update — 2026-10-04

Standards PDFs were readable and the combined ffmpeg Y/RGB stream matched
separate decodes byte for byte. No new external-tool blocker was reproduced.
The detection throughput target remains unmet; profiling and measured results
are recorded in S2_REPORT.md and s2_benchmark.json as an implementation
limitation, rather than attributed to a vendor without evidence.

## Session 3 update — 2026-10-04

No new external-tool blocker was reproduced. Repeated verification on the
encoded area cases was slow, so exact sample-history grouping was added:
byte-identical cell histories share change counters, then counts expand back
to the original grid for global/local area decisions. Equivalence checks use
exact array equality and all-profile event equality. This is an implementation
optimization, not vendor friction. The first film cache preparation completed;
that analysis was interrupted during development, so the recorded final film
benchmark explicitly starts with a warm decode cache. Concurrent validation
activity is recorded rather than presenting the timing as an isolated run.

## S4 source access — 2026-10-05

- Firecrawl scrape calls to official Blender license/download pages returned
  `Insufficient credits`; the web reader returned HTTP 402 on the same URLs.
- Reproduction: Firecrawl scrape with `maxAge: 0` for
  `https://peach.blender.org/about/` and `https://mango.blender.org/sharing/`.
- Workaround: direct HTTPS retrieval succeeded with curl; license snapshots
  are retained under `engine/eval/sources/`. No source facts were invented.

## S4 untagged reference releases — 2026-10-05

ffprobe 7.1.1 reports no color_transfer/color_primaries/color_space for the
Blender-hosted Tears of Steel 720p MOV, ToS-4k-1920 MOV, and Sintel 1080p
trailer MP4. The strict probe rejects them with `unsupported or unspecified
transfer: unknown`. Reproduced via ffprobe stream color metadata fields.
No detector checks were weakened. Retained the explicitly BT.709-tagged
Big Buck Bunny original as the full-film control; Tears of Steel is only
an artistic background to explicitly tagged synthetic composites.

## Detection performance follow-up — 2026-10-05

An attempted transposed RGB-to-XYZ matrix multiplication preserved most test
values but changed some 9×12-grid values by up to 1.11e-16. Reproduced with
`engine/tests/detect/test_equivalence.py` against the frozen dd980e5 reference.
The change was rejected; original NumPy matrix multiplication and strict
compiled arithmetic preserve exact measured state and event output. This is
an implementation/numerical issue, not external-tool friction.
