# /map-process-flow — Map a process narrative to a Salesforce-aware swim-lane flow

Wraps [`agents/process-flow-mapper/AGENT.md`](../agents/process-flow-mapper/AGENT.md). Produces a swim-lane diagram annotated with the canonical automation-tier syntax (`[FLOW] [APEX] [APPROVAL] [PLATFORM_EVENT] [INTEGRATION] [MANUAL]`), a handoff catalog with per-handoff `recommended_agents[]`, and (optionally) a story_id overlay tying every step to a backlog story.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Process narrative path (required)?
   Markdown describing the process. Can be a transcript, problem statement,
   as-is/to-be document, or hand-authored narrative.

2. Process kind (required)?
   as-is-only / to-be-only / as-is-to-be / green-field

3. Process label (required, one sentence)?
   Example: "Quote-to-Cash for SaaS subscriptions"

4. Backlog path (optional)?
   When supplied, every step gets tagged with the matching story_id.
   Use story-drafter output for cleanest overlay.

5. Target org alias (optional)?
   When supplied, runs automation-graph-for-sobject per object referenced
   to surface existing-automation overlap.

6. Personas supplied (optional)?
   Persona inventory mapping persona → PSG / Profile / record-type / list view.

7. Surfaces in scope (optional)?
   Comma-separated, e.g. "sales-cloud,experience-cloud" — narrows lane scope.
```

If `process_narrative_path` is empty or parses to < 4 atomic steps, refuse and recommend a workshop pass.

---

## Step 2 — Load the agent

Read `agents/process-flow-mapper/AGENT.md` + every Mandatory Read in its dependency block.

---

## Step 3 — Execute the plan

Follow the 9-step plan exactly:
1. Parse the narrative into atomic steps
2. Anchor swim lanes to personas + system actors with RACI
3. Tier-tag every step (`[FLOW] [APEX] [APPROVAL] [PLATFORM_EVENT] [INTEGRATION] [MANUAL]`) — citing the decision-tree branch
4. Detect handoffs (lane↔lane and tier↔tier transitions)
5. Wire `recommended_agents[]` per handoff
6. Wire `recommended_skills[]` per handoff
7. Overlay backlog story_ids (when supplied)
8. Probe org for automation overlap (when supplied)
9. Detect process gaps (missing accountable role, tier mismatches, missing NFR class, cross-cloud without ADR)

---

## Step 4 — Deliver the output

Return the Output Contract:
- Summary + confidence
- Swim-lane diagram
- Step inventory
- Handoff catalog with recommended_agents[]
- As-is vs to-be delta (when applicable)
- Process Observations (4 buckets)
- Citations

---

## Step 5 — Recommend follow-ups

Suggest (but do not auto-invoke):
- `/build-flow` for `[FLOW]` lanes
- `/plan-bulk-migration` for integration handoffs
- `/catalog-integrations` to register external systems
- `/audit-sharing` for sharing crossings
- `/architect-perms` for new persona PSGs
- `/draft-stories` if step-to-story coverage is < 80%
- `/author-config-workbook` to compile final admin handoff

---

## What this command does NOT do

- Does not deploy flows, does not generate Flow XML, does not write Apex.
- Does not invent process steps beyond the supplied narrative.
- Does not estimate hours / effort.
- Does not produce Visio / Lucidchart / BPMN XML natively.
- Does not auto-chain to any other command — handoffs are advisory.
- Does not assign owners by name — RACI uses role labels.
