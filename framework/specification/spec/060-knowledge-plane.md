# SFAEF-060 — Knowledge plane and skill governance

## Role of skills

Skills teach procedures, platform behavior, anti-patterns, and conventions. They do not prove what exists in a specific org or repository.

## Progressive loading

SFAEF-060-001. Discovery MUST begin from compact metadata or bounded domain routers.

SFAEF-060-002. Full `SKILL.md` content MUST be loaded only after selection.

SFAEF-060-003. References, scripts, and assets MUST be loaded only when the active stage requires them.

SFAEF-060-004. The default host package MUST NOT expose all 1,034 packages as always-on rules or unbounded top-level instructions.

## Selection record

Every selected knowledge item MUST record:

- canonical path and package version/digest;
- selection reason;
- product stage;
- required versus optional status;
- estimated tokens/bytes;
- source/freshness metadata where available;
- conflicts or supersession notes.

SFAEF-060-010. Selection MUST be deterministic for required core items.

SFAEF-060-011. Model-assisted ranking MAY be used for conditional items, but hard limits and allowlists MUST remain deterministic.

SFAEF-060-012. Duplicate or semantically overlapping items SHOULD be collapsed or ranked, not loaded without explanation.

## Evidence separation

SFAEF-060-020. A skill citation MAY support a recommendation or platform-behavior claim.

SFAEF-060-021. A skill citation MUST NOT support a claim that a target org, user, component, record, or job has a specific state.

## Currency

SFAEF-060-030. Release-sensitive knowledge MUST carry an official-source reference and last-reviewed date.

SFAEF-060-031. A source freshness policy MUST classify knowledge as current, review-due, stale, superseded, or historical.

SFAEF-060-032. Stale knowledge MAY be used only with an explicit warning unless a product policy prohibits it.

## Existing corpus migration

SFAEF-060-040. Existing packages remain canonical knowledge during migration.

SFAEF-060-041. Broad agent mandatory-read lists MUST be converted to core and conditional context packs before the agent is labelled V2-native.

SFAEF-060-042. Existing indexes and routers MAY remain compatibility surfaces, but missing-index state MUST be explicit and must not masquerade as zero results.
