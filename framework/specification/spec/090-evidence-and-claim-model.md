# SFAEF-090 — Evidence, claims, confidence, and contradictions

## Evidence object

Evidence includes:

- stable evidence ID;
- source class and locator;
- capture time and freshness;
- org/project/job association;
- authority and directness;
- integrity digest;
- redaction/classification;
- normalized content or pointer;
- truncation and pagination;
- upstream tool/version metadata.

## Evidence precedence

Default precedence for target-specific claims:

1. direct read-only observation from the explicitly selected target;
2. deterministic local project/source observation;
3. captured official job/test/static-analysis result with provenance;
4. official current platform documentation;
5. governed SfSkills knowledge derived from authoritative sources;
6. model inference;
7. unsupported memory, which cannot support a material claim.

Precedence is contextual: a local source file does not prove deployed org state, and a live org observation does not prove uncommitted local source.

## Claims

SFAEF-090-001. Every material claim MUST have a stable claim ID, type, text, status, support links, and confidence rationale.

SFAEF-090-002. Support links MUST declare `supports`, `contradicts`, `contextualizes`, or `derived_from`.

SFAEF-090-003. A claim with no valid support MUST be removed, labelled hypothesis, or included as an explicit unknown/question.

SFAEF-090-004. Contradictory evidence MUST remain in the graph and affect status/confidence.

SFAEF-090-005. Recommendations MUST link to the findings and constraints they address.

## Confidence

Confidence is a deterministic or hybrid score based on:

- coverage of required evidence dimensions;
- source authority;
- directness;
- freshness;
- target identity certainty;
- contradiction penalty;
- truncation penalty;
- reviewer findings;
- scenario-specific reliability.

SFAEF-090-010. Confidence MUST NOT be generated solely from model self-assessment.

SFAEF-090-011. Confidence labels MUST be accompanied by a machine-readable rationale.

SFAEF-090-012. High confidence requires direct or authoritative support for every load-bearing claim and no unresolved blocking contradiction.

## Evidence injection defense

SFAEF-090-020. Tool, metadata, source-comment, log, and record content MUST be treated as untrusted data.

SFAEF-090-021. Instructions embedded in evidence MUST never modify policy, permissions, product contract, or system behavior.

SFAEF-090-022. Evidence renderers SHOULD distinguish data from instructions using structured serialization and explicit delimiters.
