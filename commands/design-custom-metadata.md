# /design-custom-metadata — Design or audit Custom Metadata Types + Custom Settings

Wraps [`agents/custom-metadata-and-settings-designer/AGENT.md`](../agents/custom-metadata-and-settings-designer/AGENT.md). Picks the right artifact (CMT vs List Custom Setting vs Hierarchy Custom Setting) and emits field design + usage guidance + deploy/load boundary.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Mode? design | audit

2. Target org alias (required for audit; optional for design)?

3. Scenario (for design)?
   Options: feature-flag | env-config | rule-table | api-registry | tax-or-rate-table |
            rounding-rules | text-catalog | other (describe)

4. Consumers? (apex | flow | formula | validation-rule | lwc)

5. Protection needs? (protected-from-subscribers | org-internal | public)

6. Expected record count? (< 50 | 50-500 | 500+)
```

---

## Step 2 — Load the agent

Read `agents/custom-metadata-and-settings-designer/AGENT.md` + mandatory reads (admin/custom-metadata-types, admin/custom-settings, standards/decision-trees/configuration-storage-selection.md).

---

## Step 3 — Execute the plan

- Classify scenario against decision tree.
- Pick CMT vs List vs Hierarchy Custom Setting (cite the branch).
- Design fields + labels + API names per `templates/admin/naming-conventions.md`.
- Produce usage snippets for each consumer (Apex CMT query, Flow Get Records, formula references).
- Emit deploy-vs-data-load boundary (CMT = metadata, Custom Setting = data).

---

## Step 4 — Deliver the output

- Summary + confidence
- Decision (with decision-tree branch cited)
- Field design
- Usage snippets per consumer
- Deploy/load boundary
- Audit findings (audit mode)
- Process Observations
- Citations

---

## Step 5 — Recommend follow-ups

- `/architect-perms` for CMT Record Manager permissions
- `/design-object` if the use case is actually a business entity, not configuration
- `/refactor-apex` if existing hardcoded rules should move to CMT

---

## What this command does NOT do

- Does not deploy CMT / Custom Setting metadata.
- Does not seed data records.
