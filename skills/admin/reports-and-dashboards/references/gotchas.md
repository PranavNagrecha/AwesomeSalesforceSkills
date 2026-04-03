# Gotchas: Reports and Dashboards

---

## Reports Respect Record-Level Sharing — "Missing" Records Are Usually a Sharing Issue

**What happens:** A VP asks the admin to build a pipeline report. The report shows 50 opportunities. The VP says "that's not right — we have hundreds of opportunities." The admin checks the report, the filters look correct. The issue: the VP's role in the hierarchy only covers their direct reports' records. The hundreds of other opportunities are owned by teams outside their hierarchy. The report is correct — the sharing model is showing them exactly what they're supposed to see.

**When it bites you:** Every time a stakeholder says "my report is missing data." Before investigating the report configuration, always check: "Does the running user have access to the records they expect to see?"

**How to diagnose:**
1. Log in as or simulate the running user
2. Go to the relevant object's list view
3. Select "All [Objects]" (requires View All) — if the count differs from the running user's view, it's a sharing issue
4. Run the same report as a System Administrator — if you see more records, it's a sharing issue, not a report issue

**How to address:**
- Sharing issue confirmed → review sharing model, don't patch the report
- Report was expected to show all records → review whether the user needs elevated access, or if the dashboard should "Run as specified user" with appropriate access

---

## Historical Trending: Only Works on Specific Objects and Fields, and Only Forward

**What happens:** An admin asks: "Can you build a report showing how many open cases we had each day for the last 6 months?" Historical Trending would answer this. But Historical Trending wasn't enabled on Cases 6 months ago. Enabling it now starts capturing data from today. There's no retroactive data. The admin tells the VP there's 6 months of historical trend data — there isn't.

**When it bites you:** Requests for historical trend reports on objects where Historical Trending wasn't set up in advance.

**What Historical Trending supports:**
- Objects: Opportunities, Cases, Leads, Forecasts, up to 3 custom objects
- Field types: Date, Date/Time, Number, Currency, Percent, Checkbox, Picklist
- Lookback: Up to 3 months of data (rolling window)
- Maximum 8 date snapshots per record

**How to avoid it:**
- Enable Historical Trending proactively on any object where trend data may be needed
- Set it up before business requests trend reports — not after
- Communicate clearly to stakeholders: "We can show trend data from [date enabled] forward"

---

## Report Subscriptions Don't Respect Row-Level Security for Recipients

**What happens:** An admin creates a report of all Opportunities over $1M. They set up a subscription to send this report every Monday to 15 sales reps. Each rep only has access to their own opportunities via the sharing model. But the subscription sends the full report — all 1M+ opportunities — because it runs as the report owner (a Manager with "View All"). Each rep receives everyone else's pipeline data in their inbox.

**When it bites you:** Any time a report subscription is configured to send to users who have narrower access than the report owner.

**How to avoid it:**
- Before scheduling a subscription, explicitly check: does the report contain records the recipients shouldn't see?
- If recipients should see different data: DON'T use subscriptions — have each user run the report themselves ("Run as logged-in user" applies when users run manually)
- Secure alternative: build a dashboard with "Run as logged-in user" that each rep visits individually
- If a subscription is necessary: ensure the report's report type and filters produce only data appropriate for ALL recipients

---

## Dashboard Filters Don't Always Filter All Component Types

**What happens:** An admin adds a date range filter to a dashboard. The filter appears at the top and looks like it applies to all components. But one component (a matrix report) doesn't update when the filter changes. The underlying report uses a different date field than what the dashboard filter is targeting.

**When it bites you:** Complex dashboards with multiple report types where different components use different date fields.

**How to avoid it:**
- After adding any dashboard filter, test EVERY component by changing the filter value and verifying the component updates
- Dashboard filters only work when the underlying report field matches what the filter targets
- Document which components a filter applies to in the dashboard description

---

## Custom Report Types: Missing Data Due to Join Type

**What happens:** An admin creates a Custom Report Type: Account → Contacts → Opportunities. The report returns only Accounts that have at least one Contact AND at least one Opportunity. An Account with no Contacts but with Opportunities is invisible. The admin built an "inner join" report thinking they had "all accounts with opportunities."

**When it bites you:** Any Custom Report Type that chains multiple relationships. The default join type may exclude records the user expects to see.

**The join types:**
- "A record must have related B records" → inner join (default) — only records WITH the relationship appear
- "A records may or may not have related B records" → outer join — records appear even without the relationship

**How to avoid it:**
- When creating a Custom Report Type, explicitly choose the join type for each related object
- Ask: "Should records without [related object] still appear in the report?" If yes → outer join
- Test with a record you know has no related records — does it appear?
