# /architect-perms — Design or audit Permission Sets + Permission Set Groups

Wraps [`agents/permission-set-architect/AGENT.md`](../agents/permission-set-architect/AGENT.md). Two modes: `design` (from a persona) or `audit` (against the live org).

---

## Step 1 — Collect inputs

Ask the user:

```
1. Mode: design or audit?

2. Target org alias (required — live-org probe in both modes)?

3. If mode = design:
   Persona description (job title + objects touched + features used + sensitivity)?
   Example: "SDR in NA, works Leads + Opportunities, cannot export data, light reporting"

4. If mode = audit:
   Scope? org / psg:<PSG_Name> / ps:<PS_Name> / user:<username>

5. If mode = design:
   Extending an existing PSG? (Optional — pass the PSG name)
```

If mode is `design` and persona is under 10 words, STOP and ask.

---

## Step 2 — Load the agent

Read `agents/permission-set-architect/AGENT.md` + mandatory reads. In particular, read `templates/admin/permission-set-patterns.md` — it's the taxonomy the audit + design both conform to.

---

## Step 3 — Execute the plan

Design mode:
1. Decompose persona into 6 PS categories
2. Probe for reusable Feature PSes (`list_permission_sets` + `describe_permission_set`)
3. Propose the PSG composition
4. Identify muting opportunities
5. Emit metadata stubs
6. Emit deployment order

Audit mode:
1. Scope the probe
2. Classify each PS against the taxonomy
3. Detect anti-patterns (Modify All Data on persona, single-user PSes, muting PS with no parent, etc.)
4. Score the org

---

## Step 4 — Deliver the output

- Summary + confidence
- Findings table (audit) / Composition table (design)
- Metadata stubs (design only, fenced XML)
- Deployment order (design only)
- Recommended refactors (audit only)
- Process Observations
- Citations

---

## Step 5 — Recommend follow-ups

- `/sharing-audit` if the audit surfaced broad record-level access concerns (Wave B agent)
- `/catalog-integrations` if integration-user permissions surfaced as findings (Wave B agent)
- `/analyze-field-impact` if FLS changes are implied
- `/design-object` if missing objects underlie the design gap

---

## What this command does NOT do

- Does not assign Permission Sets to users.
- Does not deploy metadata.
- Does not modify an existing PS in place (refactors are proposed as new PSes + migration).
- Does not audit Sharing Rules / OWD (that's the Wave B `sharing-audit-agent`).
