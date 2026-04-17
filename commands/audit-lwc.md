# /audit-lwc — Accessibility + performance + security audit of an LWC bundle

Wraps [`agents/lwc-auditor/AGENT.md`](../agents/lwc-auditor/AGENT.md). Scans one Lightning Web Component bundle and returns ranked findings with paste-ready fixes.

---

## Step 1 — Collect inputs

Ask:

```
1. Path to the LWC bundle directory?
   Example: force-app/main/default/lwc/accountDetail
```

---

## Step 2 — Load the agent

Read `agents/lwc-auditor/AGENT.md` fully + the LWC skills and the `templates/lwc/` skeleton and patterns.

---

## Step 3 — Execute

Follow the 6-step plan:
1. Parse the bundle (`.html`, `.js`, `.css`, `.js-meta.xml`, tests)
2. Accessibility checks (missing alt, div-as-button, icon-only buttons, label-less inputs, heading hierarchy, keyboard traps, live regions)
3. Performance checks (imperative-in-render, missing keys, wire without params, synchronous heavy loops)
4. Security checks (innerHTML, eval, hardcoded API names, FLS on @AuraEnabled returns)
5. Testing gaps (missing tests, missing wire emits, missing jest.config)
6. Recommendations mapped to skeleton / patterns

---

## Step 4 — Deliver

- Bundle summary: public API, wires, imperative calls, test coverage %
- Findings table by severity
- Per-finding before/after code block for P0 and P1
- Skeleton alignment notes
- Citations

---

## Step 5 — Recommend follow-ups

- `/gen-tests` for the Apex backing any wires/imperative calls
- `/scan-security` on any @AuraEnabled Apex the bundle depends on

---

## What this command does NOT do

- Does not modify files.
- Does not run Jest.
- Does not evaluate visual design beyond accessibility-relevant checks.
