# /design-duplicate-rule — Design a Matching Rule + Duplicate Rule pair

Wraps [`agents/duplicate-rule-designer/AGENT.md`](../agents/duplicate-rule-designer/AGENT.md). Produces Setup-ready Matching Rule + Duplicate Rule XML with the bypass Custom Permission for integrations.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Object API name?
   Example: Lead

2. Target org alias (required)?

3. Policy?
   block              - hard block on exact match
   alert              - warn but allow
   block-on-create-only
   alert-on-create-only

4. Match basis?
   email / phone / name+company / custom:<comma-separated API names>
   Example: email  OR  custom:Email,Company,Country

5. Fuzziness? exact (default) / fuzzy
   (Some fields only support exact — agent downgrades with a note if needed)

6. Integration exempt? yes (default) / no
   (If yes, the agent emits a Bypass_Duplicate_Rule_<Object> Custom Permission stub)
```

If `policy=block` and the object is `Lead`, the agent will flag that Lead Convert does NOT fire duplicate rules — plan accordingly.

---

## Step 2 — Load the agent

Read `agents/duplicate-rule-designer/AGENT.md` + mandatory reads.

---

## Step 3 — Execute the plan

1. Inventory existing match + duplicate rules on the object (refuse to design competing rules)
2. Validate the match_basis (field types, fuzzy support)
3. Design the Matching Rule (emit XML)
4. Design the Duplicate Rule with policy (emit XML)
5. Handle Convert + Merge boundaries (Lead especially)
6. Integration exemption pattern (Custom Permission stub)
7. Emit the test plan

---

## Step 4 — Deliver the output

- Summary + confidence
- Matching Rule XML (fenced block with target path)
- Duplicate Rule XML (fenced block with target path)
- Custom Permission stub (if new)
- Interaction notes (Convert, Merge, Person Accounts)
- Test plan
- Process Observations
- Citations

---

## Step 5 — Recommend follow-ups

- `/architect-perms` if the bypass Custom Permission is new and needs PSG integration
- `/preflight-load` for any integration that will hit the rule
- `/analyze-field-impact` for the matched fields

---

## What this command does NOT do

- Does not activate or deploy rules.
- Does not merge existing duplicates (separate job — cite `skills/data/large-scale-deduplication`).
- Does not modify match fields.
- Does not override Lead Convert or Merge behavior.
