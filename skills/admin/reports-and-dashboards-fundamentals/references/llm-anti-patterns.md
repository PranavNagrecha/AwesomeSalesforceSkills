# LLM Anti-Patterns — Reports and Dashboards Fundamentals

Common mistakes AI assistants make when generating or advising on Salesforce Reports and Dashboards. These patterns help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Recommending a Joined Report for Any Multi-Object Reporting Need

**What the LLM generates:** "Since you need data from both Accounts and Opportunities, create a Joined Report with one block for Accounts and one block for Opportunities."

**Why it happens:** LLMs pattern-match "two objects" to "joined report" because the name suggests combining data. In practice, joined reports are rarely the right answer and have significant limits (5-block maximum, 2,000 rows per block, no cross-block bucket fields, no chart dashboard components).

**Correct pattern:**

```
For most multi-object reporting needs:
1. Use a standard report type that already covers the object pair
   (e.g., "Opportunities with Account Fields" is standard)
2. If no standard type works, create a Custom Report Type with the
   correct primary object and related objects
3. Only use a Joined Report when data from genuinely unrelated
   report types must appear side by side in the same view
   (e.g., Quota vs Closed Won from separate data sources)
```

**Detection hint:** Watch for "joined report" appearing in responses where the ask is simply "show fields from two related objects." Related objects on a CRT are not a joined report.

---

## Anti-Pattern 2: Suggesting Hard-Coded Date Filters

**What the LLM generates:** "Add a filter: Close Date >= 2025-01-01 AND Close Date <= 2025-03-31 to show this quarter's data."

**Why it happens:** LLMs default to explicit date ranges because they are unambiguous. Absolute dates look precise and complete. The problem is they become stale the moment the period ends, with no error — the report just shows the wrong period silently.

**Correct pattern:**

```
Always use relative date ranges in report filters:
- "Current FQ" for the current fiscal quarter
- "This Year" for the calendar year
- "Last 30 Days" for rolling windows
- "Last N Days" with a specific number for custom windows

Only use absolute dates when a historical snapshot is intentional,
and document it explicitly in the report description.
```

**Detection hint:** Any filter containing a four-digit year (e.g., 2025) or a specific month-day combination is almost certainly wrong for ongoing reports.

---

## Anti-Pattern 3: Conflating Dashboard Running User with Record Ownership

**What the LLM generates:** "To make the dashboard show only the manager's deals, set the running user to the manager."

**Why it happens:** LLMs map "show X's data" to "run as X," which sounds logical. But running a dashboard as a specific user shows ALL data that user can see — their entire sharing access — not just records they own. A manager who can see their whole team's data will make that entire team's data visible to all dashboard viewers, including junior reps who should only see their own records.

**Correct pattern:**

```
"Run as logged-in user" (dynamic dashboard) = each viewer sees
exactly what their own sharing access permits — the only secure
option for multi-audience dashboards.

"Run as specified user" = all viewers see the specified user's
complete data access — use only when all viewers are explicitly
permitted to see that user's full data slice.

The running user is not an ownership filter. It is a sharing
access proxy. Choose dynamic dashboards for personalized views.
```

**Detection hint:** Any suggestion to "set the running user to [a named user]" for personalized data delivery should be flagged as a potential security issue.

---

## Anti-Pattern 4: Treating the 2,000-Row UI Limit as the Complete Dataset

**What the LLM generates:** "The report returned 2,000 records, so your dataset has 2,000 accounts matching the criteria."

**Why it happens:** The report builder UI shows up to 2,000 rows. LLMs reading or reasoning about report output often treat the displayed row count as the complete result. The actual underlying dataset may be much larger.

**Correct pattern:**

```
The 2,000-row limit is a display constraint, not a query limit.
To retrieve the full dataset:
- Export the report to CSV (no row limit on export)
- Use the Analytics REST API: GET /analytics/reports/{reportId}
  with includeDetails=true
- Use Apex Reports.ReportManager.runReport() for programmatic access
- The row count shown in the report header reflects the true total;
  the grid truncates at 2,000

Always note: if a report shows exactly 2,000 rows, assume there
may be more records and export to verify.
```

**Detection hint:** Any response that uses "the report shows 2,000 records" as a definitive count without mentioning the export or the display limit is suspect.

---

## Anti-Pattern 5: Recommending a New Custom Report Type Before Exhausting Standard Options

**What the LLM generates:** "To get Account Name, Contact Email, and Opportunity Amount in one report, you'll need to create a Custom Report Type."

**Why it happens:** LLMs are aware that CRTs solve multi-object reporting problems. They suggest CRTs proactively as the safest answer, without checking whether a standard report type already covers the combination.

**Correct pattern:**

```
Before creating a Custom Report Type:
1. Check standard report types — "Contacts with Opportunities"
   and "Accounts with Contacts and Opportunities" often already
   exist and cover common multi-object combos
2. Check if a cross-filter or formula column on a standard type
   solves the need without a CRT
3. Only create a CRT if:
   a. No standard type covers the required object combination, OR
   b. The standard type uses the wrong join semantics (inner vs outer)
      that cannot be corrected in the report itself

CRTs require admin creation time, a 24-hour appearance delay for
end users in some orgs, and ongoing field-layout maintenance.
Treat them as a last resort, not a first response.
```

**Detection hint:** Any suggestion to "create a Custom Report Type" when the objects involved are standard Salesforce objects (Accounts, Contacts, Opportunities, Cases) should trigger a check of standard report types first.

---

## Anti-Pattern 6: Assuming Report Subscriptions Respect Per-Recipient Sharing

**What the LLM generates:** "Send the report subscription to all sales reps — each rep will receive their own deals because Salesforce will run the report for each recipient."

**Why it happens:** LLMs reason by analogy to systems where reports are personalized per recipient. Salesforce report subscriptions do not work this way.

**Correct pattern:**

```
Report subscriptions run once as the report owner (or the specified
running user) and send the same result set to all recipients.

If Rep A owns 10 deals and Rep B owns 15 deals, and the report owner
is the VP of Sales with 200 deals visible — all recipients receive
the VP's 200-deal result set.

For personalized scheduled delivery:
- Have each rep subscribe themselves to the report individually
  (their own running user is applied)
- OR use a dynamic dashboard and train users to refresh on login
- OR build a custom Apex solution that queries per user and sends
  individual emails
```

**Detection hint:** Any mention of "send the subscription to multiple users" without noting that all recipients receive the same data should be flagged.
