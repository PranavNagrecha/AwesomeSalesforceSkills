# Gotchas — Community Analytics Data

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: NetworkActivityAudit Rolling 12-Month Retention — Historical Data Is Permanently Lost

**What happens:** Salesforce automatically deletes NetworkActivityAudit records that are older than 12 months. There is no recycle bin, no archive, and no warning before deletion. Once records are purged, they cannot be recovered.

**When it occurs:** Any org with an Experience Cloud site that has not implemented an export or archival strategy. Organizations that delay reporting buildout by 12 months or more will find their earliest engagement data is already gone when they finally attempt historical trend analysis.

**How to avoid:** Identify the data retention requirement early. If historical data beyond 12 months is needed, implement a recurring Salesforce Data Export or Apex-based export job that writes NetworkActivityAudit records to an external data store (data warehouse, S3, etc.) before they age out. For organizations that only need year-over-year aggregates, NetworkUserHistoryMonthly provides monthly rollups with no published rolling-deletion window — verify current retention limits in the Object Reference for your edition.

---

## Gotcha 2: Engagement Insights Dashboards Have Up to 24-Hour Data Lag

**What happens:** The built-in Engagement Insights dashboards in Administration > Insights show data that can be up to 24 hours behind real-time activity. Login events and page views that occurred today may not appear until the following day.

**When it occurs:** Any time a stakeholder or business user expects to see same-day activity — for example, after a major product launch or marketing campaign sends a surge of traffic to the community. The dashboard will not reflect the surge until the next day's refresh.

**How to avoid:** Communicate the 24-hour lag explicitly to stakeholders before delivery. Do not position Engagement Insights as a real-time monitoring tool. If near-real-time data is needed, query NetworkActivityAudit directly via a scheduled Salesforce Report (which reads live data) or via SOQL in a developer tool — these do not have the same artificial lag.

---

## Gotcha 3: GA4 Measurement ID Change Requires Site Republish

**What happens:** When a GA4 Measurement ID is added, updated, or removed in site Administration, the change is not applied to the live site until the site is explicitly republished. Cached pages continue to use the previous tracking configuration (or no tracking at all). This means GA4 may appear to be working in the Administration panel but no events are actually being collected on the live site.

**When it occurs:** Any time a Measurement ID is entered or changed — including during initial setup, when migrating from one GA4 property to another, or when correcting a typo in the Measurement ID.

**How to avoid:** After every GA4 configuration change, republish the site immediately. Validate that `gtag.js` is firing on live pages using browser developer tools (Network tab, filter for `google-analytics.com`) or GA4 DebugView (requires the GA4 DebugView Chrome extension or `?gtag_debug=1` URL parameter on the site). Do not assume the change is live until validated.

---

## Gotcha 4: Built-In Dashboards Are Read-Only and Cannot Be Embedded or Exported

**What happens:** Engagement Insights dashboards cannot be cloned, customized, filtered by user segment, exported to CSV/PDF, embedded in Lightning pages, or shared outside the Administration panel. Administrators who promise stakeholders a customized or embedded engagement dashboard based on Engagement Insights will find these capabilities do not exist.

**When it occurs:** During requirements gathering when stakeholders ask for "the community dashboard embedded in our executive Lightning page" or "a filtered view showing only partner users." Practitioners who demo Engagement Insights and then promise customization are setting incorrect expectations.

**How to avoid:** Be explicit during discovery: Engagement Insights is read-only and Administration-panel-only. Any custom filtering, scheduling, embedding, or export must be built using standard Salesforce Reports and Dashboards on top of NetworkActivityAudit via a Custom Report Type.
