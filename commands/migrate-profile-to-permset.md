# /migrate-profile-to-permset — Decompose a Profile into Permission Sets + PSGs

Wraps [`agents/profile-to-permset-migrator/AGENT.md`](../agents/profile-to-permset-migrator/AGENT.md). Minimizes the profile to its mandatory residue (license, default record type, default app, page layouts, login IP/hours, session) and emits the PS + PSG layout that absorbs every migratable permission.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Target org alias (required — agent probes ProfileName, PermissionSet, PermissionSetGroup, object perms)?

2. Profile(s) to migrate?
   Either one profile name OR a name filter ("Sales*", "*Admin*").

3. Grouping strategy?
   Options: by-object | by-persona | by-feature | hybrid (recommended)

4. PSG composition goal? (flatten | nested-by-persona | baseline + overlays)

5. Rollout mode? (shadow-assign | cutover | parallel)
```

If more than 5 profiles match the filter, STOP and ask for a narrower scope — this agent processes one workstream at a time.

---

## Step 2 — Load the agent

Read `agents/profile-to-permset-migrator/AGENT.md` + mandatory reads (security/profile-to-permset-strategy, admin/permission-set-groups, security/least-privilege-principles).

---

## Step 3 — Execute the plan

- Probe profile to enumerate every permission.
- Classify each permission: mandatory residue (stays on profile) vs migratable (moves to PS).
- Group migratable permissions per chosen strategy.
- Author PermissionSet + PermissionSetGroup definitions.
- Design rollout mode (shadow-assign to validate before cutover).

---

## Step 4 — Deliver the output

- Summary + confidence
- Residue table (what stays on the profile and why)
- PermissionSet / PermissionSetGroup list
- PS definitions (metadata snippets)
- PSG composition map
- Rollout plan + validation queries
- Process Observations
- Citations

---

## Step 5 — Recommend follow-ups

- `/architect-perms` for a clean-slate persona redesign if residue is large
- `/audit-sharing` after migration to verify no permission drift
- `/scan-security` if object CRUD changed

---

## What this command does NOT do

- Does not deploy PS/PSG metadata.
- Does not assign PS to users — produces the assignment plan.
- Does not retire profiles — Salesforce requires one per user.
