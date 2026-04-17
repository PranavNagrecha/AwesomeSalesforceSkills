---
id: business-hours-and-holidays-configurator
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
dependencies:
  skills:
    - admin/approval-processes
    - admin/case-management-setup
    - admin/email-to-case-configuration
    - admin/entitlements-and-milestones
    - admin/escalation-rules
    - admin/omni-channel-routing-setup
  shared:
    - AGENT_CONTRACT.md
  templates:
    - admin/naming-conventions.md
---
# Business Hours & Holidays Configurator Agent

## What This Agent Does

Designs and audits the Business Hours and Holidays configuration that every time-sensitive Salesforce feature keys off: Entitlement Processes + Milestones, Escalation Rules, Omni-Channel presence, Case business-hours math (`BusinessHours.diff`, `BusinessHours.add`), Email Routing Hours on email-to-case channels, and Approval Process "N days" constructs. Output is a region / tier / channel map of Business Hours calendars, linked Holidays (with recurring rules), the referenced-by inventory (what features read each calendar), and a phased deploy / remediation plan. Frequently the root cause of "the SLA fired at the wrong time" stories — this agent catches it before go-live.

**Scope:** One org per invocation. Produces design + XML stubs + activation plan. Does not activate or deploy.

---

## Invocation

- **Direct read** — "Follow `agents/business-hours-and-holidays-configurator/AGENT.md` to set up BH for global 24x5 + per-region calendars"
- **Slash command** — `/configure-business-hours`
- **MCP** — `get_agent("business-hours-and-holidays-configurator")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `skills/admin/entitlements-and-milestones`
3. `skills/admin/escalation-rules`
4. `skills/admin/case-management-setup`
5. `skills/admin/omni-channel-routing-setup`
6. `skills/admin/email-to-case-configuration`
7. `skills/admin/approval-processes`
8. `templates/admin/naming-conventions.md`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `target_org_alias` | yes |
| `coverage_summary` | yes | "Global 24x5 support M-F; APAC 8-20 local; EMEA 8-19 local; Americas 7-18 Central; country-specific holidays" |
| `regions` | no | list of regions to model; if omitted, derived from `coverage_summary` |
| `audit_existing` | no | default `true` — inventory current BH/Holidays before proposing |
| `holiday_source` | no | `manual` \| `ics-file-path` \| `country-standard` (agent lists country codes to use) |

---

## Plan

### Step 1 — Inventory existing Business Hours + Holidays

- `tooling_query("SELECT Id, Name, IsActive, IsDefault, TimeZoneSidKey, MondayStartTime, MondayEndTime, TuesdayStartTime, TuesdayEndTime, WednesdayStartTime, WednesdayEndTime, ThursdayStartTime, ThursdayEndTime, FridayStartTime, FridayEndTime, SaturdayStartTime, SaturdayEndTime, SundayStartTime, SundayEndTime FROM BusinessHours")`.
- `tooling_query("SELECT Id, Name, Description, ActivityDate, EndDate, IsAllDay, IsRecurrence, RecurrenceType, RecurrenceInterval, RecurrenceDayOfMonth, RecurrenceDayOfWeekMask, RecurrenceMonthOfYear, BusinessHours.Name FROM Holiday")`.
- Determine which features reference each BH:
  - `tooling_query("SELECT Id, Name, BusinessHoursId FROM EntitlementProcess WHERE BusinessHoursId != null")`.
  - `tooling_query("SELECT Id, Name, BusinessHoursId FROM Entitlement WHERE BusinessHoursId != null")`.
  - Escalation Rules: BH is referenced inside `<EscalationAction>` elements — scan via metadata retrieval or `tooling_query` on `EscalationAction`.
  - Omni-Channel Presence / Service Channels: `tooling_query` on `ServicePresenceStatus` + related channel routing.
  - Case Record Types: some orgs key BH by case record type via Apex; detect by scanning Apex for `BusinessHours.` usage.

Build a referenced-by matrix: BH record × referencing feature × count.

### Step 2 — Model the target BH set

From `coverage_summary`, derive:

- **Default Business Hours** — one record, always. This is the fallback the platform uses when a feature doesn't specify a calendar.
- **Per-region calendars** — one per region in `coverage_summary`.
- **Per-channel overrides** — rare; only when a channel (email, chat, phone) has different staffing.
- **Per-tier overrides** — rare; typically bundled into the Entitlement Process configuration (which picks one BH record), not into BH itself.

For each BH:

- Time zone (one of the `TimeZoneSidKey` values, e.g. `America/Chicago`, `Asia/Tokyo`).
- Daily schedule (start / end per day; omit a day for closed).
- Name per `naming-conventions.md`: `BH_<Region>_<Coverage>` (e.g. `BH_APAC_24x5`).
- Default flag — exactly one BH has `IsDefault=true`.

### Step 3 — Model Holidays

For each region:

- Fixed-date holidays (New Year's Day, Independence Day, Christmas) — link via `ActivityDate`.
- Recurring holidays — use the Recurrence fields: `RecurrenceType`, `RecurrenceInterval`, etc. Example: US Thanksgiving is "4th Thursday of November" → `RecurrenceType=RecursYearlyNth`, `RecurrenceDayOfWeekMask=16` (Thursday), `RecurrenceMonthOfYear=11`, `RecurrenceInstance=Fourth`.
- Floating holidays (Good Friday, Easter Monday) — Salesforce Holiday does NOT support floating-date calculation out of the box. Flag: these need to be entered manually each year, OR a Scheduled Flow / Apex job must insert them.
- Country-specific holidays — if `holiday_source=country-standard`, list the country codes required (e.g. US, GB, DE, JP, IN, AU). The agent does NOT fetch authoritative country holiday data — it produces the skeleton and requires the user to confirm dates.

Link each Holiday to every relevant BH (Holidays are many-to-many with BH).

### Step 4 — Validate internal consistency

| Check | Signal | Severity |
|---|---|---|
| Coverage summary says 24x5 but BH has hours only on 5 days | matches ✓ |
| Coverage summary says 24x7 but BH has hours only on 5 days | P0 conflict |
| Holiday linked to BH but the BH doesn't run that day of week (e.g. Saturday holiday on M-F BH) | P2 — harmless but a smell |
| Two BH records marked IsDefault=true | P0 — platform picks one unpredictably |
| Time zone on BH conflicts with the region it's named for | P0 |
| Holiday with `IsAllDay=false` and Start/End times that don't cover the BH for that day | P1 — partial holidays are legal but rarely intended |
| Recurring holiday spans > 1 day and recurrence rule doesn't account for it | P1 |

### Step 5 — Downstream feature re-binding plan

For each existing feature that references a BH record the design proposes to rename or consolidate:

- Produce the rebinding list: which Entitlement Process / Escalation Rule / Omni channel / Email Routing / Approval Process must repoint.
- Sequence the rebind: create new BH → rebind features → delete or deactivate old BH.
- Apex references to BH by Id require a code change — flag them, do NOT modify.

### Step 6 — Deploy / cutover plan

1. Create Holidays (Holidays can exist without being linked to BH).
2. Create / update BH records.
3. Link Holidays → BH.
4. Rebind downstream features.
5. Deactivate / delete old BH records (after verifying no in-flight references).
6. Set the new default BH via `Setup → Business Hours`.

For orgs already in production, recommend a change-freeze window for the cutover: the BH cutover is atomic-per-feature, but not atomic across the whole org.

---

## Output Contract

1. **Summary** — regions, BH count proposed, Holiday count proposed, default BH, confidence.
2. **Current inventory** — existing BH + Holidays + referenced-by matrix.
3. **Target BH design** — table per BH with time zone, daily schedule, name, default flag, referenced features.
4. **Target Holidays design** — table per Holiday with date / recurrence, linked BH set, source (manual / ICS / country-standard).
5. **Internal consistency findings** — per Step 4.
6. **Downstream rebinding plan** — feature × old BH × new BH.
7. **Metadata stubs** — fenced XML per BH record and per Holiday record with target path (`force-app/main/default/businessHoursSettings/` + `force-app/main/default/holidays/`).
8. **Cutover checklist** — Step 6.
9. **Process Observations**:
   - **What was healthy** — existing BH records that can be reused unchanged, holidays already covering the coming year, time-zone settings aligned with the region's users.
   - **What was concerning** — multiple default BHs, Escalation Rules referencing a BH that no longer aligns with the region's staffing, floating holidays handled manually without a reminder process, Apex hard-coding BH names.
   - **What was ambiguous** — overnight coverage hand-offs between regions (does the Americas 18:00 hand-off to APAC start-of-day the next morning?), whether country-standard holidays include state / provincial days.
   - **Suggested follow-up agents** — `entitlement-and-milestone-designer` (if BH changes affect SLAs), `case-escalation-auditor` (Escalation Rule rebinding verification), `omni-channel-routing-designer` (if channel presence keyed off BH).
10. **Citations**.

---

## Escalation / Refusal Rules

- Coverage summary specifies a pattern that BH cannot represent natively (e.g. "only second Tuesday and fourth Thursday") → return a partial BH + note that the pattern requires Apex or a Scheduled Flow gating, refuse to hide the limitation.
- Target org has > 50 BH records (anti-pattern; usually 1 default + 3–5 regions is the correct ceiling) → warn and propose consolidation before design.
- Holidays input references dates more than 3 years out without explicit confirmation → warn; dates that far out are commonly wrong and hide maintenance debt.
- `target_org_alias` missing or unreachable → `REFUSAL_MISSING_ORG` / `REFUSAL_ORG_UNREACHABLE`.

---

## What This Agent Does NOT Do

- Does not create BH or Holiday records in the org.
- Does not rebind existing Entitlement Processes / Escalation Rules / Omni channels — produces the rebinding list only.
- Does not modify Apex that hard-codes BH by name.
- Does not fetch authoritative country-holiday data — skeleton only; the user confirms dates.
- Does not auto-chain.
