# Lessons

- User commit authorization takes precedence over the build pack's default manual-commit rule.
- Validate published source wording before implementing thresholds; product interpretations must be labeled separately.

- BT.1702-3 specifies the ≥160 relative rule for HDR; the brief's fixed leading-edge spacing is a product generalization, not the full published wording.
- Use integer frame indices for sampled one-second truth windows to avoid false extra changes at floating-point boundaries.
- Specify matching input/output color metadata as well as encoder VUI metadata; inspect ffprobe output rather than assuming flags worked.
- Spatial averaging must follow conversion to cd/m². The initial grid failed the hard-edge test; raised resolution and synthesis fidelity passed the unchanged <1 cd/m² gate.
- WCAG's red-threshold note leaves RGB transfer implicit. Document linearization as an interpretation and do not assume two saturated BT.709 colors can exceed a 0.2 chromaticity distance; independently check the chosen test colors.

- S2: a 0.34 s flash period does not itself imply >3 flashes/s; both temporal
  and area criteria are still required. Spacing eligibility and rate failure
  need separate boundary checks.
- Kids can fail isolated triples because its product limit is >4 changes;
  use per-profile truth and timing, not Broadcast truth relabeled for all profiles.
- Batched cell masks preserve per-cell temporal counts while avoiding redundant
  frame timestamp storage. Benchmark decode/cell conversion separately from
  detector time and report an unmet performance target honestly.
- Explicit BT.709 conversion requires explicit BT.709 source tags in S2;
  earlier luma-only support for other SDR transfer tags does not imply RGB support.
- Track both startup extrema before a direction is registered. A first sample
  inside a later qualifying range can otherwise hide all subsequent flashes.
  Red detection likewise needs observed startup color endpoints, not only the
  first RGB sample. Regression tests cover both luma directions and red at all fps.
