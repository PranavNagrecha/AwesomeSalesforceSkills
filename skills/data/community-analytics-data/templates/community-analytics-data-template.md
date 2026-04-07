# Community Analytics Data — Analytics Setup Checklist

Use this template when setting up or reviewing analytics for an Experience Cloud site.

## Scope

**Skill:** `community-analytics-data`

**Site name:** (fill in the Experience Cloud site name)

**Request summary:** (fill in what the stakeholder asked for)

---

## Context Gathered

Answer these before configuring anything:

- **Site type:** Customer Community / Partner Community / LWR site / other
- **Admin access confirmed:** Yes / No (System Administrator or Network Admin required)
- **Historical data requirement:** Need data beyond 12 months? Yes / No
  - If Yes: NetworkActivityAudit archival strategy must be in place NOW
- **Stakeholder expectations:** Real-time data expected? Yes / No
  - If Yes: communicate 24-hour Engagement Insights lag; direct to live SOQL/Report queries
- **External analytics in scope:** GA4 integration required? Yes / No
  - If Yes: GA4 Measurement ID available? _______________

---

## Surface Selection

Mark each analytics surface as In Scope / Out of Scope / Already Configured:

| Surface | Status | Notes |
|---|---|---|
| Engagement Insights (built-in dashboards) | | |
| Custom reports on NetworkActivityAudit | | |
| Custom reports on NetworkUserHistoryMonthly | | |
| GA4 integration (Measurement ID) | | |
| External data export / archival | | |

---

## Setup Checklist

### Engagement Insights

- [ ] Navigate to Administration > Insights and confirm dashboards are populating
- [ ] Communicate 24-hour data lag to stakeholders
- [ ] Document that built-in dashboards cannot be customized, exported, or embedded

### Custom Reports (NetworkActivityAudit)

- [ ] Create Custom Report Type: Networks (primary) + Network Activity Audits (child)
- [ ] Build report grouped by Network Name + Activity Date
- [ ] Add filter for Action Type (Login vs. Page View as needed)
- [ ] Schedule report delivery if recurring reporting is required
- [ ] Confirm report folder permissions are restricted to appropriate users

### Custom Reports (NetworkUserHistoryMonthly)

- [ ] Create Custom Report Type: Networks (primary) + Network User History Monthly (child)
- [ ] Build monthly trend report grouped by Network Name + Month
- [ ] Use as the long-term trend archive (avoids 12-month deletion risk on row-level data)

### GA4 Integration

- [ ] Enter Measurement ID (G-XXXXXXXXXX) in Administration > Advanced > Google Analytics
- [ ] Publish the site (required — changes do not take effect until republish)
- [ ] Validate gtag.js is firing on live pages (DevTools Network tab or GA4 DebugView)
- [ ] Define GA4 funnel or conversion events relevant to business goals (e.g., case deflection)

### Data Retention and Governance

- [ ] Document 12-month NetworkActivityAudit rolling deletion in project governance notes
- [ ] If historical data >12 months is needed: schedule recurring export before records age out
- [ ] Confirm no member-level behavioral data is exposed to unauthorized report viewers

---

## Approach

Which patterns from SKILL.md apply?

- [ ] Built-in Engagement Insights for executive snapshot (zero-setup, read-only)
- [ ] Custom report on NetworkActivityAudit for filtered/scheduled active-user reporting
- [ ] GA4 funnel analysis for self-service case deflection measurement
- [ ] NetworkUserHistoryMonthly for long-term aggregate trends

---

## Stakeholder Communication Notes

Document any expectations that need to be reset:

- Data lag: Engagement Insights shows data up to 24 hours behind real-time.
- Retention: NetworkActivityAudit records are deleted after 12 months — no recovery.
- Customization: Engagement Insights dashboards cannot be customized or embedded.
- Republish: GA4 Measurement ID changes require site republish to take effect.

---

## Notes

Record any deviations from the standard pattern and why:
