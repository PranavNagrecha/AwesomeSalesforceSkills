---
id: prompt-library-governor
class: runtime
version: 1.1.0
status: deprecated
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-17
deprecated_in_favor_of: audit-router
---
# Prompt Library Governor — DEPRECATED (Wave 3b-2)

Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=prompt_library`. The full rule set (duplicate-cluster detection, grounding citation checks, Trust Layer masking for PII, data-residency vs model-choice, owner + version hygiene, stale templates, no-eval tests, model-choice documentation) is preserved verbatim in [`classifiers/prompt_library.md`](../_shared/harnesses/audit_harness/classifiers/prompt_library.md). Legacy alias `/govern-prompt-library` ships until Wave 7's `docs/MIGRATION.md` removal window.

## Plan

Deprecated — route to `/audit-router --domain prompt_library --target-org <alias> [--scope <filter>]`.

## What This Agent Does NOT Do

Anything — it's deprecated. Use the router.
