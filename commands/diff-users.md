# /diff-users — Side-by-side access comparison between two Salesforce users

Wraps [`agents/user-access-diff/AGENT.md`](../agents/user-access-diff/AGENT.md). Produces a symmetric comparison across profile, PS/PSG, object CRUD, FLS, system permissions, Apex/VF grants, groups, queues, and territory — with risk flags for any asymmetric sensitive permission.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Target org alias (required — agent needs live-org access via `sf` CLI)?

2. User A (username or 15/18-char User.Id)?

3. User B (username or 15/18-char User.Id)?

4. Which dimensions to compare? (default: all)
   Options: profile, permission-sets, object-crud, fls, system-perms,
            apex-classes, vf-pages, tabs, apps, record-types,
            custom-perms, groups, queues, territories

5. Include field-level security diff? (default: no)
   FLS rows can exceed 10k on broad PSGs — turn on only when needed.

6. Purpose? (optional — shapes the Process Observations framing)
   Options: new-hire-parity | access-review | incident-investigation
```

If `user_a` == `user_b`, STOP — this agent compares two different users.

If either user isn't resolvable in the target org, STOP and ask for clarification.

---

## Step 2 — Load the agent

Read `agents/user-access-diff/AGENT.md` + all mandatory reads (probe recipe, `admin/user-management`, `admin/permission-set-architecture`, `admin/permission-sets-vs-profiles`, `security/permission-set-groups-and-muting`, plus the probe under `agents/_shared/probes/user-access-comparison.md`).

---

## Step 3 — Execute the plan

Follow the agent's 6-step plan:

1. Resolve both users to `User.Id`.
2. Run `agents/_shared/probes/user-access-comparison.md` for both users, flattening PSG components into effective PS sets.
3. Compute symmetric diffs per dimension (identical / only_a / only_b).
4. Apply the P0/P1/P2 risk rubric.
5. Frame Process Observations per the supplied `purpose`.
6. Emit the report.

---

## Step 4 — Deliver the output

Return the Output Contract:
- Summary (counts, highest severity)
- Confidence (HIGH/MEDIUM/LOW)
- User header table (both users side by side)
- Per-dimension diff tables (identical / only A / only B)
- Effective access summary (what each user can actually read/edit/delete)
- Risk flags table (severity, dimension, delta, recommended next step)
- Process Observations (Healthy / Concerning / Ambiguous / Suggested follow-ups)
- Citations

---

## Step 5 — Recommend follow-ups

Based on what the diff surfaced:
- `/architect-perms` — if remediation is needed (this agent is read-only)
- `/audit-sharing` — if two users should see the same records but don't (record visibility, not permission)
- `/migrate-profile-to-permset` — if Profile difference dominates the delta

---

## What this command does NOT do

- Does not grant, revoke, or modify any access.
- Does not compute sharing-rule outcomes — use `/audit-sharing` for record-visibility differences.
- Does not explain historical "why" — use audit trail separately.
- Does not compare more than two users per invocation.
- Does not propose a remediation PSG design — that's `/architect-perms`.
