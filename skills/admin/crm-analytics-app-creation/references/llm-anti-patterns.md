# LLM Anti-Patterns — CRM Analytics App Creation

Common mistakes AI coding assistants make when advising on CRM Analytics app setup.

## Anti-Pattern 1: Treating Permission Set Assignment as Sufficient for Data Access

**What the LLM generates:** "Assign the CRM Analytics Plus User permission set to your users and they will be able to access the dashboard and see the data."

**Why it happens:** LLMs apply the standard Salesforce model where permission set assignment is the primary access gate. CRM Analytics has three independent security layers that do not follow this model.

**Correct pattern:**

```
Three steps are required (not one):
1. Assign CRM Analytics Plus User permission set
2. In the app, click Share and add the user/group as Viewer
3. Configure a row-level security predicate on the dataset 
   if users should see restricted row subsets

All three are required. Stopping at step 1 produces blank dashboards.
```

**Detection hint:** Any response that says "assign the permission set and users can access the data" without mentioning app sharing and row-level security.

---

## Anti-Pattern 2: Using Connected Objects Directly as Dashboard Data Sources

**What the LLM generates:** "Enable Data Sync for the Opportunity object. Your Opportunity data will now be available to use in dashboard steps."

**Why it happens:** LLMs interpret "sync" as making data available for immediate use. Connected objects are a staging layer, not a visualization-ready dataset.

**Correct pattern:**

```
Data Sync → Connected Object → [Recipe or Dataflow] → Registered Dataset → Lens/Dashboard

Connected objects are staging replicas only.
They are NOT selectable as dataset sources in lenses or dashboards.
A recipe or dataflow must materialize them into a registered dataset first.
```

**Detection hint:** Any workflow that goes directly from "enable Data Sync" to "create a lens/dashboard" without a recipe or dataflow step.

---

## Anti-Pattern 3: Recommending Faceting for Cross-Dataset Dashboard Filtering

**What the LLM generates:** "Enable faceting on your dashboard to allow users to filter widgets by clicking on chart elements. This will propagate the selection across all your dashboard widgets."

**Why it happens:** Faceting sounds like a universal dashboard filtering mechanism. By default it stops at the dataset boundary, and the cross-dataset option (connected data sources) is easy to miss.

**Correct pattern:**

```
Faceting: by default filters steps on the SAME dataset (broadcastFacet,
receiveFacetSource control who sends and receives).
Across datasets, choose one:
1. Connected data sources (dashboard dataSourceLinks): link the shared field
   in each dataset so faceting crosses them
   (Dashboard JSON Guide: "Cross-Dataset Faceting with Connected Data Sources")
2. Selection bindings, e.g. {{cell(stepA.selection, 0, "DimensionField")}},
   wired into Step B's SAQL filter when the relationship is not a field match
```

**Detection hint:** Any recommendation to use faceting for widgets that reference different datasets.

---

## Anti-Pattern 4: Claiming CRM Analytics Data Is Real-Time

**What the LLM generates:** "CRM Analytics pulls live data from your Salesforce org, so dashboards always show the most current information."

**Why it happens:** LLMs conflate "connected to Salesforce" with "real-time data access." CRM Analytics datasets are materialized snapshots, not live queries.

**Correct pattern:**

```
CRM Analytics data is NOT real-time by default.
- Data Sync replicates Salesforce object records on a schedule
- Dataflows/recipes process the sync'd data into datasets on a schedule
- Dashboards query the last refreshed dataset version

For near-real-time requirements:
- Increase refresh frequency within the org budget: 60 dataflow and recipe
  runs per rolling 24 hours (Analytics Platform Setup Guide)
- Consider Direct Data for Data Cloud for live queries on Data Cloud data
  (UNVERIFIED (2026-10-03): the earlier "~15 minutes per sync cycle" minimum
  and the Direct Data connector scope were not confirmed)
- Surface dataset "Last Updated" timestamp in dashboard headers
```

**Detection hint:** Any claim that CRM Analytics shows "live" or "real-time" data without qualifying with refresh schedule.

---

## Anti-Pattern 5: Skipping Row-Level Security Configuration

**What the LLM generates:** "Create the app, share it with your team as Viewers, and the dashboard will show the relevant data to each user."

**Why it happens:** LLMs assume CRM Analytics inherits Salesforce object-level sharing (OWD, role hierarchy, sharing rules). It does not.

**Correct pattern:**

```
After configuring app sharing, ALSO configure dataset security:

Option A — Security Predicate (most flexible):
'OwnerId' == "$User.Id"
# Only shows records owned by the current user

Option B: Sharing Inheritance, always with a backup predicate:
Setup > Quick Find "Analytics" > Settings > "Inherit sharing from Salesforce";
then Data Manager > Connect > (object) > Row Level Sharing > Sharing inheritance on
# Works "for supported objects"; adds time to syncs, jobs, and queries
# UNVERIFIED (2026-10-03): the earlier "5 objects, max 3000 rows" limits and
# object list come from Salesforce Help and were not confirmed

Without one of these:
All Viewers see ALL dataset rows regardless of Salesforce sharing settings.
```

**Detection hint:** Any app setup workflow that does not mention security predicates or sharing inheritance configuration on the dataset.

---

## Anti-Pattern 6: Hand-Editing Retrieved Dashboard Files Before Deployment

**What the LLM generates:** "Retrieve the dashboard, open the `.wdash` file, remove the unused steps and fix the labels, then deploy to production."

**Why it happens:** Retrieved metadata looks like ordinary source code, and editing it is the normal developer move.

**Correct pattern:**

```
Metadata API, WaveDashboard:
- "Modifications to the .wdash component are unsupported."
- "Removing steps from the .wdash component causes deployment to the
  destination org to fail because the source dashboard fails validation."
Edit in the dashboard designer or JSON editor (CTRL/CMD+E), save in the
org, then retrieve and deploy the unmodified file.
```

**Detection hint:** Any deployment plan that edits `.wdash` content between retrieve and deploy.

