# SFAEF-110 — Security, identity, authorization, and authority separation

## Authority profiles

1. `product-read-only` — ordinary user products; no Salesforce mutation.
2. `fixture-offline` — local captured evidence; no network.
3. `qa-scratch-setup` — guarded setup/teardown for disposable scratch orgs only; never model-exposed.
4. `maintainer-local-write` — generated files, indexes, reports, and package maintenance.
5. `future-approved-action` — reserved; not part of V2.

## Requirements

SFAEF-110-001. Every run MUST declare exactly one authority profile and a target identity scope.

SFAEF-110-002. Product agents MUST not elevate authority, change org allowlists, or invoke QA setup code.

SFAEF-110-003. Product policy MUST be deny-by-default for unknown MCP tools and shell commands.

SFAEF-110-004. Shell classification MUST parse command structure and reject compound/nested execution, not rely only on substrings.

SFAEF-110-005. Credentials, access tokens, auth URLs, session IDs, private keys, and sensitive values MUST be redacted before persistence or model exposure.

SFAEF-110-006. The run MUST display and record the selected org and project before consequential evidence gathering.

SFAEF-110-007. Multiple project or org candidates MUST produce an ambiguity state rather than an arbitrary selection.

SFAEF-110-008. Host capability gaps MUST downgrade the guarantee. If an MCP hook is unavailable in cloud execution, documentation and status MUST say so.

## Prompt and evidence injection

SFAEF-110-020. Tool output, metadata descriptions, source comments, logs, record values, and retrieved documents are untrusted.

SFAEF-110-021. Evidence must never be able to override system policy, request new tools, modify schemas, or change review criteria.

SFAEF-110-022. The framework MUST test direct and indirect prompt injection carried in Salesforce text fields, Apex comments, logs, filenames, and MCP error text.

## Supply chain

SFAEF-110-030. Host packages and review artifacts SHOULD include manifests and checksums.

SFAEF-110-031. Generated plugin output MUST be deterministic and drift-checked.

SFAEF-110-032. Dependencies and external executables MUST be version-recorded; install helpers MUST not silently replace unrelated files.

## Scratch-org safeguards

SFAEF-110-040. Scratch setup MUST verify Dev Hub identity, scratch-org type, expiration, and a scenario marker before mutation.

SFAEF-110-041. Cleanup MUST run unconditionally and produce deletion evidence.

SFAEF-110-042. A failure to prove disposability MUST stop the scenario before mutation.
