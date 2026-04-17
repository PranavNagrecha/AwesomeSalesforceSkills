# /build-changeset — Build or validate a deployment Change Set manifest

Wraps [`agents/changeset-builder/AGENT.md`](../agents/changeset-builder/AGENT.md). Produces a dependency-ordered component list, destructive-changes list, and post-deploy activation checklist.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Mode? build | validate

2. Source org alias (required — agent verifies every named component exists)?

3. Target org alias (required — agent checks receivability + conflicts)?

4. Feature description OR artifact list?
   Example: "EPIC-1472 — revenue recognition v2", or a bullet list of API names.

5. Destructive changes? (yes / no — default no; if yes, provide removal list)
```

If source or target org is missing, STOP.

---

## Step 2 — Load the agent

Read `agents/changeset-builder/AGENT.md` + mandatory reads (devops/change-sets, devops/deployment-dependencies, devops/destructive-changes).

---

## Step 3 — Execute the plan

- Probe source org for each named artifact.
- Enumerate implicit dependencies (profile → object, VR → object, Apex → object, etc.).
- Build a topologically-ordered component list.
- Validate mode: dry-run against target and surface conflicts.

---

## Step 4 — Deliver the output

- Summary + confidence
- Component list (ordered)
- Dependency graph (mermaid or ASCII)
- Deployment order
- Destructive-changes list (if applicable)
- Post-deploy activation checklist
- Conflicts + unresolved refs (validate mode)
- Process Observations
- Citations

---

## Step 5 — Recommend follow-ups

- `/score-deployment` before actually deploying
- `/detect-drift` on target org ahead of deploy
- `/plan-release-train` if this is part of a coordinated release

---

## What this command does NOT do

- Does not deploy.
- Does not create the Change Set in Setup — produces the plan for a human to execute.
- Does not package for 2GP / unlocked packages (out of scope).
