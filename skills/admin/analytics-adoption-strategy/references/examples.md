# Examples — Analytics Adoption Strategy

## Example 1: Analytics Adoption App Setup After New Dashboard Launch

**Context:** A Salesforce admin at a mid-size manufacturing company has just launched a CRM Analytics app with five dashboards for the sales operations team (18 users). Three weeks after launch, leadership asks how many people are actually using the dashboards. The admin has no data.

**Problem:** Without the Analytics Adoption App configured, there is no org-native way to see who opened which dashboard and when. The admin has only anecdotal feedback from two enthusiastic managers and no signal on the other 16 users.

**Solution:**

Step 1 — Verify the Analytics Adoption Metadata managed package is installed:
```
Setup > Installed Packages
Look for: "Analytics Adoption Metadata"
If absent: install from AppExchange before proceeding — the template will not appear without it
```

Step 2 — Create the Adoption App from the template:
```
Analytics Studio > Create > App > Use a Template
Select: Adoption Analytics
Configuration wizard:
  - Select "All Apps" scope (admin has access to all)
  - Confirm the dataflow schedule (default: daily at 2 AM)
  - Finish
```

Step 3 — Review the auto-generated dashboards:
The template creates three primary views:
- **App Usage Overview** — total opens by app per week
- **Dashboard Usage Detail** — opens per dashboard, filtered by date range
- **User Engagement** — ranked list of users by open count

Step 4 — Share the Adoption App with analytics champions:
```
Adoption App > Share
Add: Analytics Admin group as Manager
Add: Department Heads as Viewer
```

Step 5 — Schedule a weekly 15-minute review for the first 6 weeks:
Pull the Dashboard Usage Detail view, filter to the five target dashboards, note which dashboards have fewer than 50% of the 18-user audience opening them, and follow up with the relevant manager.

**Why it works:** The Adoption App is purpose-built for analytics usage tracking — it captures the event data that the platform writes when a user opens an app, dashboard, or lens. Unlike login metrics or CRM record-creation metrics, it measures analytics-specific engagement directly.

---

## Example 2: Embedding Pipeline Dashboard on Opportunity List View to Drive Field Rep Adoption

**Context:** The revenue operations team built a CRM Analytics pipeline health dashboard showing win rate by stage, average deal age, and forecast accuracy. After two months, the Adoption App shows the dashboard averages 4 opens per week across 35 sales reps. The reps report they "always forget to check it."

**Problem:** Sales reps spend their Salesforce time on the Opportunity and Account record pages. Navigating to Analytics Studio requires an extra step that most reps do not take. The dashboard exists but is not in the workflow.

**Solution:**

Step 1 — Identify the highest-traffic page for the reps:
In this org, reps use the "My Open Opportunities" list view daily. This is the right page to embed.

Step 2 — Open Lightning App Builder for the Opportunities list view page:
```
Setup > Lightning App Builder
Open: "Opportunities" List View Page
(or create a new App Page named "My Pipeline" if a standalone page is preferred)
```

Step 3 — Add the CRM Analytics Dashboard component:
```
Component Palette > search "CRM Analytics Dashboard"
Drag to the top region of the page (above the list view)
Properties pane:
  App: Sales Pipeline App
  Dashboard: Pipeline Health Overview
```

Step 4 — Configure the filter to scope the dashboard to the current user:
```
Dashboard Filter configuration:
  Filter name (as defined in the dashboard): OwnerFilter
  Filter value: {!currentUser.Id}
```
This ensures each rep sees only their own pipeline data, not the full team view.

Step 5 — Activate the page for the Sales Rep profile.

Step 6 — Measure impact via Adoption App:
After 4 weeks, compare Dashboard Usage Detail filtered to "Pipeline Health Overview" — the embedded version should show 3-5x higher weekly open counts than the pre-embedding baseline of 4.

**Why it works:** The rep never navigates away from their existing workflow. The dashboard appears as part of the page they already open. Filter pass-through via `{!currentUser.Id}` ensures the data is personally relevant, which drives repeat usage.

---

## Example 3: Self-Service Lens Access for Operations Analyst Team

**Context:** An operations analyst team of 6 wants to explore the same datasets that power shared dashboards to answer ad hoc questions. They do not want to wait for the analytics developer to build a new dashboard for every one-off request.

**Problem:** The analytics developer assigned all 6 analysts as App Viewers. Viewers cannot create lenses or save explorations — they are locked to pre-built dashboards. The analysts are frustrated and have reverted to exporting data to Excel for their analysis.

**Solution:**

Step 1 — Change the 6 analysts from Viewer to Editor on the "Operations Analytics" app:
```
Operations Analytics App > Share
Find each analyst's name (or their Operations Analysts public group)
Change access level from Viewer to Editor
```

Step 2 — Brief the analysts on the difference between shared dashboards and personal lenses:
- Shared dashboards (in the app's main asset list) are canonical — do not edit or save changes to them
- Personal lenses (created from a dataset, saved to "My Private App" or a personal folder) are safe exploration space

Step 3 — Run a 45-minute lens creation walkthrough:
```
Open a dataset (e.g., "Operations Metrics")
Select measures and group-by dimensions
Apply a chart type
Save As > personal lens in "My Private App"
```

Step 4 — Confirm the shared dashboards are not at risk:
Advise the analytics developer to set the canonical dashboards to "read-only" by switching their sharing to make only the admin the Editor — other Editors in the app can still explore datasets but cannot save over canonical dashboards if dashboard-level protection is applied.

**Why it works:** Editor access unlocks dataset exploration (lens creation) without granting the ability to manage app membership or delete shared assets. The combination of Editor access, dataset awareness, and clear norms around shared vs. personal space gives the analysts what they need without corrupting the org's canonical dashboards.

---

## Anti-Pattern: Confusing Salesforce Adoption Dashboards with the Analytics Adoption App

**What practitioners do:** When asked to measure "who is using our analytics dashboards," the admin installs the Salesforce Adoption Dashboards package from AppExchange (Salesforce Labs) and opens the resulting dashboard.

**What goes wrong:** The Salesforce Adoption Dashboards package tracks CRM record creation (Opportunities created, Cases created, Accounts created) and login frequency by user and profile. It does not track CRM Analytics app, dashboard, or lens opens at all. The admin reports a 90% "active user" rate (based on login frequency) while 80% of users have never opened the analytics app. Leadership thinks analytics adoption is healthy when it is not.

**Correct approach:** Use two separate tools for two separate signals:
- **Salesforce Adoption Dashboards (AppExchange / Salesforce Labs)**: measures CRM platform adoption — login frequency, record creation, feature engagement for standard Salesforce features
- **Analytics Adoption App (Analytics Studio template, requires Analytics Adoption Metadata managed package)**: measures CRM Analytics-specific usage — who opened which app, dashboard, or lens and when

Both tools are valid and serve different purposes. Neither replaces the other.
