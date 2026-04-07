# LLM Anti-Patterns — Community Analytics Data

Common mistakes AI coding assistants make when generating or advising on Experience Cloud community analytics. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending CRM Analytics for Basic Community Engagement Metrics

**What the LLM generates:** Instructions to create a CRM Analytics (Einstein Analytics / Tableau CRM) dataset from NetworkActivityAudit, build a dataflow, and create a lens to track login counts and page views — treating CRM Analytics as the default analytics tool for all Salesforce analytics needs.

**Why it happens:** LLMs conflate "Salesforce analytics" with "CRM Analytics" because CRM Analytics is a prominent Salesforce analytics brand. Training data contains many CRM Analytics tutorials and the LLM generalizes without checking whether the license or complexity is warranted.

**Correct pattern:**

```
For basic community engagement metrics (login counts, page views, member growth):
  - Built-in Engagement Insights dashboards in Administration > Insights — zero setup
  - Custom Report Type on NetworkActivityAudit — one-time setup, full flexibility

CRM Analytics is only appropriate when:
  - Multi-object joins beyond standard report capability are required
  - Predictive scoring or machine learning on engagement data is needed
  - SAQL-level query complexity cannot be expressed in standard SOQL reports
```

**Detection hint:** If the response mentions "dataflow", "dataset sync", "SAQL", or "CRM Analytics" in the context of basic community login/page view reporting, this anti-pattern is likely present.

---

## Anti-Pattern 2: Expecting Real-Time Data from Engagement Insights

**What the LLM generates:** Instructions to monitor live site activity using the Engagement Insights dashboards, or promises that today's login surge from a campaign will be visible in the Administration panel immediately.

**Why it happens:** LLMs trained on general analytics documentation default to assuming analytics dashboards show near-real-time or same-session data. The 24-hour lag in Engagement Insights is a platform-specific limitation that is not prominent in general Salesforce docs.

**Correct pattern:**

```
Engagement Insights dashboards update with up to 24-hour lag.
Data from today will typically not appear until the following day.

For near-real-time activity:
  - Query NetworkActivityAudit directly via a Salesforce Report (live data)
  - Use SOQL in Developer Console or Workbench for immediate row-level data
  - Use GA4 real-time reports if GA4 integration is configured
```

**Detection hint:** If the response says "you can see today's logins in the Insights panel" or implies same-day data availability without caveating the 24-hour lag, this anti-pattern is present.

---

## Anti-Pattern 3: Missing the 12-Month Retention Limit on NetworkActivityAudit

**What the LLM generates:** A custom report setup guide or SOQL query plan for NetworkActivityAudit with no mention of the 12-month rolling deletion policy — implying historical data is available indefinitely.

**Why it happens:** LLMs are not reliably aware of platform-specific data retention policies. NetworkActivityAudit's 12-month rolling deletion is documented in Salesforce Help but not in prominently indexed developer guides. The LLM defaults to treating sObject data as permanent unless the user asks about retention.

**Correct pattern:**

```
NetworkActivityAudit records are retained for a rolling 12-month window only.
Records older than 12 months are automatically and permanently deleted.

Always address retention in analytics design:
  1. If historical data beyond 12 months is needed: implement recurring export
     to external storage (e.g., data warehouse, S3) before records age out.
  2. For long-term aggregates: use NetworkUserHistoryMonthly — monthly rollups
     that avoid the row-level deletion risk.
  3. Document the 12-month window in project data governance notes.
```

**Detection hint:** Any analytics design guide for NetworkActivityAudit that does not mention "12 months", "rolling retention", or "data retention" should be flagged for review.

---

## Anti-Pattern 4: Not Combining GA4 and Native Analytics

**What the LLM generates:** An analytics plan that uses only GA4 for Experience Cloud (ignoring NetworkActivityAudit) or only NetworkActivityAudit (ignoring GA4) — treating them as alternatives rather than complements.

**Why it happens:** LLMs often frame analytics tool selection as a binary choice ("use X or Y"). The complementary nature of GA4 (session behavior, funnel, conversion) and Salesforce native analytics (authenticated member identity, CRM attribute joins) is a nuance not well represented in most training data.

**Correct pattern:**

```
GA4 and Salesforce native analytics are complementary, not competing:

  Salesforce native (NetworkActivityAudit + custom reports):
    - Confirms who: authenticated member identity, license type, contact/account
    - Enables CRM joins (e.g., "members with open cases who viewed the FAQ")

  GA4:
    - Confirms behavioral flow: funnel progression, scroll depth, session duration
    - Enables conversion analysis: case deflection rate, self-service success funnels

Recommended: run both surfaces and cross-reference for a complete picture.
```

**Detection hint:** If the response presents "should we use GA4 or Salesforce reports?" as a mutually exclusive choice, or implements only one surface without explaining what the other would add, this anti-pattern is present.

---

## Anti-Pattern 5: Forgetting to Republish the Site After GA4 Configuration Changes

**What the LLM generates:** Instructions to enter the GA4 Measurement ID in Administration settings and then immediately validate GA4 events — skipping the site republish step, leading the practitioner to conclude GA4 integration is broken when it is simply not yet live.

**Why it happens:** LLMs trained on general web analytics integration patterns expect configuration changes to take effect immediately. The Experience Cloud requirement to republish before configuration changes are applied to live pages is a platform-specific step not found in standard GA4 integration documentation.

**Correct pattern:**

```
After adding or changing the GA4 Measurement ID in Administration > Advanced:

  1. Click Publish (or Publish > Publish Now) to republish the site.
  2. Wait for publish to complete (typically 1-5 minutes).
  3. Open a site page in a browser and validate with DevTools:
     - Network tab: filter for google-analytics.com — should see collect requests
     - OR: use GA4 DebugView (Admin > DebugView in GA4) while browsing the site
  4. Do NOT validate before republish — the old configuration is still active.

Without republish, the Measurement ID change has no effect on live pages.
```

**Detection hint:** If GA4 setup instructions do not include an explicit "republish the site" step between entering the Measurement ID and validating tracking, this anti-pattern is likely present.

---

## Anti-Pattern 6: Conflating Experience Cloud Analytics with Internal Salesforce Reporting

**What the LLM generates:** Guidance that blends standard CRM reporting (e.g., Case reports, Opportunity reports, Account activity) with Experience Cloud site analytics, treating them as the same surface or suggesting that standard reports automatically include community engagement data.

**Why it happens:** Both surfaces exist within the same Salesforce org and use the same Reports and Dashboards interface. LLMs frequently blur the boundary between internal CRM data reporting and Experience Cloud member activity reporting because the tooling looks the same.

**Correct pattern:**

```
Experience Cloud analytics (this skill) covers:
  - NetworkActivityAudit: site page views and login events per community member
  - NetworkUserHistoryMonthly: aggregated monthly site activity
  - Engagement Insights: built-in admin-panel dashboards for site metrics
  - GA4: session-level behavioral analytics on the Experience Cloud site

Internal Salesforce reporting covers:
  - Case, Opportunity, Contact, Account, and other CRM objects
  - Service Cloud metrics: case resolution time, CSAT, first-contact resolution

These can be JOINED in custom reports (e.g., NetworkActivityAudit joined to Contact)
but they are distinct data surfaces with different ownership, retention, and tooling.
```

**Detection hint:** If a response about "community analytics" starts discussing CSAT scores, case resolution SLAs, or Opportunity pipeline without explicitly framing these as CRM data joined to community data, the scope boundary is blurred.
