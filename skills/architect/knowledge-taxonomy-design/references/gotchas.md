# Gotchas — Knowledge Taxonomy Design

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Validation Status Enablement Is One-Way

**What happens:** After enabling Validation Status in Setup → Knowledge Settings, the checkbox cannot be unchecked without first removing all Validation Status values from every article version in the org. If thousands of article versions exist, this requires a bulk data operation via Data Loader or API before the setting will allow disablement. Salesforce will surface an error in Setup if you attempt to disable it while any record holds a non-null value.

**When it occurs:** Admins enable Validation Status in a production org to test the feature before the picklist design is finalised, then try to reverse course when stakeholders change requirements. Also occurs after a Validation Status picklist value is removed from the picklist definition — articles holding the removed value become invalid and must be mass-updated before re-sync.

**How to avoid:** Design the full Validation Status picklist (including all custom values) and map each value to a workflow role and a policy decision before enabling in production. Enable in a Developer sandbox first and run the full Solve/Evolve workflow end-to-end. Only enable in production once the design is locked.

---

## Gotcha 2: Only 3 Data Category Groups Are Active by Default — the 4th Silently Blocks

**What happens:** Salesforce allows a maximum of 5 Data Category Groups per org but activates only 3 by default. If an admin creates a fourth group and assigns it to the Knowledge object, the assignment may appear to succeed in Setup but the fourth group will not appear in article categorisation UI, search facets, or SOSL category filters. In some org editions, Setup shows a validation error; in others the assignment silently fails with no user-facing error.

**When it occurs:** Taxonomy designs that require four dimensions (e.g., Products, Topics, Audience, Region) without checking the active group limit. Migrations from a legacy system that had four or more category dimensions.

**How to avoid:** Before designing a taxonomy that requires more than 3 active groups, open a Salesforce support case to confirm whether the org's edition supports a limit increase and request the increase. Build the taxonomy design around 3 active groups as the baseline. The fourth slot should only be activated after the limit increase is confirmed in the target environment, not in a sandbox.

---

## Gotcha 3: Archived Articles Linger in Experience Cloud Search Results

**What happens:** When an article is archived, its Publication Status changes immediately in the database, but the Experience Cloud search index does not update synchronously. Depending on the site's search configuration (Salesforce Search vs Custom Apex Search), archived articles can continue to surface in customer-facing search results for minutes to hours after archival. If a customer clicks the result, they may see a "page not found" or "permission denied" error rather than a clean redirect.

**When it occurs:** Any time articles are bulk-archived during a content audit or taxonomy restructuring. Also occurs during the migration window when old-taxonomy articles are archived and new-taxonomy articles are published simultaneously.

**How to avoid:** Schedule bulk archival operations during low-traffic windows. After bulk archival, manually trigger a search index rebuild if the platform supports it (Setup → Search → Rebuild). Include a communication step in the migration plan to inform Experience Cloud site owners that search results may be stale for up to 2 hours post-archival. Do not archive and replace articles in the same transaction window if real-time search accuracy is critical.

---

## Gotcha 4: Data Category Visibility Rules Override Publication Status

**What happens:** An article can be in Published status but still invisible to a specific agent or portal user if that user's profile or permission set does not have Data Category visibility configured for the article's assigned category. Admins who test article publishing as a System Administrator (who sees all categories) will report the article is visible, but agents on restricted profiles may not see it at all in search results.

**When it occurs:** After activating a new Data Category Group or adding new categories to an existing group. Also occurs after profiles are cloned or rebuilt — the cloning process does not always copy Data Category visibility settings.

**How to avoid:** After any Data Category Group or category changes, audit affected profiles via Setup → Users → Profiles → [Profile Name] → Data Category Visibility. Build a test protocol that verifies article visibility using a test user on each affected profile, not as System Administrator. Include a Data Category visibility check in the deployment runbook for any Knowledge taxonomy change.

---

## Gotcha 5: Search Activity Gaps Has No API — Manual Export Required for Trend Tracking

**What happens:** The Search Activity Gaps dashboard in the Knowledge console is a UI-only report. There is no REST API, Connect API endpoint, or SOQL query that exposes the underlying gap data programmatically. If you want to track gap closure trends over time (a core KCS measurement), you must manually export the gap list from the UI at each measurement interval and store it externally.

**When it occurs:** Any KCS program that promises leadership a monthly gap-closure trend report or ROI dashboard. Teams that assume Salesforce Reports or Analytics Studio can pull Search Activity Gaps data.

**How to avoid:** Establish a manual export cadence (weekly or bi-weekly) from day one of the KCS program. Export to a shared spreadsheet or BI tool. Document the export process so any team member can perform it, not just the Knowledge admin. Do not commit to automated gap-trend dashboards in the program charter without first confirming whether a custom instrumentation approach (e.g., tracking article creation events alongside gap exports) is in scope.
