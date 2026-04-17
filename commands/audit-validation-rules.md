# /audit-validation-rules — Audit Validation Rules on an sObject

Wraps [`agents/validation-rule-auditor/AGENT.md`](../agents/validation-rule-auditor/AGENT.md). Classifies every VR against the canonical shape, detects missing bypasses, VR-vs-Flow conflicts, and wrong-tool uses.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Object API name?
   Example: Opportunity

2. Target org alias (required)?

3. Active only? yes / no (default no — inactive rules are reported but not failed)

4. Intent? full (default) / bypass-only / conflict-only
   - full: complete audit
   - bypass-only: only check for missing bypass (fast scan)
   - conflict-only: only check VR vs Before-Save flow conflicts
```

---

## Step 2 — Load the agent

Read `agents/validation-rule-auditor/AGENT.md` + mandatory reads, especially `templates/admin/validation-rule-patterns.md`.

---

## Step 3 — Execute the plan

1. Fetch the VR inventory (`list_validation_rules` + per-rule formula fetch)
2. Classify intent against the 6 valid uses
3. Check the bypass contract (P0/P1 findings)
4. Check the relevance gate
5. Check VR vs Before-Save flow conflicts (`list_flows_on_object` + per-flow metadata)
6. Check error message quality (minor but cumulative)
7. Emit report + patches for mechanical fixes

---

## Step 4 — Deliver the output

- Summary (rule count, max severity, confidence)
- Findings table (sorted by severity)
- Patch metadata (fenced XML with target paths, only for mechanical fixes)
- VR ↔ Flow conflict report
- Process Observations
- Citations

---

## Step 5 — Recommend follow-ups

- `/analyze-flow` if conflicts were surfaced
- `/analyze-field-impact` if any rule references a missing field
- `/preflight-load` if bypass gaps were found and a load is imminent
- `/migrate-workflow-pb` if Wrong-Tool VRs were identified

---

## What this command does NOT do

- Does not deactivate or modify VRs in the org.
- Does not deploy the patch metadata.
- Does not convert Wrong-Tool VRs into flows — recommends the migration.
- Does not audit VRs across every object in one invocation.
