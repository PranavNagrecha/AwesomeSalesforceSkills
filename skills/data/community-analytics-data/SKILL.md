---
name: community-analytics-data
description: "Use when analyzing Experience Cloud site analytics including login metrics, member engagement, page view tracking, and content performance. Triggers: Experience Cloud site analytics, community member engagement data, portal login tracking, page view reports community, GA4 Experience Cloud integration. NOT for CRM Analytics or Tableau CRM. NOT for internal Salesforce reporting on standard CRM objects."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
tags:
  - experience-cloud
  - community
  - analytics
  - engagement-insights
  - ga4
  - network-activity-audit
triggers:
  - "Experience Cloud site analytics not showing data"
  - "community member engagement data reports"
  - "portal login tracking and page views"
  - "page view reports community site"
  - "GA4 Experience Cloud integration Measurement ID"
  - "how do I track who is logging into my community"
  - "NetworkActivityAudit custom report"
inputs:
  - Experience Cloud site name and Network ID
  - Access to site Administration panel (Network Admin or System Administrator profile)
  - GA4 Measurement ID (if configuring Google Analytics integration)
  - Reporting requirements (built-in vs custom reports vs external analytics)
outputs:
  - Engagement Insights dashboard configuration guidance
  - SOQL queries against NetworkActivityAudit and NetworkUserHistoryMonthly
  - GA4 integration setup checklist
  - Custom report type recommendations for community analytics
  - Data retention and archival strategy for site activity data
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Community Analytics Data

Use this skill when a practitioner needs to understand, report on, or configure analytics for an Experience Cloud site — covering login activity, member engagement, page views, and content performance. It does not apply to CRM Analytics (Einstein Analytics), Tableau CRM, or standard internal Salesforce reporting.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the user has a licensed Experience Cloud site (Customer Community, Partner Community, or LWR-based site) and has System Administrator or delegated Network Admin access.
- The most common wrong assumption: practitioners expect real-time data. Engagement Insights dashboards have up to a 24-hour data lag and cannot be customized.
- NetworkActivityAudit records are retained on a rolling 12-month basis — data older than 12 months is permanently deleted. Plan archival if historical trend reporting beyond one year is needed.
- GA4 integration requires republishing the site after adding or changing the Measurement ID; it does not take effect on cached pages until publish.

---

## Core Concepts

### Engagement Insights: Built-In Administration Dashboards

Experience Cloud provides read-only Engagement Insights dashboards accessible from the site's Administration panel under **Administration > Insights**. These dashboards show login activity, unique logins, page views, new member growth, and top-performing pages. They are pre-built, non-customizable, and reflect data with up to 24 hours of lag. They are appropriate for quick executive snapshots but cannot be filtered by segment, time-sliced below the day level, or embedded outside the Administration panel.

### NetworkActivityAudit and NetworkUserHistoryMonthly Objects

For custom reporting, Salesforce exposes two key objects:

- **NetworkActivityAudit** — records individual page view and login events per member per site. Each row captures the Network (site), member, action type, and timestamp. Retention is a rolling 12 months; records older than 12 months are deleted by the platform with no warning.
- **NetworkUserHistoryMonthly** — aggregated monthly rollup of user activity per Network. Useful for long-term trend reporting without incurring the per-row volume of NetworkActivityAudit. Retention behavior follows standard org data limits; check your org's storage and confirm with Salesforce documentation for your edition.

Custom report types built on these objects allow standard Reports and Dashboards to surface community activity data alongside CRM records (e.g., contact, case, account).

### GA4 Integration via Measurement ID

Experience Cloud sites support Google Analytics 4 integration natively. Enter a GA4 Measurement ID (format: `G-XXXXXXXXXX`) in **Administration > Advanced > Google Analytics** for the site. Salesforce injects the `gtag.js` snippet on every page of the site automatically — no manual code change is required. This enables GA4 event tracking, funnel analysis, audience segmentation, and conversion measurement that complements Salesforce-native metrics. Important: the site must be republished after adding or updating the Measurement ID for the change to take effect on all pages.

### Content Performance via Page-Level Analytics

Page view data in NetworkActivityAudit and GA4 can be used to assess content performance — which knowledge articles, product pages, or community discussion threads drive the most engagement or deflect the most cases. GA4 provides richer behavioral metrics (bounce rate, session duration, scroll depth) while native reports confirm which authenticated members are viewing which pages.

---

## Common Patterns

### Pattern 1: Custom Report for Daily Active Users Per Site

**When to use:** When the business needs to track daily or monthly active user counts for an Experience Cloud site beyond what the read-only Engagement Insights panel shows — especially when filtering by user segment, license type, or combining with CRM data.

**How it works:**
1. Create a Custom Report Type with **Networks** as the primary object and **Network Activity Audits** as a related object.
2. Build a report using this type, grouped by **Network Name** and **Activity Date**.
3. Add a count of unique Members (distinct login records) to measure daily active users.
4. Add filters for Action = `Login` to isolate authentication events, or `Page View` for content engagement.
5. Schedule the report to run daily and deliver to a dashboard or via subscription.

**Why not the alternative:** The built-in Engagement Insights dashboards cannot be exported, scheduled, or filtered by user segment. A custom report gives scheduling, sharing, and drill-down capability.

### Pattern 2: GA4 Funnel Tracking for Self-Service Case Deflection

**When to use:** When the business wants to measure whether Experience Cloud content (knowledge articles, FAQ pages, community answers) is reducing support case volume — a common ROI metric for self-service portals.

**How it works:**
1. In GA4, define a funnel exploration starting at a known entry point (e.g., search results page or support landing page) through knowledge article views, and ending at the "Contact Support" or "Create Case" page.
2. The GA4 Measurement ID must already be configured in site Administration and the site republished.
3. Cross-reference GA4 funnel drop-off rate (users who viewed an article but did not reach the case creation page) with case volume from standard Salesforce Case reports.
4. High funnel abandonment before the case page, combined with stable or declining case volume, indicates successful deflection.

**Why not the alternative:** NetworkActivityAudit does not capture session-level behavioral flow or conversion events. GA4 is the appropriate tool for multi-step funnel and conversion analysis.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Quick executive dashboard — logins, page views, member growth | Engagement Insights (Administration > Insights) | Read-only, zero setup, sufficient for snapshots |
| Filtered or scheduled active-user reporting against CRM data | Custom report on NetworkActivityAudit via Custom Report Type | Flexible, combinable with Contact/Account/Case data |
| Session behavior, funnel analysis, bounce rate, conversion tracking | GA4 integration (Measurement ID in site settings) | GA4 captures behavioral session data Salesforce does not natively expose |
| Long-term (>12 months) trend reporting on user activity | NetworkUserHistoryMonthly + archival strategy | NetworkActivityAudit is purged at 12 months; monthly aggregates extend the usable window |
| Deep segmentation analytics, machine learning on engagement data | Export to external data warehouse (e.g., via Data Export or Salesforce Connect) | Platform-native tools lack ML/segmentation capabilities at this depth |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner configuring or reporting on Experience Cloud analytics:

1. **Clarify requirements** — Determine whether the request is for built-in snapshots (Engagement Insights), custom Salesforce reports (NetworkActivityAudit/NetworkUserHistoryMonthly), external analytics (GA4), or a combination. Confirm data retention requirements: if historical data beyond 12 months is needed, plan archival before NetworkActivityAudit records age out.
2. **Check existing site configuration** — Verify the Experience Cloud site is active and the user has Administration panel access. For GA4, confirm whether a Measurement ID is already configured under **Administration > Advanced > Google Analytics**.
3. **Configure native analytics access** — For Engagement Insights, navigate to **Administration > Insights** and verify the dashboards are populating (allow up to 24 hours for initial data). For custom reports, build a Custom Report Type on Networks + Network Activity Audits (or Network User History Monthly for aggregates).
4. **Configure GA4 integration if required** — Enter the GA4 Measurement ID (`G-XXXXXXXXXX`) in **Administration > Advanced > Google Analytics**, then republish the site. Validate that `gtag.js` is firing on site pages using browser developer tools or the GA4 DebugView.
5. **Validate and document data coverage** — Confirm which metrics are covered by each surface. Document the 12-month retention limit for NetworkActivityAudit in the project's data governance notes and set a reminder or automated export if historical data must be preserved.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Engagement Insights dashboards are accessible and showing data (or documented as intentionally unused)
- [ ] Custom report types reference the correct object relationships (Network > NetworkActivityAudit or NetworkUserHistoryMonthly)
- [ ] GA4 Measurement ID is entered and site has been republished if GA4 integration is in scope
- [ ] Data retention limit (rolling 12 months for NetworkActivityAudit) is documented in project notes
- [ ] 24-hour data lag in Engagement Insights is communicated to stakeholders expecting real-time data
- [ ] No custom report or dashboard is being positioned as a substitute for CRM Analytics unless explicitly out of scope

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **NetworkActivityAudit rolling 12-month retention** — Salesforce automatically deletes NetworkActivityAudit records older than 12 months with no notification. Organizations that delay building reporting infrastructure risk permanently losing historical engagement data. Export to an external system or use NetworkUserHistoryMonthly for longer retention before the window closes.
2. **Engagement Insights 24-hour data lag** — Data in the built-in Engagement Insights dashboards (Administration > Insights) can be up to 24 hours behind real-time. Practitioners who build stakeholder dashboards on Engagement Insights without disclosing this lag will face credibility issues when the data does not match same-day expectations.
3. **GA4 Measurement ID requires site republish** — Adding or changing the GA4 Measurement ID in site Administration does not take effect until the site is republished. Cached pages continue to use the old (or no) tracking snippet until publish. Validate tracking with GA4 DebugView after every Measurement ID change.
4. **Built-in dashboards are read-only and non-embeddable** — Engagement Insights dashboards cannot be customized, filtered, cloned, exported, or embedded in Lightning pages or external portals. Practitioners who promise stakeholders a customized engagement dashboard must use Custom Report Types and standard Reports/Dashboards instead.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Engagement Insights configuration notes | Documented state of built-in dashboards and any known data lag for stakeholder communication |
| Custom report type setup | Report type on Networks + NetworkActivityAudit or NetworkUserHistoryMonthly with recommended groupings and filters |
| GA4 integration checklist | Measurement ID entry, publish confirmation, and DebugView validation steps |
| Data retention and archival plan | Documents the 12-month NetworkActivityAudit window and export or archival cadence if historical data is required |

---

## Related Skills

- admin/einstein-analytics-basics — Use when the requirement is for CRM Analytics (Einstein Analytics / Tableau CRM) rather than native Experience Cloud site analytics
- data/report-performance-tuning (if present) — Use when custom reports on NetworkActivityAudit are hitting query limits due to high row volume
