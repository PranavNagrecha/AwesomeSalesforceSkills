# SFAEF-180 — Data privacy, classification, and retention

## Data classes

- `public-knowledge`
- `repository-internal`
- `org-metadata`
- `org-business-data`
- `security-sensitive`
- `credential-secret`
- `benchmark-sanitized`

## Requirements

SFAEF-180-001. Every evidence item MUST carry a data classification.

SFAEF-180-002. Credential-secret data MUST never be persisted or sent to the model.

SFAEF-180-003. Org-business-data SHOULD be minimized and replaced with schema/count/hashed examples when content is not necessary.

SFAEF-180-004. Default run retention MUST be local and bounded; users must be able to delete a run bundle completely.

SFAEF-180-005. Remote telemetry or hosted review MUST be opt-in and disclose fields, purpose, processor, and retention.

SFAEF-180-006. Cross-org evidence reuse is prohibited unless evidence is explicitly sanitized and reclassified.

SFAEF-180-007. Benchmark artifacts MUST be scanned for secrets, customer identifiers, and proprietary data before contribution.

SFAEF-180-008. Redaction MUST preserve enough structure to debug behavior and prove that the secret was removed.

## Privacy by mode

- Knowledge-only and fixture modes can operate offline.
- Local-project mode reads only the selected path and respects ignore/exclusion policy.
- Live mode uses explicit org allowlists and minimal queries.
- Scratch-QA artifacts are sanitized before leaving protected CI.
