# /draft-stories — Draft a Salesforce-aware INVEST story backlog

Wraps [`agents/story-drafter/AGENT.md`](../agents/story-drafter/AGENT.md). Produces a backlog of INVEST stories with given/when/then AC, S/M/L/XL sizing, MoSCoW priority, fit tier, NFR class, training impact, and per-story `recommended_agents[]` + `recommended_skills[]` handoff metadata. Also emits an RTM and capacity check.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Discovery artifact path (required)?
   A markdown file containing a transcript, problem statement, requirements list, or process narrative.

2. Discovery artifact kind?
   transcript / problem-statement / requirements-list / process-narrative

3. Feature scope (one sentence)?
   Example: "Account-team automation for Mid-Market accounts"

4. Target org alias (optional)?
   When supplied, fit-tier confidence elevates from MEDIUM to HIGH after a license + similar-object probe.

5. Personas supplied (optional)?
   Path to a persona inventory mapping persona → PSG / Profile / record-type / list view.
   If absent, the agent infers and flags inferred personas as ambiguities.

6. Release capacity points (optional)?
   Story-points capacity for the target release window.
   When supplied, MoSCoW pass enforces the 60% Must-have rule.

7. Priority overrides (optional)?
   JSON map of {requirement_id: priority} applied AFTER MoSCoW.
```

If `discovery_artifact_path` is empty or under 5 distinct requirements after parsing, STOP and ask clarifying questions per the agent's Escalation rules.

---

## Step 2 — Load the agent

Read `agents/story-drafter/AGENT.md` + every Mandatory Read in its dependency block.

---

## Step 3 — Execute the plan

Follow the 9-step plan exactly:
1. Parse the discovery artifact into atomic requirements
2. Anchor every persona to a concrete Salesforce PSG / Profile / record-type / list view
3. Cluster requirements into epics + vertical slices (no horizontal layer splits)
4. Draft each story with INVEST shape + ≥3 Gherkin AC + S/M/L/XL sizing + fit tier + NFR class + training impact
5. Wire `recommended_agents[]` per story (the handoff seam)
6. Wire `recommended_skills[]` per story (3–8 each)
7. Apply MoSCoW + WSJF + 60% capacity rule
8. Emit Requirements Traceability Matrix rows
9. Detect handoff gaps (missing personas, license gaps, cross-cloud, AI surface, missing process flow)

---

## Step 4 — Deliver the output

Return the Output Contract:
- Summary + confidence
- Persona anchor table
- Story backlog grouped by epic
- RTM rows
- MoSCoW capacity check
- Process Observations (4 buckets)
- Citations

---

## Step 5 — Recommend follow-ups

Suggest (but do not auto-invoke):
- `/run-fit-gap` for L/XL stories that need org-confirmed fit-tier
- `/map-process-flow` when stories span > 1 system / cloud
- `/author-config-workbook` to compile the final admin handoff once the backlog stabilizes
- The agents named in each story's `recommended_agents[]`

---

## What this command does NOT do

- Does not estimate stories in hours or assign owners by name.
- Does not push stories to Jira / ADO / Linear.
- Does not invent requirements beyond the supplied artifact.
- Does not auto-chain to any other command — handoffs are advisory.
- Does not write code, metadata, or org-deployable artifacts.
