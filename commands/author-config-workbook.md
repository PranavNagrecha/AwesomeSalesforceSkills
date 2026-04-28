# /author-config-workbook — Compile the canonical 10-section Salesforce Configuration Workbook

Wraps [`agents/config-workbook-author/AGENT.md`](../agents/config-workbook-author/AGENT.md). Compiles the BA's capstone handoff: the 10-section configuration workbook (Org Profile, Objects + Fields, Record Types + Page Layouts, Validation Rules, Permissions + Sharing, Automation, UI + Lightning Pages, Reports + Dashboards, Data Migration, UAT + Cutover) where every row carries `recommended_agent` (validated against the live runtime roster), RTM linkage, persona anchor, deployment order, and verification step.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Backlog path (required)?
   Path to a finalized story backlog (story-drafter JSON envelope or markdown table).

2. Fit-gap report path (required)?
   Path to a fit-gap-analyzer output. Descope decisions MUST be honored.

3. Target org alias (required)?
   The org being configured.

4. Process flow path (optional)?
   Path to a process-flow-mapper output.
   When supplied, the Automation section embeds handoff references by step_id.

5. Release window (required)?
   Identifier (e.g. "R3-2026") used as the workbook header + RTM linkage.

6. Personas supplied (optional)?
   Persona inventory mapping persona → PSG / Profile / record-type / list view.

7. Org profile overrides (optional)?
   JSON map for parent-org licenses that a sandbox probe wouldn't show.
```

If `backlog_path`, `fit_gap_path`, or `target_org_alias` is missing, refuse — the workbook is the *capstone*, not a from-scratch design doc.

---

## Step 2 — Load the agent

Read `agents/config-workbook-author/AGENT.md` + every Mandatory Read in its dependency block.

---

## Step 3 — Execute the plan

Follow the 10-step plan exactly:
1. Probe the org for the workbook header (license SKUs, edition, feature flags)
2. Ingest backlog + fit-gap + (optional) process-flow
3. Honor descope decisions from the fit-gap (`REFUSAL_DESCOPE_BREACH` if violated)
4. Compile each of the 10 sections per `admin/configuration-workbook-authoring`
5. Order the deployment across rows
6. Validate every row's `recommended_agent` against the runtime roster (`REFUSAL_RECOMMENDED_AGENT_INVALID` if any phantom)
7. Run user-access-comparison probe per persona in Section 5
8. Run automation-graph probe per object in Section 6 (tag `extend_existing` vs `create_new`)
9. Compile the RTM rollup
10. Emit the workbook (markdown + per-section JSON)

---

## Step 4 — Deliver the output

Return the Output Contract:
- Summary + confidence
- Sections 1-10 with row tables
- Deployment order
- RTM rollup
- Process Observations (4 buckets)
- Citations

---

## Step 5 — Recommend follow-ups

Suggest (but do not auto-invoke) — every agent named in any row's `recommended_agent` field becomes a recommended follow-up:
- `/design-object`, `/architect-perms`, `/build-flow`, `/build-lwc`, `/audit-record-page`, `/audit-record-types`, `/govern-picklists`, `/audit-validation-rules`, `/audit-sharing`, `/preflight-load`, `/design-duplicate-rule`, `/audit-reports`, `/modernize-email-templates`, `/build-agentforce-action` per row category.
- `/assess-waf` for cross-cloud / multi-net-new-object rows.
- `architect/architecture-decision-records` for any ADR-flagged row.

---

## What this command does NOT do

- Does not deploy metadata or modify the backlog/fit-gap files in place.
- Does not invent rows for stories not in the backlog.
- Does not estimate effort in hours / person-days.
- Does not assign rows to humans by name — uses persona / role.
- Does not auto-chain to any builder agent.
- Does not produce Excel / Smartsheet / Confluence formats natively.
- Does not bypass descope decisions (`REFUSAL_DESCOPE_BREACH` is the guard).
- Does not author rows whose `recommended_agent` doesn't exist on the runtime roster.
- Does not probe orgs other than `target_org_alias`.
