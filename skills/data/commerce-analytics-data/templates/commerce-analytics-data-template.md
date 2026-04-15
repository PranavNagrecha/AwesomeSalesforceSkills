# Commerce Analytics Data — Work Template

Use this template when working on a commerce analytics task. Fill in each section before starting work.

## Scope

**Skill:** `commerce-analytics-data`

**Request summary:** (fill in what the user asked for)

---

## Platform Identification

Which Commerce platform is in use?

- [ ] **B2C Commerce (SFCC / Salesforce Commerce Cloud)** — storefront data in Business Manager
- [ ] **B2B Commerce on Core** — storefront data in Salesforce CRM objects (WebCart, CartItem, etc.)
- [ ] Unknown — confirm with user before proceeding

---

## Context Gathered

Answer these before starting:

- **Commerce platform confirmed:** ___________
- **Business unit / site ID (B2C) or WebStore name (B2B):** ___________
- **Date range for analysis:** ___________
- **Specific metric(s) needed:**
  - [ ] Conversion rate / funnel
  - [ ] Cart abandonment rate
  - [ ] Product performance (units, revenue, view-to-purchase)
  - [ ] Revenue / GMV / AOV
  - [ ] Other: ___________
- **Expected row count in export:** ___________  (if >1,000 and B2C, plan for SFTP feed)
- **CRM Analytics licensed? (relevant only for B2B):** [ ] Yes [ ] No [ ] Unknown

---

## Routing Decision

Based on the platform and license check:

| Condition | Action |
|---|---|
| B2C Commerce | Go to Business Manager > Reports & Dashboards |
| B2C Commerce, export >1,000 rows | Configure SFTP Data Feed |
| B2B Commerce, CRM Analytics licensed | Use bi_template_b2bcommerce in CRM Analytics |
| B2B Commerce, no CRM Analytics | Write SOQL against WebCart / CartItem |

**Selected approach:** ___________

---

## Metric Definitions (agree before querying)

| Metric | Numerator | Denominator | Time Window | Agreed With |
|---|---|---|---|---|
| Conversion rate | Orders placed | Sessions (or visits) | ___ days | ___ |
| Cart abandonment rate | Active carts > threshold | All carts created in window | ___ days | ___ |
| Average order value (AOV) | Total revenue | Order count | ___ days | ___ |

---

## Business Manager Navigation (B2C only)

- [ ] Logged into Business Manager at `https://<instance>.demandware.net`
- [ ] Selected the correct Site (business unit): ___________
- [ ] Navigated to: Merchant Tools > Reports & Dashboards
- [ ] Dashboard selected: ___________
- [ ] Date range set to: ___________
- [ ] Export method: [ ] CSV (≤1,000 rows) [ ] SFTP Feed (>1,000 rows)

---

## SOQL Query (B2B only)

Paste the agreed SOQL below. Confirm:
- [ ] `Status = 'Active'` used for abandoned cart filter (not 'Open' or 'Pending')
- [ ] Date threshold confirmed: `LAST_N_DAYS:<N>` where N = ___
- [ ] `PendingDelete` exclusion decision documented: [ ] Excluded [ ] Included
- [ ] Tested in Developer Console or VS Code Salesforce Extension

```soql
-- Paste final SOQL here
```

---

## Checklist

- [ ] Commerce platform confirmed (B2C vs B2B) before any query or navigation
- [ ] Legacy Business Manager Analytics NOT referenced (retired January 2021)
- [ ] CSV export row count checked — SFTP feed path planned if >1,000 rows
- [ ] SOQL Status values verified against WebCart picklist (not assumed)
- [ ] Metric definitions documented and agreed with stakeholder
- [ ] Data freshness expectations communicated (Business Manager: 15–60 min lag)

---

## Notes

Record any deviations from the standard pattern and why.
