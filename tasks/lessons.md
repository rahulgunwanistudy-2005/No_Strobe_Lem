# Lessons

- User commit authorization takes precedence over the build pack's default manual-commit rule.
- Validate published source wording before implementing thresholds; product interpretations must be labeled separately.

- BT.1702-3 specifies the ≥160 relative rule for HDR; the brief's fixed leading-edge spacing is a product generalization, not the full published wording.
- Use integer frame indices for sampled one-second truth windows to avoid false extra changes at floating-point boundaries.
- Specify matching input/output color metadata as well as encoder VUI metadata; inspect ffprobe output rather than assuming flags worked.
- Spatial averaging must follow conversion to cd/m². The initial grid failed the hard-edge test; raised resolution and synthesis fidelity passed the unchanged <1 cd/m² gate.
- WCAG's red-threshold note leaves RGB transfer implicit. Document linearization as an interpretation and do not assume two saturated BT.709 colors can exceed a 0.2 chromaticity distance; independently check the chosen test colors.
