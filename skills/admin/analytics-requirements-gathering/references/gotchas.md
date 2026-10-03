# Gotchas: Analytics Requirements Gathering

Non-obvious CRM Analytics behaviors that turn incomplete requirements into rework. Sources are listed in `well-architected.md`. Line references cite the `pdftotext -layout` extraction of each Summer '26 PDF, written as `<guide> L<n>`. A claim that could not be re-read in an official source carries an inline `UNVERIFIED (2026-10-03):` marker.

## Gotcha 1: Synced objects are connected objects, and connected objects can't be visualized

**What happens:** "A data sync loads source object data as a connected object in Analytics. Connected objects can't be visualized directly, but are used like a cache to speed up other jobs that pull from the source object and load it into a dataset" (CRM Analytics REST API Developer Guide, Replicated Dataset Resources, `bi_dev_guide_rest L6012-6015`). A requirement that says "use the Opportunity object" therefore describes a sync, not a dataset.

**When it occurs:** Requirements list Salesforce objects as if they were dashboard-ready, and the build estimate omits the recipe or dataflow that turns each connected object into a dataset.

**How to avoid:** For every Salesforce source, write down the dataset it becomes and the recipe or dataflow that builds it. Include those builds in scope and in the refresh budget.

---

## Gotcha 2: The Integration User decides what can be extracted

**What happens:** "Analytics uses the permissions of the Integration User to extract data from Salesforce objects and fields when a dataflow or recipe job runs." If the job extracts an object or field the Integration User cannot read, "the job fails." The Integration User's permissions "don't affect access to the data in datasets" (Analytics Platform Setup Guide, `bi_admin_guide_setup L90-94`).

**When it occurs:** Requirements add a new custom field or a sensitive field late, or security restricts the Integration User profile, and the next scheduled job fails.

**How to avoid:** Put a field-level column in the data source matrix and check it against the Integration User. If a field must not reach CRM Analytics, restrict it on the Integration User on purpose and remove it from the requirement. Row visibility is a separate requirement (gotcha 3).

---

## Gotcha 3: A dataset without row-level security shows every row to everyone with access

**What happens:** "If row-level security isn't applied to a dataset, any user that has access to the dataset can view all records in the dataset" (Analytics Security Implementation Guide, `bi_admin_guide_security L289`). App sharing decides who can open the dataset, not which rows they see.

**When it occurs:** Requirements capture "the VP and the reps both use the dashboard" without saying what each may see, and the dataset ships with no predicate.

**How to avoid:** The audience matrix must name a row-level mechanism per role: a security predicate (for example `'OwnerId' == "$User.Id"`) or sharing inheritance. Set it before the dataset is created, because a recipe's Security Predicate has no effect once the dataset exists; changes must then be made on the dataset (`bi_admin_guide_security L274-275`).

---

## Gotcha 4: Sharing inheritance is accurate but slows every job and query

**What happens:** Sharing inheritance lets CRM Analytics apply the Salesforce sharing model to datasets. "The tradeoff for applying sharing inheritance is an increase in the time to complete data syncs, dataflow and recipe jobs, and queries. The more complicated the sharing settings, the more impact there is" (`bi_admin_guide_security L253-257`). When sharing inheritance is enabled, the predicate can be set to `'false'` to block users not covered by sharing, and that is the default (`L276-277`).

**When it occurs:** Requirements ask for "the same access as Salesforce" on a large object with complex sharing and an aggressive refresh cadence.

**How to avoid:** Record the choice per dataset with its cost. Use sharing inheritance where Salesforce sharing is the real rule. Use a simpler predicate where the rule is simple (owner, territory). Tell stakeholders that users not covered by sharing see nothing under the default `'false'` predicate.

---

## Gotcha 5: Refresh cadences share a 60-run rolling 24-hour budget

**What happens:** The org may run at most 60 dataflow and recipe jobs in a rolling 24-hour period. Runs under 2 minutes (and data syncs) do not count, but at the limit "you can't run a dataflow, recipe, or data sync job, regardless of size." Only 3 recipe runs execute concurrently, and concurrent dataflow runs are 2 on a CRM Analytics Plus production org but 1 on a sandbox or a CRM Analytics Growth production org (`bi_admin_guide_setup L1148-1185`).

**When it occurs:** Each stakeholder asks for hourly data on their source, and the sum exceeds the budget. Growth-licensed orgs hit dataflow concurrency first.

**How to avoid:** Add a refresh budget to the requirements: every scheduled job, its expected duration, and its frequency. Negotiate cadence per source before build.

---

## Gotcha 6: The Security User must read every User field a predicate references

**What happens:** When a dataset predicate references the User object, Analytics evaluates it as the Security User. "The Security User must have at least read permission on each User object field included in a predicate." Standard User fields are readable by default; "if the predicate is based on a custom field, then grant the Security User read access on the field." Otherwise an error appears when users query the dataset (`bi_admin_guide_setup L98-104`).

**When it occurs:** The audience matrix keys visibility on a custom User field such as `Sales_Region__c`, and nobody grants the Security User access.

**How to avoid:** List every User field the predicates reference in the requirements, and add "grant the Security User read on these fields" to the build tasks. Predicates referencing `$User` also need a new user session before a changed value is recognized (`bi_admin_guide_security L295`).

---

## Gotcha 7: External and output connections count against org API limits; the local connection does not

**What happens:** "When using a Salesforce local input connection, CRM Analytics bulk API usage doesn't count towards Salesforce bulk API limits. Use of the external Salesforce connection and output connection impacts your limits" (`bi_admin_guide_setup L1140-1141`). Writing data back out is also capped per run, for example 100 MB or 1 million rows per recipe run per output connector to Salesforce, and 100 MB or 1 million rows per rolling 24-hour period (`L1241-1244`).

**When it occurs:** Requirements pull data from another Salesforce org or write results back to Salesforce, and the integration team's API budget is consumed without warning.

**How to avoid:** Mark each source as local, external, or output in the matrix. Share the external and output volumes with whoever owns the org's API limits.

---

## Gotcha 8: Dataset row storage is capped by license

**What happens:** The total rows across all registered datasets depend on the license mix: 10 billion with CRM Analytics Plus, 100 million with CRM Analytics Growth, and 25 million for each of several packaged analytics apps (`bi_admin_guide_setup L974-1004`).

**When it occurs:** Requirements for event, activity, or history datasets assume Plus-scale storage on a Growth-licensed org.

**How to avoid:** Estimate rows per dataset in the requirements and compare the total with the license allocation before committing to the design.

---

## Gotcha 9: Data Cloud direct query and external incremental refresh are unconfirmed assumptions

**What happens:** Earlier versions of this skill stated that a Data Cloud direct connection queries Data Model Objects without a dataset but does not support all SAQL operations, and that external connectors pull full tables unless incremental refresh is configured. UNVERIFIED (2026-10-03): neither behavior is described in the CRM Analytics REST API guide or the Analytics Platform Setup Guide read for this pass. The REST guide shows a connected object's `connectionMode` set to `Full` (`bi_dev_guide_rest L6195-6200`) but does not list the other modes.

**When it occurs:** Requirements promise real-time Data Cloud dashboards or hourly refresh of very large external tables.

**How to avoid:** Mark these as assumptions to confirm in a sandbox. Record the needed query patterns and whether the external table has a reliable change timestamp, so the developer can test them early.
