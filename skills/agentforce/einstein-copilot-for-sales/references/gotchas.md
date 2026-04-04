# Gotchas — Einstein Copilot for Sales

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Opportunity Scoring Requires 200+ Closed Opportunities in the Last 2 Years — or It Silently Does Nothing

**What happens:** When an org enables Opportunity Scoring with fewer than 200 closed opportunities (IsClosed = true, CloseDate within the last 730 days), the feature appears active in Setup and the `Opportunity Score` field is present on layouts — but no scores are ever generated. The Setup screen shows "Insufficient Data" as the model training status. Opportunity records display blank score fields with no inline error message to the rep.

**When it occurs:** Any org that is relatively new, has migrated from another CRM without importing historical closed opportunities, or has had low pipeline volume. The two-year window is also a trap for orgs that have been on Salesforce for years but only started closing deals recently.

**How to avoid:** Before enabling Opportunity Scoring in a customer rollout, run the SOQL count query against the production org:
```text
SELECT COUNT() FROM Opportunity WHERE IsClosed = true AND CloseDate >= LAST_N_DAYS:730
```
If the count is below 200, communicate the dependency clearly to stakeholders and defer the feature enablement. Consider importing historical closed-won and closed-lost data if available from a prior system.

---

## Gotcha 2: EAC Synced Activities Are Not Stored in Standard Salesforce Activity Objects and Do Not Appear in Standard Reports

**What happens:** After EAC is enabled and syncing, sales managers build Activity reports (or use existing ones) expecting to see rep email activity. The reports return no EAC-synced emails or calendar events. The data appears only in the Activity Timeline component on record pages, not in reports built on the `Activities`, `Tasks`, or `Events` report types.

**When it occurs:** Any org that relies on Activity reports for rep performance tracking, coaching dashboards, or compliance auditing. It also affects integrations and automation that query `Task` or `Event` objects expecting EAC-synced data to be present there.

**How to avoid:** Understand that EAC data lives in a separate data store and is surfaced through the Activity Timeline UI component and through specialized Einstein Activity Capture report types (available in the Report Type setup when EAC is enabled). If reporting on EAC activity is a hard requirement, use the `Einstein Activity Capture` report types added by the feature, or use CRM Analytics (Einstein Analytics) datasets that include EAC data. Do not promise standard report compatibility without validating this first.

---

## Gotcha 3: Einstein Generative Email (AI Email Drafting) Requires Einstein Generative AI License — Not Just Einstein for Sales

**What happens:** An org with Einstein for Sales enabled cannot find or activate the "Write Email with Einstein" (generative email drafting) button for reps. The feature simply does not appear in the email activity composer. Admins search Setup for "Generative Email" and find the setting greyed out or absent.

**When it occurs:** Orgs that purchased Einstein for Sales add-on only (without Einstein 1 Sales edition or the separate Einstein Generative AI / Einstein GPT entitlement). Einstein for Sales includes Opportunity Scoring, EAC, Pipeline Inspection, and the older Einstein Email Recommendations (suggested replies based on templates) — but NOT generative AI drafting from a natural-language prompt.

**How to avoid:** Before scoping a generative email feature in a Sales rollout, verify the license manifest at Setup > Company Information > Feature Licenses. The required entitlement is labeled "Einstein Generative AI" (or the edition is "Einstein 1 Sales"). If it is absent, do not build user enablement materials or training that reference AI email drafting. Escalate to the account team to add the Einstein Generative AI entitlement or upgrade to Einstein 1 Sales.

---

## Gotcha 4: Pipeline Inspection AI Insights Panel Shows Nothing Until Opportunity Scoring Model Is Fully Trained

**What happens:** An admin enables Pipeline Inspection for the forecast team. The Pipeline Inspection view loads the deal table correctly, but the AI Insights side panel is empty. No deal health flags, no score changes, no risk indicators appear. There is no error message — just an empty panel that looks broken.

**When it occurs:** Pipeline Inspection is enabled before Opportunity Scoring has completed its initial model training pass (which takes 24–72 hours), or Pipeline Inspection is enabled in an org where Opportunity Scoring has never been activated. The two features are independently toggled in Setup, so it is easy to enable one without the other.

**How to avoid:** Always enable and confirm Opportunity Scoring model training status (Setup > Einstein > Opportunity Scoring > status = "Active") before enabling Pipeline Inspection or presenting it to users. Make model training status part of the go-live checklist for any Einstein Sales rollout. If Pipeline Inspection is already live with an empty insights panel, do not immediately escalate to Salesforce Support — check Opportunity Scoring status first.

---

## Gotcha 5: Einstein Relationship Insights Requires EAC Email Sync History — It Is Not Instant

**What happens:** An org enables Einstein Relationship Insights and assigns the permission set to users. Reps open contact or account records and see no relationship connections displayed — the panel shows "No connections found" universally, for all contacts and accounts.

**When it occurs:** EAC email sync was enabled at the same time as Relationship Insights, or EAC has been enabled for fewer than 30 days with low email volume. The relationship graph is built by mining email correspondence patterns over time. There is no relationship data to surface until the email sync has accumulated sufficient history. Also occurs if EAC is not enabled at all — Relationship Insights cannot function without email data.

**How to avoid:** Confirm that EAC has been running and syncing emails for at least 30 days with meaningful email volume before presenting Relationship Insights to users. Set realistic expectations in training: the feature improves over time as email history grows. Do not position it as a feature that delivers value immediately on Day 1 of rollout.
