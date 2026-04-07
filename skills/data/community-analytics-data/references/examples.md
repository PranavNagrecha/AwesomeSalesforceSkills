# Examples — Community Analytics Data

## Example 1: Custom Report for Daily Active Users Per Site

**Context:** A customer success manager wants a weekly report showing how many unique community members logged in per day across two Experience Cloud sites (a customer portal and a partner portal). The Engagement Insights dashboards exist but cannot be filtered by site for comparison or scheduled for delivery.

**Problem:** Without a custom report, the only native option is the read-only Engagement Insights panel — which cannot be scheduled, exported, or segmented. Building a report without the right Custom Report Type means NetworkActivityAudit is not exposed in the report builder.

**Solution:**

```
1. Setup — Create Custom Report Type
   Object: Networks (primary)
   Related object: Network Activity Audits (child, "each Network may or may not have related Network Activity Audits")
   Label: "Community Login Activity"
   Category: Customer Support (or any relevant category)
   Fields to expose: Network Name, Member, Activity Date, Action Type, Count

2. Build the Report
   Report type: Community Login Activity (custom type above)
   Group rows by: Network Name, Activity Date
   Summary: Count of unique Member records
   Filter: Action Type = "Login"
   Date range: Rolling 30 days (adjust as needed)

3. Add to Dashboard
   Add as a line chart grouped by Network Name over Activity Date
   Schedule dashboard refresh daily

4. Optional: Add a second component filtered to Action Type = "PageView"
   to show daily page views alongside login counts
```

**Why it works:** NetworkActivityAudit captures every login and page view event per member per site. Grouping by Network Name separates the two sites. Filtering by Action Type = `Login` isolates authentication events for true active-user measurement.

---

## Example 2: GA4 Funnel Tracking for Self-Service Case Deflection

**Context:** A support operations team wants to prove that their Experience Cloud knowledge base is deflecting cases. They need to show that members who view knowledge articles are significantly less likely to create a case in the same session.

**Problem:** Salesforce native reporting on NetworkActivityAudit can show page views but cannot reconstruct session-level behavioral funnels (e.g., "user viewed article then did NOT create a case"). GA4 is the correct tool, but practitioners often either skip the GA4 integration setup or do not define the funnel correctly.

**Solution:**

```
Step 1 — Configure GA4 Integration
  In Experience Cloud site Administration:
    Go to: Administration > Advanced > Google Analytics
    Enter Measurement ID: G-XXXXXXXXXX (your GA4 property ID)
    Save > Publish the site

  Validate: Open browser DevTools on a site page, check Network tab for
  requests to google-analytics.com/g/collect — confirms gtag is firing.
  OR use GA4 DebugView (Admin > DebugView) while browsing the site.

Step 2 — Define the Deflection Funnel in GA4
  In GA4 > Explore > Funnel Exploration:
    Step 1: Event = page_view, page_location contains "/knowledge/" (article views)
    Step 2: Event = page_view, page_location contains "/create-case" (case form)

  The funnel shows: of all users who viewed a knowledge article,
  what % proceeded to the case creation page.
  Inverse (abandonment at Step 1) = deflection rate.

Step 3 — Cross-reference with Case Volume
  In Salesforce Reports: Count of cases created per week (filter: Origin = "Web")
  Compare GA4 deflection rate trend with case volume trend over same period.
  Inverse correlation (rising deflection, stable/falling cases) = deflection ROI signal.
```

**Why it works:** GA4 captures session-level behavioral sequences that NetworkActivityAudit cannot reconstruct. The Measurement ID injection by Salesforce means no custom code is needed — only site republish. Funnel exploration in GA4 Explorations surfaces the abandonment rate natively.

---

## Anti-Pattern: Using CRM Analytics for Basic Community Metrics

**What practitioners do:** When asked to "build an analytics dashboard for the community," some practitioners immediately reach for CRM Analytics (Einstein Analytics / Tableau CRM) — creating datasets, dataflows, and lenses against NetworkActivityAudit.

**What goes wrong:** CRM Analytics requires an additional license (not included in standard Experience Cloud licenses), has a steeper setup overhead (dataflow configuration, dataset sync scheduling), and is not the recommended tool for basic community engagement metrics. It also introduces a second sync layer between NetworkActivityAudit and the CRM Analytics dataset, adding another potential point of data lag.

**Correct approach:** Use the built-in Engagement Insights dashboards for executive snapshots and Custom Report Types on NetworkActivityAudit for filterable, schedulable reports. Only escalate to CRM Analytics if the requirement explicitly involves multi-object joins, predictive scoring, or SAQL-level query complexity that standard Reports cannot handle.
