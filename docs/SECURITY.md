# Security review — 6 October 2026

**S8 security gate is open.** Published Python dependency audits found no known vulnerabilities, and the root contract npm audit is clean. The TV SDK graph still has high findings after supported remediation; its clean-security acceptance is not asserted.

## Scope and evidence

Gitleaks 8.30.1 scanned both reachable Git histories and a product tracked-file archive with redacted reports; no finding was reported. Final changed files/history are rescanned before delivery. Reports under [evidence/s8](evidence/s8/) contain no discovered secrets. Ignored local device discovery tokens, credentials, decoded media and build environments are excluded from commits.

`pip-audit` queried published advisories in the locked engine and infra environments; the local unpublished package itself cannot be checked against public advisories. [Engine audit](evidence/s8/python-audit.json), [infra audit](evidence/s8/infra-python-audit.json), [contract npm audit](evidence/s8/contracts-audit.json).

The official npm endpoint initially reported 81 TV dependency findings (66 high, 15 moderate). The tested overrides update Lodash to 4.18.1, Minimatch major 3/9 to 3.1.5/9.0.9, affected Ajv major 8 to 8.20.0 and the TOML parser to 4.3.0. The existing parser API remains exercised by ESLint and all native Release architecture builds. React Native, Kepler and W3C Media stay on the measured SDK mapping.

The final audit reports **72 findings: 60 high, 12 moderate, zero critical**. These include inherited dependency chains, not 60 distinct direct flaws. The high root advisory still concerns `braces` ≤3.0.3; the current published versions list contains no newer patched release. Several tooling/SDK packages inherit that finding. Moderate root findings concern fast-xml-parser, sprintf-js and uuid. The exact dependency locations and advisory links are preserved in [before](evidence/s8/tv-audit-before.json) and [after](evidence/s8/tv-audit-after.json) reports. Do not replace a live audit with an offline zero result or upgrade framework mappings solely to silence inherited warnings.

## S3 and Lambda boundaries

- Only `public/*` grants anonymous `s3:GetObject`; no anonymous list/write permission. `ingest/*` remains outside that grant. An explicit transport Deny covers bucket and object ARNs.
- Bucket-owner enforcement, blocked public ACLs, AES256 encryption and GET-only CORS are declared. Account-level public-access controls may still prevent public hosting; only a real anonymous HTTP test can establish deployment behavior.
- Function IAM reads `ingest/*`, reads/writes `public/*` and lists only `public/*` prefixes. S3 event filters require the ingest prefix and MP4 suffix; the handler independently checks source, bucket, key and event kind.
- The encoded input limit is enforced on declared ContentLength **and every streamed block**, even when a response understates its length. Notification ETags bind the download. Duration and projected decoded-storage limits reject before solving; malformed/nonfinite configuration cannot disable those limits.
- Runtime source bindings use SHA-256. Verified statuses are committed last; optimistic catalog writes relist on ETag conflict. Failed profiles cannot publish media or playable tracks. Network/SDK failures propagate for Lambda retry.
- Container base, static codecs, public library wheel and runtime requirements are pinned by checksums. Network protocols are absent from the minimal ffmpeg runtime; parsing still processes untrusted media inside the Lambda resource bounds.
- Catalog URLs reject embedded credentials, fragments, whitespace and backslashes while retaining HTTPS signed queries. Track schema, source identity, profile and verifier refusal remain enforced before autoplay.

These are reviewed source/configuration boundaries and local integration evidence. Live bucket policy, cloud workload limits, costs and teardown remain pending an authenticated profile/region. Reviewers should read the raw findings and release blockers before deployment.
