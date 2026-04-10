# Examples — Marketing Reporting Requirements

## Example 1: B2B SaaS Company Choosing an Attribution Model

**Context:** A B2B SaaS company with a 90-day average sales cycle wants to prove marketing's contribution to pipeline. The marketing director wants to report "marketing-influenced pipeline" to the CFO but the sales operations team is already using the Primary Campaign Source field for first-touch reporting. The org has Salesforce Enterprise edition and MCAE but no B2B Marketing Analytics Plus license.

**Problem:** The marketing director asks for "all pipeline that marketing touched." Without defining attribution precisely, the implementation team builds a report using Primary Campaign Source (which is a first-touch, single-campaign metric), presents it as influenced pipeline, and the number is 40% lower than stakeholders expected. Trust in the data collapses and the project is restarted.

**Solution:**

```
Attribution Model Decision Record
──────────────────────────────────────────────────────────
Business question: What percentage of closed-won revenue
  was touched by a marketing campaign at any point?
Chosen model: Even Distribution (Customizable Campaign Influence)
Salesforce feature required: Customizable Campaign Influence
  (Enterprise edition — confirmed licensed)
Prerequisite check:
  - Opportunity Contact Roles: populated on 87% of Opp records
    (gap: 13% of Opportunities have no Contact Roles;
     remediation plan: Salesforce Flow to prompt on close stage)
  - Campaign Influence: ENABLED in Setup > Campaign Influence
  - Lookback window: updated from 30 days to 120 days to match
    90-day sales cycle plus 30-day buffer
Distinct metrics defined:
  - Marketing-sourced pipeline: Primary Campaign Source populated
    on Opportunity (uses existing field, no CCI required)
  - Marketing-influenced pipeline: CampaignInfluence object
    record exists on Opportunity (requires CCI + Contact Roles)
Sign-off: Marketing Director, VP Sales Ops — 2026-03-15
```

**Why it works:** Documenting the model choice before any report is built ensures that "influenced pipeline" is defined identically by marketing and sales ops. The lookback window adjustment is critical for a 90-day sales cycle: the default 30-day window would exclude the majority of early-funnel campaign touches.

---

## Example 2: Enterprise Manufacturing Company Requiring Email Engagement KPIs

**Context:** A manufacturing company's marketing team sends product newsletters via MCAE. They want a dashboard showing open rates, click rates, cost per lead by campaign, and campaign ROI alongside the existing Campaign Performance Report. Salesforce org is Enterprise, MCAE is connected, but Campaign Member statuses have never been configured beyond the two defaults (Sent, Responded).

**Problem:** The requirements document lists "email open rate by campaign" as a KPI. The implementation team discovers that MCAE writes engagement data to Campaign Member Status values, but because only "Sent" and "Responded" statuses exist, click and open data cannot be captured. The dashboard is built with placeholder components and the launch is delayed 6 weeks while statuses are reconfigured and historical data is re-synced.

**Solution:**

```
KPI Definition Register (excerpt)
──────────────────────────────────────────────────────────
KPI: Email Open Rate
Definition: Unique opens / Total sent emails, per campaign
Salesforce source: Campaign Members with Status = "Opened"
  / Campaign Members with Status = "Sent"
Required configuration:
  - Campaign Member Status "Opened" must exist on each email
    campaign type (MCAE writes to this status on open event)
  - Campaign Member Status "Clicked" must exist for click rate
  - MCAE campaign connector must be active and syncing
Native or add-on: NATIVE (no add-on required if statuses
  are configured and MCAE connector is active)
Gap note: Current org has only "Sent" and "Responded" statuses.
  Remediation: Add "Opened", "Clicked", "Unsubscribed" statuses
  to email campaign record types before first sync.
  Data will not backfill for sends prior to status addition.
```

**Why it works:** Identifying the Campaign Member Status gap during requirements — rather than after dashboard build — allows the remediation to happen before data collection begins. Backfilling engagement data for past sends is not possible once the status is added; only future sends are captured. Catching this in requirements avoids a launch with permanently incomplete historical data.

---

## Anti-Pattern: Building Dashboards Before the Attribution Model Decision

**What practitioners do:** The team receives a request to "build a marketing dashboard" and immediately starts selecting report types, creating dashboard components, and configuring Campaign Influence based on an assumed First Touch model. The attribution question is deferred because it "seems like a detail."

**What goes wrong:** Three months into the project, leadership wants to change to an Even Distribution model to share credit across multiple campaigns. Customizable Campaign Influence has a fundamentally different data model from standard Campaign Influence — the CampaignInfluence object records replace the single Primary Campaign Source field. All reports built against Primary Campaign Source must be rebuilt. All historical data associations must be reprocessed. The lookback window must be reconfigured. Stakeholder trust is damaged because the numbers change significantly.

**Correct approach:** Run the attribution model decision workshop as step one, before any report type or dashboard component is selected. Document the decision with business rationale and sign-off. Only then begin selecting report types and configuring Campaign Influence. The 30–60 minutes spent on the decision saves weeks of rework.
