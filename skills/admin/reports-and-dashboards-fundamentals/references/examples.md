# Examples — Reports and Dashboards Fundamentals

---

## Example 1: Pipeline Dashboard for Sales Managers Using Dynamic Dashboards

**Context:** A sales operations admin needs to build a pipeline dashboard for a team of 12 sales managers. Each manager should see only their own team's opportunities — not the entire org's pipeline. The org uses a Private sharing model on Opportunities.

**Problem:** The admin initially created a static dashboard running as the VP of Sales. All 12 managers see the VP's complete pipeline view, including deals owned by managers outside their hierarchy. This is both a security issue and a usability problem — managers are confused by irrelevant data.

**Solution:**

1. Create a Summary report on Opportunities, grouped by Stage, with filters:
   - Close Date = Current FQ (relative date — never hard-code)
   - Opportunity: Forecast Category not equal to "Omitted"
2. Add summary fields: SUM(Amount) labeled "Total Pipeline" and COUNT(Id) labeled "Opportunity Count."
3. Add a Summary Formula for Average Deal Size: `Amount:SUM / RowCount`
4. Save to the Sales Operations shared folder.
5. Create a new Dashboard. Set Running User to **"Run as logged-in user"** (this makes it dynamic).
6. Add a Bar Chart component: Stage on X-axis, SUM(Amount) on Y-axis, sourced from the Summary report.
7. Add a Metric component showing total pipeline SUM(Amount).
8. Add a Table component showing open opportunities sorted by Amount descending (from a Tabular report with row limit 10).
9. Share the dashboard folder with the Sales Manager profile.

**Why it works:** Dynamic dashboards execute the source reports as the viewing user, so each manager's sharing access is applied at query time. A manager in the Western region sees only Western region records they own or can access via the role hierarchy. No data leakage occurs. The relative date filter keeps the dashboard accurate every quarter without manual updates.

**Limit to know:** Enterprise orgs support a maximum of 5 simultaneous dynamic dashboard running users. If your org needs more than 5 simultaneous personalized views, upgrade to Unlimited or consider CRM Analytics.

---

## Example 2: Custom Report Type for Account Activity Coverage

**Context:** A sales manager wants a report showing all Accounts, along with the date of their most recent activity (Task or Event), to identify accounts that have gone cold. No standard Salesforce report type covers Accounts + Activities with the fields needed.

**Problem:** The standard "Activities with Accounts" report type shows one row per activity. The manager gets hundreds of rows per account and cannot see the most recent activity date at a glance. "Accounts with Activities" does not exist as a standard type.

**Solution:**

1. Go to Setup > Report Types > New Custom Report Type.
2. Primary Object: **Accounts**
3. Click "Click to relate another object" — relate **Activities** (Tasks and Events). Set the relationship to **"'A' records may or may not have related 'B' records."** (Outer join — accounts with no activities still appear.)
4. In the Field Layout editor, add from Accounts: Account Name, Account Owner, Billing State, Industry, Annual Revenue. Add from Activities: Activity Date (Last Activity Date), Subject, Type.
5. Label: "Accounts with Activity Detail." Save and deploy.
6. Build a Summary report on this CRT:
   - Group by Account Owner
   - Filter: Account Owner = "My Team's Accounts" (if role hierarchy is set up) or Owner Role contains "Sales"
   - Add a filter: Activity Date > LAST 90 DAYS (or leave blank to see all accounts including those with no activity)
   - Sort by Activity Date ascending to surface the oldest accounts first
7. Add a Bucket Field on Activity Date: "Recent" (within 30 days), "Aging" (31–90 days), "Cold" (>90 days or blank).
8. Group by the Bucket Field to show counts per coverage tier.

**Why it works:** The outer join ("may or may not have") ensures accounts with zero activities appear in the report — they show as blank in the Activity Date column and fall into the "Cold" bucket. An inner join ("must have") would silently exclude those accounts, making coverage look better than it is.

---

## Example 3: Joined Report for Side-by-Side Quota vs. Actuals

**Context:** A sales director wants a single report showing each rep's quota (from a custom Quota object) alongside their closed-won revenue for the current quarter, side by side.

**Problem:** Quota and Opportunity Closed Won data live on different objects with no direct relationship. A standard report type cannot combine them into a single row per rep.

**Solution:**

1. Create a **Joined Report**.
2. **Block 1**: Report type = "Opportunities." Filters: Stage = Closed Won, Close Date = Current FQ. Group by Opportunity Owner. Summary field: SUM(Amount) labeled "Closed Won."
3. **Block 2**: Report type = "Quotas with Users" (a custom CRT or standard if available). Filters: Quota Period = Current FQ. Group by Quota Owner. Summary field: SUM(Quota Amount) labeled "Quota."
4. Set the common grouping field to Owner Name across both blocks (this is how joined report blocks align rows).
5. Add a Summary Formula across blocks: Attainment % = `[Opportunities]Amount:SUM / [Quotas]QuotaAmount__c:SUM`
6. Save and add to the leadership dashboard as a Table component — note that joined reports can only appear as tables in dashboards, not as charts.

**Limits to know:** Maximum 5 blocks per joined report. Maximum 2,000 rows per block. Bucket fields cannot span blocks. Joined reports are not available in dashboards as chart components — only as embedded table components, and only on some editions.

**Why it works:** The joined report treats each block as an independent data source aligned on the common grouping. Reps with quota but no closed deals still appear (block 2 contributes the row); reps with deals but no quota entry also appear (block 1 contributes). The cross-block summary formula surfaces attainment percentage without requiring a custom formula field on either object.

---

## Anti-Pattern: Hard-Coded Date Filters in Dashboard Source Reports

**What practitioners do:** Set a report filter like "Close Date equals 01/01/2025 to 03/31/2025" to capture Q1 data, then use that report as a dashboard source.

**What goes wrong:** The date range is static. On April 1 the dashboard still shows Q1 data. Stakeholders believe they are looking at current data. Quarterly business reviews are conducted on stale numbers. The admin has to manually update every report at the start of each quarter.

**Correct approach:** Use relative date ranges: "Close Date = Current FQ," "Created Date = Last 30 Days," "Activity Date = This Year." Relative ranges advance automatically. If a static snapshot is genuinely needed (e.g., historical comparison), document the intent clearly in the report description and schedule a reminder to archive and replace it each period.
