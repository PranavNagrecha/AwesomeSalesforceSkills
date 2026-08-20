# SFAEF-190 — Versioning, release, and conformance

## Versions

- Specification version.
- Core runtime/kernel version.
- Product version.
- Agent/command/tool schema version.
- Host adapter version.
- Knowledge corpus snapshot/version.
- Scenario/benchmark version.

SFAEF-190-001. Every run MUST record all available versions.

SFAEF-190-002. Breaking schema or semantic changes require a major version or explicit migration layer.

SFAEF-190-003. Generated adapters MUST declare the canonical definitions they were built from.

## Release stages

- `experimental` — architecture may change; fixture use only.
- `alpha` — end-to-end local product path; no behavior claim.
- `beta` — actual host smoke, deterministic QA, selected live-read-only verification.
- `release-candidate` — required scratch-org scenarios and security gates pass.
- `stable` — published support/compatibility policy and no open P0 defect.
- `deprecated` — replacement and sunset path exist.

## Conformance gates

SFAEF-190-010. A V2 release candidate MUST include a valid requirement traceability matrix.

SFAEF-190-011. All P0 tests and applicable product thresholds MUST pass.

SFAEF-190-012. Any unrun live/host test MUST be explicit and blocks the corresponding qualification label.

SFAEF-190-013. The release bundle MUST be reproducible, checksum-protected, secret-scanned, and built from a clean commit.

SFAEF-190-014. Documentation MUST state actual host, Salesforce, model, and QA dates.

SFAEF-190-015. Public claims MUST not exceed the weakest proven conformance profile.

## Compatibility

SFAEF-190-020. Existing SfSkills users must retain a documented legacy path during V2 adoption.

SFAEF-190-021. Deprecation requires telemetry or evidence of low use where available, a replacement, migration instructions, and at least one compatibility release unless safety requires immediate removal.
