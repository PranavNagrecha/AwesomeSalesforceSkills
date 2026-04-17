# /build-lwc — Generate a Lightning Web Component bundle

Wraps [`agents/lwc-builder/AGENT.md`](../agents/lwc-builder/AGENT.md). Produces `.js`, `.html`, `.css`, `.js-meta.xml`, Jest tests, and — where applicable — the matching `@AuraEnabled(cacheable=true)` Apex controller stub.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Component name (camelCase)?

2. Purpose (3+ sentences — drives markup + reactivity decisions)?

3. Surface(s) it targets? (lightning__RecordPage | lightning__AppPage |
   lightning__HomePage | lightningCommunity__Page | lightning__FlowScreen | custom)

4. Data binding? (none | @wire getRecord | @wire imperative Apex | wire custom)

5. Exposed properties? (list of @api props with types)

6. Accessibility tier? (default: WCAG 2.1 AA)
```

If purpose is under 3 sentences or surface is unspecified, STOP.

---

## Step 2 — Load the agent

Read `agents/lwc-builder/AGENT.md` + mandatory reads (lwc/component-patterns, lwc/accessibility, lwc/testing, security/lightning-locker-and-lws, plus templates under `templates/lwc/`).

---

## Step 3 — Execute the plan

- Choose base skeleton from `templates/lwc/component-skeleton/`.
- Pick a pattern from `templates/lwc/patterns/` where one fits.
- Generate `.js` with reactive tracking, error handling, a11y hooks.
- Generate `.html` with semantic markup.
- Generate `.css` scoped to component.
- Generate `.js-meta.xml` with surface targets + config.
- Generate Jest tests (render, error, interaction, a11y).
- If data binding uses imperative Apex, emit the matching `@AuraEnabled(cacheable=true)` controller stub with SecurityUtils.

---

## Step 4 — Deliver the output

- Summary + confidence
- File bundle (fenced blocks, one per file)
- Jest tests
- Apex controller stub (if applicable) with test class
- Deployment manifest
- Process Observations
- Citations

---

## Step 5 — Recommend follow-ups

- `/audit-lwc` after deploy
- `/scan-security` on the controller Apex
- `/gen-tests` if coverage needs deepening

---

## What this command does NOT do

- Does not deploy.
- Does not modify existing LWCs — use `/audit-lwc` to identify gaps first.
- Does not run Jest against the live repo.
