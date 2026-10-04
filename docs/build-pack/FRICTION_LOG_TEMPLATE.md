# Friction log entry format (copy into docs/FRICTION_LOG.md)

Log at the moment it happens. Real, reproduced issues only. One entry per distinct issue.

```
### FL-NNN — <short title>
- Product / tool: <Vega SDK x.y | Vega Virtual Device | W3C Media for Vega | Builder Tools MCP | AWS SAM | Lambda | S3 | Kiro | ...>
- Date / version: <YYYY-MM-DD, versions, host OS>
- Task attempted: <what you were trying to do>
- Steps taken: <numbered, with exact commands>
- Expected: <...>
- Actual: <... include error text, trimmed>
- Severity: Blocker | Major | Minor | Cosmetic
- Workaround: <what you did, or "none">
- Suggestion: <one actionable change to docs/tooling/API>
```

Candidates to watch for (log only if you actually hit them): host-OS restrictions of the Vega SDK; VVD screen-recording path; `timeupdate` granularity vs frame-accurate needs; metadata text-track support in Vega W3C media; native-driven Animated on Vega; storage API discoverability; Lambda container + ffmpeg packaging; S3 public-prefix policy ergonomics.
