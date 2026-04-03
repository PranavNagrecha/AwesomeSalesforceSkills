# Dashboard Design Template

Complete this before building a dashboard. It forces stakeholder alignment on what the dashboard is for, who it's for, and how the data is secured.

---

## Dashboard Overview

| Property | Value |
|----------|-------|
| **Dashboard Name** | TODO: e.g. "Sales Pipeline — Manager View" |
| **Dashboard API Name** | TODO: e.g. `Sales_Pipeline_Manager_View` |
| **Audience** | TODO: e.g. Sales Managers, VP of Sales |
| **Business question answered** | TODO: One sentence. e.g. "What is the current state of our pipeline by stage and rep?" |
| **Refresh frequency** | TODO: Daily / Weekly / Manual |
| **Author / Owner** | TODO |
| **Created Date** | TODO: YYYY-MM-DD |
| **Review cadence** | TODO: e.g. Quarterly |
| **Folder** | TODO: e.g. Sales Leadership Reports |

---

## Running User Configuration

| Option | Selected | Justification |
|--------|:--------:|--------------|
| Run as logged-in user (recommended) | ☐ | Each viewer sees their own data per sharing model |
| Run as specified user | ☐ | All viewers see same data as: [User Name/Role] |
| Run as logged-in user, with field visibility | ☐ | Recommended when sensitive fields involved |

**If "Run as specified user":**
- Specified user: TODO
- That user's data access level: TODO (View All? Role hierarchy? Specific sharing rules?)
- Confirmed that viewers should see this user's full data: ☐ Yes / ☐ No

**Security sign-off for "Run as specified user" dashboards:** TODO: Name/Date

---

## Dashboard Filters

| Filter Name | Field | Applies to Components | Default Value |
|-------------|-------|----------------------|--------------|
| TODO: e.g. Close Date | Opportunity.CloseDate | TODO: All / Specific: | TODO: This Quarter |
| TODO | TODO | TODO | TODO |

---

## Component Design

One row per dashboard component. Aim for 4-6 components maximum per dashboard — more creates noise.

### Component 1

| Property | Value |
|----------|-------|
| **Component Name** | TODO: e.g. "Pipeline by Stage" |
| **Underlying Report** | TODO: Report name + folder |
| **Chart Type** | TODO: Funnel / Bar / Column / Donut / Table / Gauge / Metric |
| **Metric Displayed** | TODO: e.g. Sum of Amount, grouped by Stage |
| **Why it matters** | TODO: What decision does this chart enable? |
| **Drill-through** | ☐ Yes — links to: TODO / ☐ No |

### Component 2

| Property | Value |
|----------|-------|
| **Component Name** | TODO |
| **Underlying Report** | TODO |
| **Chart Type** | TODO |
| **Metric Displayed** | TODO |
| **Why it matters** | TODO |
| **Drill-through** | ☐ Yes — links to: TODO / ☐ No |

### Component 3

| Property | Value |
|----------|-------|
| **Component Name** | TODO |
| **Underlying Report** | TODO |
| **Chart Type** | TODO |
| **Metric Displayed** | TODO |
| **Why it matters** | TODO |
| **Drill-through** | ☐ Yes — links to: TODO / ☐ No |

### Component 4 (add more as needed)

| Property | Value |
|----------|-------|
| **Component Name** | TODO |
| **Underlying Report** | TODO |
| **Chart Type** | TODO |
| **Metric Displayed** | TODO |
| **Why it matters** | TODO |
| **Drill-through** | ☐ Yes — links to: TODO / ☐ No |

---

## Sharing Settings

| Audience | Access Level | Folder |
|----------|-------------|--------|
| TODO: e.g. Sales Managers | View | TODO: Sales Leadership Reports |
| TODO: e.g. VP of Sales | Edit | TODO |

**Private folder risk check:** ☐ Confirmed dashboard is NOT in a private folder

---

## Subscriptions (if applicable)

| Recipient | Frequency | Day/Time | Report Sent | Security Review Done? |
|-----------|-----------|----------|-------------|----------------------|
| TODO: e.g. VP of Sales | Weekly | Monday 8am | Full dashboard | ☐ Yes |
| TODO | TODO | TODO | TODO | ☐ Yes |

**Subscription security check:** Do all recipients have appropriate access to see ALL rows in the report?
- ☐ Yes — recipients have equivalent or broader access than the report owner
- ☐ No — ⚠️ Review needed before enabling subscription

---

## Testing Checklist

| Test | Result |
|------|--------|
| Each component displays data when expected | ☐ Pass |
| Dashboard filter changes update all applicable components | ☐ Pass |
| Running as a lower-access user shows appropriate data (not over-sharing) | ☐ Pass |
| Drill-through links work and land on correct report/record | ☐ Pass |
| Refresh loads within 10 seconds | ☐ Pass |
| Mobile view is readable (if mobile audience) | ☐ Pass / ☐ N/A |

---

## Approval

| Role | Name | Approved | Date |
|------|------|----------|------|
| Salesforce Admin | TODO | ☐ | |
| Business Owner / Dashboard Audience Rep | TODO | ☐ | |
| Security review (if "Run as specified user") | TODO | ☐ | |
