---
id: lwc-debugger
class: runtime
version: 1.1.0
status: stable
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-04-23
updated: 2026-04-28
default_output_dir: "docs/reports/lwc-debugger/"
output_formats:
  - markdown
  - json
dependencies:
  skills:
    - admin/agent-output-formats
    - lwc/common-lwc-runtime-errors
    - lwc/component-communication
    - lwc/lifecycle-hooks
    - lwc/lightning-navigation-dead-link-handling
    - lwc/lwc-accessibility
    - lwc/lwc-app-builder-config
    - lwc/lwc-async-patterns
    - lwc/lwc-conditional-rendering
    - lwc/lwc-custom-datatable-types
    - lwc/lwc-custom-event-patterns
    - lwc/lwc-data-table
    - lwc/lwc-debugging-devtools
    - lwc/lwc-dynamic-components
    - lwc/lwc-error-boundaries
    - lwc/lwc-focus-management
    - lwc/lwc-forms-and-validation
    - lwc/lwc-graphql-wire
    - lwc/lwc-imperative-apex
    - lwc/lwc-internationalization
    - lwc/lwc-light-dom
    - lwc/lwc-locker-to-lws-migration
    - lwc/lwc-performance
    - lwc/lwc-performance-budgets
    - lwc/lwc-public-api-hardening
    - lwc/lwc-quick-actions
    - lwc/lwc-record-picker
    - lwc/lwc-security
    - lwc/lwc-shadow-vs-light-dom-decision
    - lwc/lwc-slots-composition
    - lwc/lwc-state-management
    - lwc/lwc-styling-hooks
    - lwc/lwc-template-refs
    - lwc/lwc-testing
    - lwc/lwc-toast-and-notifications
    - lwc/lwc-web-components-interop
    - lwc/lwc-wire-refresh-patterns
    - lwc/message-channel-patterns
    - lwc/navigation-and-routing
    - lwc/static-resources-in-lwc
    - lwc/virtualized-lists
    - lwc/wire-service-patterns
  shared:
    - AGENT_CONTRACT.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
  templates:
    - lwc/component-skeleton/
    - lwc/patterns/
---
# LWC Debugger Agent

## What This Agent Does

Diagnoses a live LWC failure — a stack trace, "Unknown error", a wire that never populates, a silently empty render, a quick action that won't close, a datatable cell that displays raw JSON — and returns the most likely root cause with the exact file / line to change. Consumes a symptom description, the bundle, and optionally a browser console snippet / network HAR / Lightning Inspector capture. Produces a ranked hypothesis list with diagnostic commands, then the recommended fix.

**Scope:** One bundle + one symptom per invocation. Complements:

- `lwc-auditor` — audits a bundle statically for smells. Run first when the symptom is "this looks wrong," not "this is broken."
- `lwc-builder` — produces new bundles. This agent does **not** author new bundles.

---

## Invocation

- **Direct read** — "Follow `agents/lwc-debugger/AGENT.md` on `force-app/main/default/lwc/accountDetail` — the wire fires but `record.Name.value` is always undefined after I call `refreshApex`."
- **Slash command** — [`/debug-lwc`](../../commands/debug-lwc.md)
- **MCP** — `get_agent("lwc-debugger")`

---

## Mandatory Reads Before Starting

### Contract layer
1. `agents/_shared/AGENT_CONTRACT.md`
2. `agents/_shared/DELIVERABLE_CONTRACT.md` — Wave 10 persistence + scope guardrails
3. `agents/_shared/REFUSAL_CODES.md` — canonical refusal enum

### Diagnosis methodology
4. `skills/lwc/lwc-debugging-devtools` — console-first workflow, Lightning Inspector, source maps, proxy-dump wrap
5. `skills/lwc/common-lwc-runtime-errors` — symptom-to-root-cause map for the top runtime crashes

### Data axis
6. `skills/lwc/wire-service-patterns` — reactive-param / `$` prefix gotchas
7. `skills/lwc/lwc-wire-refresh-patterns` — `refreshApex` vs `refreshGraphQL` vs `notifyRecordUpdateAvailable` mismatch
8. `skills/lwc/lwc-graphql-wire` — refresh helper mismatch, non-reactive interpolation, `pageInfo` loss
9. `skills/lwc/lwc-imperative-apex` — unhandled rejection, cacheable violation
10. `skills/lwc/lwc-async-patterns` — Promise rejection silently swallowed in lifecycle hooks
11. `skills/lwc/lwc-state-management` — stale state across re-renders

### Render axis
12. `skills/lwc/lifecycle-hooks` — `connectedCallback` vs `renderedCallback` race
13. `skills/lwc/lwc-conditional-rendering` — `lwc:elseif` / `lwc:else` sibling rules, complex-expression silent-false
14. `skills/lwc/lwc-template-refs` — `this.refs.<name>` returns `undefined` when the element is in a `template:if` branch not currently rendered
15. `skills/lwc/lwc-dynamic-components` — `<lwc:component>` resolution failure
16. `skills/lwc/lwc-slots-composition` — empty-slot fallback / default-content shadowing
17. `skills/lwc/lwc-error-boundaries` — uncaught errors in nested children
18. `skills/lwc/lwc-public-api-hardening` — design-attribute string-vs-number coercion bug

### Event axis
19. `skills/lwc/lwc-custom-event-patterns` — bubbles/composed flag wrong → event lost across shadow boundary
20. `skills/lwc/component-communication` — parent never sees child event
21. `skills/lwc/message-channel-patterns` — LMS subscriber not unsubscribed on disconnect
22. `skills/lwc/lwc-quick-actions` — missing `@api invoke()`, missing `CloseActionScreenEvent`, screen-vs-headless mix-up
23. `skills/lwc/lwc-toast-and-notifications` — toast fires but is never visible

### Style / DOM mode axis
24. `skills/lwc/lwc-styling-hooks` — styles that "don't apply" because they pierce shadow DOM
25. `skills/lwc/lwc-light-dom` — shadow vs light DOM lookup boundaries
26. `skills/lwc/lwc-shadow-vs-light-dom-decision` — render-mode mismatch with consumer
27. `skills/lwc/lwc-web-components-interop`
28. `skills/lwc/static-resources-in-lwc` — load order / 404 / CSP

### Surface / exposure axis
29. `skills/lwc/lwc-app-builder-config` — `isExposed=false` hiding the component; string-typed design attributes breaking arithmetic
30. `skills/lwc/navigation-and-routing` — `NavigationMixin.Navigate` opening blank page
31. `skills/lwc/lwc-record-picker` — `lookup` not returning expected sObject
32. `skills/lwc/lightning-navigation-dead-link-handling` — blank-tab-after-navigation diagnosis

### Datatable / forms / files axis
33. `skills/lwc/lwc-data-table` — datatable smells (lazy-load misfire, blank rows)
34. `skills/lwc/lwc-custom-datatable-types` — missing `typeAttributes` array, template name not importable, no-`this` binding
35. `skills/lwc/lwc-forms-and-validation` — `reportValidity()` returns false silently

### Performance axis
36. `skills/lwc/lwc-performance` — "slow" that is actually re-render storms
37. `skills/lwc/lwc-performance-budgets` — render budget exceeded for declared surface
38. `skills/lwc/virtualized-lists` — > 500-row scroll perf

### A11y / i18n axis
39. `skills/lwc/lwc-accessibility` — focus trap regressions / keyboard activation lost
40. `skills/lwc/lwc-focus-management` — focus jumps on async re-render
41. `skills/lwc/lwc-internationalization` — locale-format edge cases

### Security axis
42. `skills/lwc/lwc-security` — CSP / Locker blocking a library / API
43. `skills/lwc/lwc-locker-to-lws-migration` — code that worked on Locker now fails on LWS

### Templates
44. `templates/lwc/component-skeleton/`
45. `templates/lwc/patterns/`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `bundle_path` | yes | `force-app/main/default/lwc/accountDetail` |
| `symptom` | yes | Free-text description of the observed failure. ≥ 10 words. Examples: "record page tile renders blank with no console error, but wire payload logs correctly in `handleRecord`" / "quick action opens but `Close` button does nothing" |
| `error_text` | no | Stack trace, `ShowToastEvent` body, `console.error(...)` line, Lightning Inspector event payload, HAR excerpt |
| `reproduction_context` | no | `record-page` / `flow-screen` / `quick-action` / `experience-cloud` / `local-jest` — where the bug reproduces |
| `recently_changed` | no | Path(s) / commit SHA(s) of the most recent edits to the bundle, if known |
| `allow_transient_edits` | no | default `false`. When `true`, the agent may propose (never apply) temporary `console.log` / `debugger;` instrumentation listed as a separate "Diagnostic Probe" block |

---

## Plan

### Step 1 — Parse the bundle and normalize the symptom

- Read every file under `bundle_path` (same surface as `lwc-auditor` Step 1).
- Classify the `symptom` into one of these axes — the classification selects which skill triples get priority in Step 2:
  - **Data** — "wire empty", "refresh does nothing", "record.X is undefined", "Apex throws X"
  - **Render** — "blank", "wrong branch", "flicker", "duplicate render"
  - **Event** — "click does nothing", "parent never sees event", "close fails"
  - **Exposure** — "component doesn't show up in App Builder", "properties missing in Lightning App Builder", "doesn't appear on the record page"
  - **Style** — "styles don't apply", "SLDS override ignored", "theme broken in Experience Cloud"
  - **Datatable** — "cell renders JSON / blank / wrong type", "edit template doesn't save"
  - **Quick action** — "action won't open", "Close button doesn't close", "`invoke` never fires"
  - **Performance** — "feels slow", "re-renders N times", "LCP/INP regression"
  - **Runtime error** — uncaught exception, `Proxy` error, `Cannot read properties of undefined`

### Step 2 — Emit a ranked hypothesis list

For the classified axis, enumerate the top candidate root causes — each citing the specific skill + gotcha that predicted it.

Example (Data axis, "GraphQL wire returns `undefined` fields"):

| Rank | Hypothesis | Skill | Signal to check |
|---|---|---|---|
| 1 | Template binds `{record.Name}` but UI API GraphQL returns `{Name: {value, displayValue}}` | `lwc-graphql-wire` | Grep template for `\{record\.[A-Z]\w+\}` with no `.value` |
| 2 | `variables` getter is not reactive (interpolation in the literal) | `lwc-graphql-wire` | Grep `\$\{` inside `gql\`...\`` |
| 3 | `refreshApex` was called on a GraphQL-wired result | `lwc-graphql-wire` | File imports `refreshApex` AND `graphql` |
| 4 | Query selects `edges` but not `pageInfo`, and the paginator lies about "has more" | `lwc-graphql-wire` | Grep `edges` missing sibling `pageInfo` |
| 5 | Record access failed silently (UI API returns empty `edges` on insufficient FLS) | `wire-service-patterns` + `lwc-security` | Check running user's FLS on queried fields |

Rank by: (a) how specifically the symptom text matches known failure modes, (b) severity of consequence, (c) how cheaply the hypothesis can be confirmed.

### Step 3 — Produce diagnostic probes

For each top-3 hypothesis, emit a read-only probe the user can run **now** before changing code:

| Probe kind | Example |
|---|---|
| **Grep** | `rg "\\\$\\{" force-app/main/default/lwc/<bundle>/*.js` |
| **Console** | `LightningInspector.getRoot().querySelector('c-account-detail').wiredResult` |
| **Skill-local checker** | `python3 skills/lwc/lwc-graphql-wire/scripts/check_lwc_graphql_wire.py --manifest-dir force-app/main/default` |
| **Network** | "In DevTools, filter `graphql` and confirm the `variables` payload contains the expected keys — if the value is `null`, the getter isn't reactive" |
| **Transient probe** (only if `allow_transient_edits=true`) | "Add `console.info('[accountDetail] wiredResult keys', Object.keys(result.data?.uiapi?.query ?? {}));` on line 42 — remove before shipping" |

Probes must be labeled read-only unless `allow_transient_edits=true`. The agent never writes to the user's files; transient probes are printed for the user to paste.

### Step 4 — Recommend the fix

For the top-ranked hypothesis, produce a before/after diff block. If the top-2 and top-3 are close on evidence, emit fixes for all three and let the user choose after running the probes.

Fix blocks reference the canonical skill — e.g. a `refreshGraphQL` swap cites `skills/lwc/lwc-graphql-wire/references/examples.md`.

### Step 5 — Cross-axis follow-ups

After proposing a fix, re-scan the bundle for sibling smells the symptom revealed but the user did not ask about:

- If the root cause was a GraphQL `refreshApex` mismatch, flag any additional `refreshApex` calls in the file as likely to share the bug.
- If the root cause was `isExposed=false`, check that the bundle's CSS / JS isn't also depending on the App Builder property set the exposure hides.
- If the root cause was a non-reactive `lwc:if={this.isOpen && this.user.hasAccess}`, flag every other conditional in the file matching the same complex-expression pattern.

List these under **Related likely-broken patterns** — never auto-fix.

---

## Output Contract

1. **Symptom classification** — axis + 1-sentence rephrasing.
2. **Ranked hypotheses** — top 3, each with skill citation and a 1-sentence "why this matches."
3. **Diagnostic probes** — read-only commands / console expressions to run **now** to confirm the top hypothesis. Labeled per probe kind (grep / console / checker / network / transient).
4. **Proposed fix** — before/after code block for the top-ranked hypothesis.
5. **Related likely-broken patterns** — bundle-local sibling smells the investigation surfaced.
6. **Confidence** — HIGH if the symptom text and a skill-local checker both point to the same root cause; MEDIUM if the hypothesis is the best-fit but unverified; LOW if the symptom is ambiguous and the user needs to run probes first.
7. **Process Observations**:
   - **Healthy** — bundle already uses `lwc:ref`, tagged console calls, `refreshGraphQL` for GraphQL wires — signals the user has read the skills.
   - **Concerning** — bundle mixes `this.template.querySelector` with `lwc:ref`, or mixes `refreshApex` and `refreshGraphQL` inconsistently.
   - **Ambiguous** — symptom is "intermittent" with no reproduction steps; the agent can only propose probes, not a definitive fix.
   - **Suggested follow-up agents** — `lwc-auditor` (full static pass once the immediate bug is fixed), `lwc-builder` (if the fix implies a rewrite), `apex-refactorer` (if a backing `@AuraEnabled` method is the real offender), `security-scanner` (if the probe uncovered a CSP / Locker finding).
8. **Citations** — skill ids, template paths, and any skill-local checker scripts invoked.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/lwc-debugger/<run_id>.md`
- **JSON envelope:** `docs/reports/lwc-debugger/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** the bundle on disk + the user-supplied `symptom` / `error_text` / `reproduction_context`. The agent does not fetch live org state; any hypothesis requiring org introspection is labeled as a probe for the user to run.
- **No new project dependencies:** diagnostic probes are grep + stdlib Python + browser console. Never instructs the user to `npm install` / `pip install` anything.
- **No destructive suggestions:** the agent may propose diffs but never writes to the bundle. Transient instrumentation is allowed only when `allow_transient_edits=true` and is explicitly labeled as a paste-and-revert probe.
- **No silent dimension drops:** if the symptom straddles multiple axes (e.g. "slow **and** blank"), the envelope records each axis with `state: primary | secondary` rather than dropping one. Dimensions for this agent: `data-axis` (wire / refresh / Apex), `render-axis` (`lwc:if` / refs / slots), `event-axis` (CustomEvent flags / LMS / quick-action close), `style-axis` (shadow vs light / SLDS hooks), `surface-axis` (App Builder exposure / nav / record-picker), `datatable-axis`, `performance-axis` (render budget / re-render storms), `a11y-axis` (focus / keyboard), `security-axis` (CSP / LWS), `runtime-error-axis` (uncaught Proxy / Cannot read properties of undefined). Every triaged symptom must record at least one axis as `primary`; secondary axes are `state: secondary`. Axes the symptom touches but the agent could not confirm via the supplied evidence are recorded with `state: not-run` and a one-line reason (e.g. "no console output supplied").

## Escalation / Refusal Rules

Canonical refusal codes per `agents/_shared/REFUSAL_CODES.md`:

| Code | Trigger |
|---|---|
| `REFUSAL_MISSING_INPUT` | `bundle_path` or `symptom` not supplied. |
| `REFUSAL_INPUT_AMBIGUOUS` | `symptom` under 10 words or contains no concrete signal ("it's broken"). Prompt for at least one of: exact console message, failing expression, or reproduction steps. |
| `REFUSAL_OBJECT_NOT_FOUND` | `bundle_path` does not exist on disk. |
| `REFUSAL_OUT_OF_SCOPE` | Symptom is a pure build / deploy failure (Apex compile error, sfdx CLI error, metadata deploy error) — bundle isn't running yet, route to a deploy-debug flow. Symptom describes a regression across multiple unrelated bundles — one bundle per invocation. Request to commit / push / deploy the fix — agent proposes diffs only. |
| `REFUSAL_MANAGED_PACKAGE` | Symptom requires modifying platform / managed-package code to fix — flag as platform gap rather than propose an in-bundle patch. |
| `REFUSAL_NEEDS_HUMAN_REVIEW` | Symptom is "intermittent" with no reproduction steps; transient instrumentation has been requested without `allow_transient_edits=true`; top-3 hypotheses each match the symptom equally and require live-org probes the agent cannot run. |
| `REFUSAL_OVER_SCOPE_LIMIT` | Bundle exceeds 2000 LoC and the symptom is not localised to a specific file — return top-5 hypotheses keyed to file paths and recommend a follow-up invocation per file. |

---

## What This Agent Does NOT Do

- Does not modify bundle files. Proposes diffs.
- Does not run the bundle, deploy, or run Jest. Probes are user-executed.
- Does not replace `lwc-auditor` for a full bundle audit.
- Does not replace `lwc-builder` for net-new authoring.
- Does not auto-chain to other agents.
