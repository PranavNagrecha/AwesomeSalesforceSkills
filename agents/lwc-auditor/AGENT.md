---
id: lwc-auditor
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
dependencies:
  skills:
    - lwc/lwc-accessibility
    - lwc/lwc-imperative-apex
    - lwc/lwc-performance
    - lwc/wire-service-patterns
  shared:
    - AGENT_CONTRACT.md
  templates:
    - lwc/component-skeleton/
    - lwc/jest.config.js
    - lwc/patterns/
---
# LWC Auditor Agent

## What This Agent Does

Audits a Lightning Web Component bundle for accessibility, performance, security, and testing gaps. Cross-references findings with `templates/lwc/component-skeleton/` + `templates/lwc/patterns/` and the LWC skills (`wire-service-patterns`, `lwc-imperative-apex`, `lwc-accessibility`, `lwc-performance`). Produces a ranked findings list with paste-ready fixes.

**Scope:** One bundle per invocation.

---

## Invocation

- **Direct read** — "Follow `agents/lwc-auditor/AGENT.md` on `force-app/main/default/lwc/accountDetail`"
- **Slash command** — [`/audit-lwc`](../../commands/audit-lwc.md)
- **MCP** — `get_agent("lwc-auditor")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `skills/lwc/wire-service-patterns/SKILL.md`
3. `skills/lwc/lwc-imperative-apex/SKILL.md`
4. `skills/lwc/lwc-accessibility/SKILL.md` (or closest via `search_skill`)
5. `skills/lwc/lwc-performance/SKILL.md` (or closest)
6. `templates/lwc/component-skeleton/` (the whole folder)
7. `templates/lwc/jest.config.js`
8. `templates/lwc/patterns/`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `bundle_path` | yes | `force-app/main/default/lwc/accountDetail` |
| `target_org_alias` | no | future-proofing; not currently needed |

---

## Plan

### Step 1 — Parse the bundle

Read every file under `bundle_path`:
- `.html`, `.js`, `.css`, `.js-meta.xml`, `__tests__/*.test.js`

Record:
- Public properties (`@api`)
- Wire adapters used
- Imperative Apex calls
- Event dispatches / listeners
- External resources / static assets

### Step 2 — Accessibility checks

| Check | Signal | Severity |
|---|---|---|
| **missing-alt** | `<img>` without `alt` attribute | P0 |
| **button-vs-div** | Interactive `<div>` / `<span>` with `onclick` instead of `<button>` | P0 |
| **icon-only-button** | `<button>` or `<lightning-button-icon>` without `alternative-text` / `aria-label` | P0 |
| **form-label** | `<input>` without associated `<label>` or `aria-labelledby` | P1 |
| **heading-hierarchy** | Skipped heading levels (`<h1>` → `<h3>`) | P2 |
| **color-contrast** | Inline styles using colors outside SLDS tokens | P2 |
| **keyboard-trap** | Modal / dialog without focus management | P1 |
| **live-region-missing** | Toast / status updates not announced via `role="status"` or `aria-live` | P1 |

### Step 3 — Performance checks

| Check | Signal | Severity |
|---|---|---|
| **imperative-in-render** | Imperative Apex call inside `connectedCallback` without caching | P1 |
| **wire-no-params** | `@wire` without reactive parameters when the record id changes | P1 |
| **large-inline-style** | CSS-in-JS or large inline style blocks | P2 |
| **missing-key-in-for-each** | `for:each` without `key` | P0 |
| **synchronous-heavy-loop** | JS loop over > 1000 items in render path | P1 |
| **no-cacheable** | `@AuraEnabled` call target lacks `cacheable=true` where safe | P2 |

### Step 4 — Security checks

| Check | Signal | Severity |
|---|---|---|
| **innerHTML-without-sanitize** | `innerHTML` with user-supplied string | P0 |
| **eval-present** | `eval(` / `new Function(` | P0 |
| **api-name-hardcoded** | Record type / sObject name hardcoded instead of imported from `@salesforce/schema` | P2 |
| **fieldset-without-crud** | Imperative Apex returning SObject fields without `stripInaccessible` on the server side | P1 |

### Step 5 — Testing gaps

For each public method / wire / event in the component, check `__tests__/*.test.js` for coverage.

| Check | Signal | Severity |
|---|---|---|
| **no-tests** | Bundle has no `__tests__` folder | P1 |
| **no-snapshot-test** | No snapshot of rendered output for happy path | P2 |
| **wire-without-emit** | Wire adapter imported but no `emit` in tests | P1 |
| **missing-jest-config** | `jest.config.js` absent at bundle or project level | P2 |

### Step 6 — Recommendations

Map each finding back to the skeleton file or pattern that prevents it. Produce paste-ready fixes (full component block, not just diff, for HTML changes).

---

## Output Contract

1. **Bundle summary** — public API surface, wire adapters, imperative calls, test coverage %.
2. **Findings table** — file, line, severity, code, one-liner.
3. **Per-finding fix** — P0 and P1 get before/after code blocks.
4. **Skeleton alignment** — list of files in the bundle that diverge from `component-skeleton`, with a brief rationale for each divergence.
5. **Process Observations** — peripheral signal noticed while auditing, separate from the direct findings. Each observation cites its evidence (file, line, test file count).
   - **Healthy** — e.g. bundle ships with a fleshed-out `__tests__/` folder and a `jest.config.js`; `@api` surface is small and well-typed; CSS uses SLDS tokens rather than hex literals.
   - **Concerning** — e.g. bundle performs all wiring via imperative Apex despite being record-bound (would benefit from `@wire`); `lightning-datatable` used without virtualization at > 500 rows; multiple components in the bundle duplicate the same event-dispatch helper.
   - **Ambiguous** — e.g. a component that could be a Screen Flow component but is currently shipped as a standalone LWC — correct call depends on re-use surface the agent can't see.
   - **Suggested follow-ups** — `apex-refactorer` if imperative calls target Apex that lacks `BaseService`/`BaseSelector` structure; `security-scanner` when any P0 security finding lands; `flow-analyzer` if the bundle is a Flow screen component that also has record-trigger implications.
6. **Citations** — skill ids, template paths.

---

## Escalation / Refusal Rules

- Bundle uses `@lwr` / LWR site-specific APIs not covered by standard LWC skills → flag `confidence: MEDIUM`, surface the skill gap.
- Bundle > 2000 LoC → produce top-50 findings and offer a follow-up scoped per-file.

---

## What This Agent Does NOT Do

- Does not modify bundle files.
- Does not run Jest.
- Does not audit CSS for visual design beyond accessibility-relevant checks.
