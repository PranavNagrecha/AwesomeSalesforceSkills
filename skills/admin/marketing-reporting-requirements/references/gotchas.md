# Gotchas — Marketing Reporting Requirements

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Campaign Influence Associations Are Not Retroactive When Lookback Window Changes

**What happens:** When the Campaign Influence lookback window is changed in Setup (for example, from the 30-day default to 120 days to match a longer sales cycle), the new window applies only to Opportunities created after the change. Existing Opportunity-to-Campaign associations that were created under the old 30-day window are not recalculated. Historical attribution data remains based on the old window, producing a permanent inconsistency between pre- and post-change periods.

**When it occurs:** Any time the lookback window is changed after Campaign Influence has been live and recording associations. Also occurs when Customizable Campaign Influence is enabled on an org that previously used standard Campaign Influence — CCI associations start fresh from the enablement date.

**How to avoid:** Set the lookback window to match the business's actual sales cycle length before enabling Campaign Influence in production. Document the window value in the requirements decision record. If the window must change in a live org, document the change date as a data lineage break and exclude pre-change data from trend comparisons.

---

## Gotcha 2: The Campaign Performance Report's "Value Won" Is Not the Same as Attribution Revenue

**What happens:** The native Campaign Performance Report shows "Value Won" as the sum of Amount on Won Opportunities where that campaign is the Primary Campaign Source. This is a first-touch, single-campaign metric. Stakeholders frequently misread "Value Won" as "revenue influenced by this campaign" and derive inflated ROI figures or misattribute credit. When Customizable Campaign Influence is enabled, influenced revenue appears on the CampaignInfluence object — not in the Campaign Performance Report — and the two numbers will not match.

**When it occurs:** Any time both the Campaign Performance Report and CCI-backed reports are used simultaneously, which is the standard configuration once CCI is enabled. The discrepancy is invisible unless someone explicitly compares the two report types.

**How to avoid:** In requirements, define "Value Won" and "Influenced Revenue" as separate KPIs with separate definitions. Document which report type backs each metric. Never use both metrics in the same executive dashboard without clearly labeling which attribution model each represents.

---

## Gotcha 3: Even Distribution Credit Does Not Sum to 100% Across Campaigns Per Opportunity

**What happens:** When Customizable Campaign Influence is configured with an Even Distribution model, Salesforce creates one CampaignInfluence record per campaign-opportunity pair and assigns each a percentage. However, the percentages are calculated at the time of association and do not automatically rebalance if a new campaign is associated later. If a fourth campaign is associated after the initial three received 33.3% each, the total exceeds 100% until the model is recalculated. This causes "Revenue Influenced" sums to overcount when campaign counts change over the sales cycle.

**When it occurs:** Long sales cycles where prospects interact with additional campaigns after the initial Campaign Influence association is created. The system does not retroactively redistribute percentages when new associations are added.

**How to avoid:** During requirements, specify whether the attribution model should recalculate on each new campaign association or lock at opportunity creation. Document this as a data governance rule. If recalculation is required, note that MCAE B2B Marketing Analytics Plus handles this automatically in its Einstein Analytics pipeline, whereas native CCI does not.

---

## Gotcha 4: Primary Campaign Source Is Overwritten on Each Opportunity Save

**What happens:** The Primary Campaign Source field on Opportunity is auto-populated by Salesforce when an Opportunity is created, based on the most recent Campaign Membership on a related Contact. However, if a sales rep manually changes the Primary Campaign Source field at any point, the automatic population logic does not restore it. Subsequent changes to Campaign Memberships do not update the field unless triggered by a custom workflow. Marketing teams relying on Primary Campaign Source for first-touch reporting silently lose accuracy when sales reps override the field.

**When it occurs:** In any org where sales reps have edit access to the Primary Campaign Source field on Opportunity. Common in orgs that also use the field for sales-initiated campaign associations.

**How to avoid:** In requirements, confirm whether Primary Campaign Source should be locked (field-level security to read-only for non-admins) or freely editable. If locked, document the governance rule. If freely editable, flag to stakeholders that first-touch attribution data may be manually overridden and metrics should be interpreted accordingly.

---

## Gotcha 5: B2B Marketing Analytics Plus Datasets Refresh on a Schedule, Not in Real Time

**What happens:** MCAE B2B Marketing Analytics Plus powers multi-touch attribution and engagement trend dashboards via Einstein Analytics (CRM Analytics). The datasets that back these dashboards are refreshed on a schedule (daily by default), not in real time. Marketers who launch a campaign in the morning and expect to see engagement metrics in the analytics dashboard within hours will see stale data until the next scheduled refresh. This is materially different from native Salesforce Campaign Member reports, which reflect data as soon as it is synced from MCAE.

**When it occurs:** Any org using B2B Marketing Analytics Plus for attribution or engagement reporting. The refresh lag is most visible immediately after campaign launches and during live events.

**How to avoid:** In requirements, document the data freshness SLA for each KPI. Native Campaign Member status reports can be flagged as near-real-time (subject to MCAE sync frequency, typically 10–15 minutes). B2B Marketing Analytics Plus dashboards should be documented as "as of previous day's refresh." Stakeholders who require same-day engagement data should use native Campaign Member reports rather than the analytics dashboards.
