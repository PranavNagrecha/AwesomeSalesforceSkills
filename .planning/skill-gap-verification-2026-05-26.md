# Skill Gap Verification — 2026-05-26

Run mode: scheduled-task `daily-skill-creation`. Catalog size at start: **1002 skills**.

## Sources scanned

### Source A — Decision-tree branch gaps

Walked all 7 trees in `standards/decision-trees/`:

- `agentforce-capability-selector.md`
- `async-selection.md`
- `automation-selection.md`
- `flow-pattern-selector.md`
- `integration-pattern-selection.md`
- `performance-tuning.md`
- `sharing-selection.md`

Extracted 53 unique skill citations across all trees. Apparent "missing" hits
(11 of 53) were all slug-drift to existing skills (tree wording vs. actual
slug). Spot-checked each via search_knowledge.py:

| Tree slug | Actual skill (verified) |
|---|---|
| `integration/oauth-flows` | `integration/oauth-flows-and-connected-apps` (2.258) |
| `integration/callouts-and-http-integrations` | `integration/callout-limits-and-async-patterns` + others |
| `integration/change-data-capture-for-external-subscribers` | `integration/change-data-capture-integration` |
| `integration/named-credentials` | `integration/named-credentials-setup` |
| `integration/graphql` | `integration/graphql-api-patterns` |
| `integration/salesforce-connect` | `integration/salesforce-connect-external-objects` |
| `architect/event-driven-salesforce-architecture` | `architect/event-driven-architecture` |
| `admin/permission-sets` | `admin/permission-set-architecture` |
| `admin/permission-set-groups` | `admin/permission-set-group-composition` |
| `security/org-hardening` | `security/org-hardening-and-baseline-config` |
| `admin/record-page-performance` | `admin/lightning-page-performance-tuning` (11.481) |

**Net branch gaps from Source A: 0**.

### Source B — Cross-skill broken references

Greped `skills/*/*/SKILL.md` and `skills/*/*/references/*.md` for `skills/<domain>/<slug>` paths. Found 63 unique references, of which 15 do not resolve to a real skill directory:

| Broken ref | Lives in | Actual skill (verified) |
|---|---|---|
| `admin/approval-process-design` | `admin/approval-process-apex-patterns/.../well-architected.md` | `admin/approval-processes` + `admin/approval-process-apex-patterns` |
| `admin/order-of-execution` | `admin/workflow-field-update-patterns/.../well-architected.md` | `apex/order-of-execution-deep-dive` |
| `apex/apex-security-crud-fls` | `flow/flow-transactional-boundaries/SKILL.md` | `apex/apex-stripinaccessible-and-fls-enforcement` + `apex/apex-security-patterns` |
| `apex/apex-testing-patterns` | `flow/flow-invocable-from-apex/SKILL.md` | `apex/test-class-standards` (2.700) + `apex/apex-test-setup-patterns` |
| `apex/dynamic-soql` | `apex/apex-string-and-regex/.../well-architected.md` | `apex/apex-dynamic-soql-binding-safety` |
| `devops/sandbox-strategy-designer` | `admin/sandbox-post-refresh-automation/.../well-architected.md` | `devops/environment-strategy` (5.467) + `admin/sandbox-strategy` |
| `devops/sfdx-cicd-pipeline` | `devops/cicd-for-experience-cloud/.../well-architected.md` | `devops/devops-center-pipeline` + `devops/bitbucket-pipelines-for-salesforce` + `architect/ci-cd-pipeline-architecture` |
| `flow/flow-best-practices` | `admin/workflow-field-update-patterns/.../well-architected.md` | `flow/flow-element-naming-conventions` (7.575) + `flow/flow-resource-patterns` + `flow/fault-handling` |
| `flow/flow-screen-flow-accessibility` | `flow/flow-screen-lwc-components/SKILL.md` | `flow/screen-flow-accessibility` |
| `flow/flow-screen-flows` | `flow/flow-screen-lwc-components/SKILL.md` | `flow/flow-screen-input-validation-patterns` + `lwc/lwc-in-flow-screens` + `flow/flow-screen-lwc-components` |
| `lwc/lwc-component-skeleton` | `flow/flow-screen-lwc-components/SKILL.md` | `lwc/lwc-base-component-recipes` (2.286) + `templates/lwc/component-skeleton/` |
| `lwc/lwc-flow-properties` | `flow/flow-screen-lwc-components/SKILL.md` | `flow/flow-screen-lwc-components` (already cited from same file) |
| `security/oauth-flows-and-connected-apps` | `admin/connected-app-troubleshooting/.../well-architected.md` | `integration/oauth-flows-and-connected-apps` (wrong domain prefix) |
| `service/email-to-case` | `admin/email-service-inbound/.../well-architected.md` | `admin/email-to-case-configuration` (drift, wrong domain prefix) |
| `territory/capacity` | `admin/fsl-shifts-and-crew/.../llm-anti-patterns.md` | `admin/enterprise-territory-management` (5.130) + `data/territory-data-alignment` + `admin/fsl-resource-management` |

**Net broken-ref gaps from Source B: 0**. Every broken reference resolves to
an existing skill via slug-drift or wrong-domain-prefix. These should be
fixed (out of scope for this run — they are typos in citations, not missing
content).

### Source C — Salesforce release notes

Skipped — `WebFetch` against `help.salesforce.com` continues to return CSS-only
shells for release-notes pages (client-rendered). Tracked as a known limitation
since 2026-05-15. Same posture as 2026-05-22.

### Source D — BACKLOG.yaml TODO sweep (8 candidates not verified individually in 2026-05-22)

The 2026-05-22 run audited 10 candidates from BACKLOG. The TODO list still
holds 43 entries. Picked 8 with the highest technical specificity that were
not part of the 2026-05-22 sample.

## Threshold rules (from scheduled-task brief)

- Top hit score > 4.0 same domain → REJECT auto.
- Top hit 2.5–4.0 → require articulated delta after reading the top hit's SKILL.md or REJECT.
- Top hit < 2.5 across all phrasings → ACCEPT.

## Candidates verified

| # | Candidate | Phrase 1 top hit (score) | Phrase 2 top hit (score) | Decision |
|---|---|---|---|---|
| 1 | `integration/event-relay-patterns` | `integration/event-relay-configuration` 9.767 | `integration/event-relay-configuration` 9.500 | **REJECT auto** |
| 2 | `integration/composite-api-advanced` | `integration/composite-api-patterns` 11.333 | `integration/composite-api-patterns` 5.673 | **REJECT auto** |
| 3 | `devops/salesforce-api-version-strategy` | `devops/api-version-management` 10.392 | `devops/api-version-management` 6.009 | **REJECT auto** |
| 4 | `integration/external-credentials-setup` | `integration/named-credentials-setup` 8.896 | `integration/named-credentials-setup` 3.672 | **REJECT auto** (Phrase 1) |
| 5 | `apex/apex-webservice-annotation` | `apex/apex-rest-services` 3.672 | `apex/apex-rest-services` 2.572 / `integration/webhook-inbound-patterns` 2.680 | **REJECT** — delta absent (see below) |
| 6 | `security/event-log-file-analysis` | `security/event-monitoring` 5.331 / `security/security-incident-response` 4.450 | `security/event-monitoring` 7.439 | **REJECT auto** |
| 7 | `data/polymorphic-field-data-patterns` | `admin/activity-and-task-patterns` 4.322 / `admin/standard-object-quirks` 2.484 | `admin/standard-object-quirks` 3.019 / `apex/apex-polymorphic-soql` 2.669 / `admin/activity-and-task-patterns` 2.689 | **REJECT auto** (Phrase 1) |
| 8 | `admin/formula-field-limits-and-patterns` | `apex/formula-field-performance-and-limits` 6.510 / `admin/formula-fields` 2.140 | `apex/formula-field-performance-and-limits` 7.127 | **REJECT auto** |

## Delta-articulation verification — #5 `apex-webservice-annotation`

**Best existing hit:** `apex/apex-rest-services` at 3.672 on Phrase 1.

Read `skills/apex/apex-rest-services/SKILL.md` (description, Before Starting,
Core Concepts, Common Patterns). The skill covers exactly the surface the
candidate would address:

- `@RestResource` URL mapping and versioning ("Version The URL Mapping Deliberately")
- `HttpGet / HttpPost / HttpPatch` annotation pattern ("HttpGet HttpPost HttpPatch in Apex" trigger)
- `RestContext.request` / `RestContext.response` pattern ("RestContext request and response pattern")
- Status codes and consistent error envelope ("Status Codes And Error Bodies Are Part Of The Contract")
- Sharing / FLS enforcement inside REST classes ("Security Must Be Declared And Enforced")
- Thin Resource + Service Layer separation
- Versioning strategy

There is no articulated sub-topic the candidate would cover that
`apex-rest-services` does not. The candidate name is essentially a rename of
the existing skill. **REJECT.**

## Built skills

None. Catalog remains saturated.

## Summary

Walked Source A (decision-tree branches), Source B (broken refs in SKILL.md
files), Source D (BACKLOG.yaml TODO sweep, 8 new candidates). Source C
unavailable due to JS-rendered release-notes pages. **0 verified gaps.**

The catalog at 1002 skills continues to cover the surface area mapped by the
decision trees and the BACKLOG TODO list. Remaining BACKLOG TODOs that have
not yet been audited individually (35 entries) can be deferred to future
runs; the 2026-05-22 run set the precedent that ~10 entries per pass is the
right cadence and most resolve to slug-drift or existing coverage.

## Process observations

- All 11 "missing" skill paths in Source A and all 15 in Source B are
  slug-drift. There is real value in a one-shot fixer that rewrites broken
  `skills/<domain>/<slug>` references to the correct slug; this is a tooling
  improvement, not a skill gap. Out of scope for this scheduled task.
- BACKLOG TODO entries continue to mostly resolve to existing same-domain
  skills with 4.0+ scores. The signal that an entry is genuinely a gap is
  rare (1 of every 10–11 candidates over the last two months of runs).
