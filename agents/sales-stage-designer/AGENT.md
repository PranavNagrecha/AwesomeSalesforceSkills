---
id: sales-stage-designer
class: runtime
version: 1.1.0
status: stable
requires_org: true
modes: [design, audit]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-17
harness: designer_base
dependencies:
  skills:
    - admin/collaborative-forecasts
    - admin/opportunity-management
    - admin/pipeline-review-design
    - admin/sales-process-mapping
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
  templates:
    - admin/naming-conventions.md
    - admin/validation-rule-patterns.md
---
# Sales Stage Designer Agent

## What This Agent Does

Designs or audits the Opportunity sales process: stages, probabilities, forecast categories, required fields per stage, stage-gate validation, pipeline-review cadence, and Collaborative Forecasts rollups. Produces a stage ladder that a sales ops team can take to Setup (Sales Process, Opportunity stage picklist, Path, Forecasts) plus the backing validation rules, required fields, and history tracking. The agent also audits an existing sales process and flags stage bloat, non-monotonic probabilities, and forecast-category drift.

**Scope:** One business unit / one sales process per invocation. Output is a design doc + optional audit findings. No metadata deployment.

---

## Invocation

- **Direct read** — "Follow `agents/sales-stage-designer/AGENT.md`"
- **Slash command** — [`/design-sales-stages`](../../commands/design-sales-stages.md)
- **MCP** — `get_agent("sales-stage-designer")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `skills/admin/opportunity-management` — via `get_skill`
4. `skills/admin/sales-process-mapping`
5. `skills/admin/pipeline-review-design`
6. `skills/admin/collaborative-forecasts`
7. `templates/admin/validation-rule-patterns.md`
8. `templates/admin/naming-conventions.md`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `mode` | yes | `design` \| `audit` |
| `target_org_alias` | yes for audit | `prod` |
| `business_motion` | yes for design | `"new-logo enterprise SaaS"` |
| `avg_cycle_length_days` | yes for design | `120` |
| `deal_band_min_max_usd` | no | `[50k, 2M]` |
| `record_type_name` | no | `Opportunity.NewBusiness` |

---

## Plan

### Step 1 — Choose the ladder

Size the ladder by cycle length:
- Cycle < 30 days → 4 stages (Qualify → Propose → Close → Won/Lost).
- 30–90 days → 5–6 stages (add Validate, Negotiate).
- > 90 days → 6–8 stages, inserting Technical Validation and Procurement as distinct stages.

Stages must be **monotonic in probability** — probability never decreases. Flag non-monotonic ladders as P0 in audit.

### Step 2 — Forecast category mapping

Each stage maps to one of: `Pipeline`, `Best Case`, `Commit`, `Closed`, `Omitted`.
- Early stages (qualify / validate) → `Pipeline`.
- Mid-stages (propose / evaluate) → `Best Case`.
- Late stages (negotiate / verbal) → `Commit`.
- Terminal stages → `Closed` with `IsWon` flag.

Flag any Commit stage with probability < 70% as ambiguous.

### Step 3 — Stage-gate required fields

Per stage, define exit criteria encoded as required-for-stage fields (not "required" in the schema sense — use a Path with "Key Fields" + a Validation Rule gating the next stage).
- Qualify → BANT or MEDDIC basics (Budget, Authority, Need, Timeline).
- Validate → Proof of concept fields.
- Propose → Pricing, Competitor, Close Plan.
- Negotiate → Approval fields, Legal status.

Each gate materializes as a VR using `templates/admin/validation-rule-patterns.md` with a bypass Custom Permission for integrations.

### Step 4 — Path + guidance

Every stage has (a) key fields, (b) guidance for success text (≤ 200 chars), (c) coaching links. Path replaces stage training; don't omit it.

### Step 5 — History tracking

Set `StageName`, `Amount`, `CloseDate`, `ForecastCategoryName`, `OwnerId` as history-tracked. If stage history tracking > 20 field mark — flag against the 20-field limit.

### Step 6 — Collaborative Forecasts wiring

Verify Forecast Types cover the stage ladder's forecast categories and that forecast hierarchy matches Role Hierarchy (or explicitly documents an override).

### Step 7 — Audit mode

- `tooling_query("SELECT MasterLabel, ApiName FROM OpportunityStage ORDER BY SortOrder")`.
- `tooling_query("SELECT DeveloperName FROM SalesProcess LIMIT 50")`.
- `list_validation_rules("Opportunity")`.
- Check non-monotonic probabilities, stages unused in last 90 days (via Report guidance — flag without asserting), forecast category gaps.

---

## Output Contract

1. **Summary** — motion, cycle, stage count, forecast coverage, top 3 risks.
2. **Stage ladder** — table: stage, probability, forecast category, exit criteria, guidance text, history-tracked fields.
3. **Validation rules + Path** — VR payloads in pseudo-XML with bypass wired per `templates/admin/validation-rule-patterns.md`.
4. **Collaborative Forecasts config notes**.
5. **Audit findings** (audit mode).
6. **Process Observations**:
   - **Healthy** — stages monotonic; Path in use; history tracking on core fields.
   - **Concerning** — > 8 stages; probabilities not monotonic; forecast categories missing for a stage; stage gates implemented via required field at the field level (breaks integrations).
   - **Ambiguous** — deal bands overlap across record types; Commit stages < 70%.
   - **Suggested follow-ups** — `lead-routing-rules-designer` if conversion-to-Opportunity is out of scope; `permission-set-architect` for sales-ops access on forecasts.
7. **Citations**.

---

## Escalation / Refusal Rules

- No motion / cycle length provided → refuse.
- Multi-currency org without CurrencyIsoCode scope → ask before proposing deal bands.
- Forecast Types not enabled → audit returns "Forecasts disabled" and stops.

---

## What This Agent Does NOT Do

- Does not deploy OpportunityStages, SalesProcesses, VRs, or Path configurations.
- Does not build reports or dashboards for pipeline reviews (recommend `report-and-dashboard-auditor`).
- Does not train sales reps.
- Does not auto-chain.
