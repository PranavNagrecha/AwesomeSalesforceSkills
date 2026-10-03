# Gotchas: Einstein Analytics Basics

Non-obvious behaviours that decide whether CRM Analytics is the right tool and why a basic design fails. Each gotcha names its source. Claims that could not be confirmed from a fetched source carry an inline `UNVERIFIED (2026-10-03):` marker. "Setup Guide" means the Analytics Platform Setup Guide (Spring '26, https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_admin_guide_setup.pdf); "Security Guide" means the Analytics Security Implementation Guide (Spring '26, https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_admin_guide_security.pdf).

---

## Gotcha 1: Mistaking "Fancy Dashboard" For A CRM Analytics Requirement

**What happens:** Stakeholders ask for CRM Analytics because the dashboard should "look executive." The actual requirement is a summary chart on standard Salesforce data. CRM Analytics is "available for an extra cost in Enterprise, Performance, and Unlimited Editions," so the choice buys licences, a data pipeline, and a second security model.

**When it occurs:** Sales ops, service ops, and leadership dashboards that are visually ambitious but analytically simple.

**How to avoid:** Make the team state what standard reports cannot do. If the answer is unclear, stay in Reports and Dashboards.

**Source:** Setup Guide, Set Up the CRM Analytics Platform (edition box: "Available with CRM Analytics, which is available for an extra cost in Enterprise, Performance, and Unlimited Editions. Also available in Developer Edition").

---

## Gotcha 2: Datasets Are Refreshed By Jobs, And Jobs Have A Daily Budget

**What happens:** Users assume analytics data is live. A dashboard shows the last dataflow or recipe run, and trust drops. Teams then schedule runs every few minutes and hit the org limit: 60 dataflow and recipe runs in a rolling 24-hour period. Runs under 2 minutes and data sync do not count, but once the limit is reached "you can't run a dataflow, recipe, or data sync job, regardless of size." Concurrency is also low: 1 dataflow at a time in a sandbox or a Growth-licensed production org, 2 with Plus.

**When it occurs:** Daily standups, queue management, and any dashboard users compare with live records.

**How to avoid:** Write the refresh cadence on every dashboard and confirm the latency is acceptable. Budget runs per day across all recipes and dataflows before adding a schedule. If the requirement truly is live, that is a point for Reports.

**Source:** Setup Guide, CRM Analytics Limits, Recipe and Dataflow Limits (60 runs per rolling 24 hours and the 2-minute rule; concurrent dataflow runs 2 or 1; concurrent recipe runs 3; 48-hour maximum run time).

---

## Gotcha 3: Licences Are Permission Set Licences, And Row Allocation Is Contractual

**What happens:** The pilot works for admins and analysts, but rollout stalls because the intended users lack a licence. Assigning any CRM Analytics permission set auto-assigns the CRM Analytics Growth permission set licence, which pairs only with certain user licences (Lightning Platform, Full CRM, Salesforce Platform, Salesforce Platform One). Data volume is capped by licence: the limits table allocates 100 million rows for Growth and 10 billion for Plus, and "CRM Analytics license data storage limits are contractual, not technical." The same guide also says each Growth or Plus licence limits the instance to 1 billion rows; the two statements disagree, so confirm the contract.

**When it occurs:** Executive dashboards, regional rollouts, Experience Cloud sharing (which needs a CRM Analytics for Communities permission set licence), and projects that load years of history.

**How to avoid:** Count actual consumers and rows before building. Check which user licences the audience holds. Record the contracted row allocation and the projected rows per dataset.

**Source:** Setup Guide, Learn about CRM Analytics Platform Licenses and Permission Sets (auto-assignment, compatible user licences, contractual row limits, 1 billion row statement); Learn about CRM Analytics Permission Set Licenses and User Permissions (Communities licence); CRM Analytics Limits, Dataset Row Storage Allocations per License.

---

## Gotcha 4: A Dataset With No Row-Level Security Shows Every Row To Everyone Who Can Open It

**What happens:** Teams assume Salesforce sharing governs analytics. It does not by default: "If row-level security isn't applied to a dataset, any user that has access to the dataset can view all records in the dataset." Field-level security from Salesforce "isn't preserved when the data is loaded into a CRM Analytics dataset." Sharing inheritance exists but has limits, so it must be backed by a security predicate.

**When it occurs:** Territory-based analytics, partner views, and sensitive service metrics.

**How to avoid:** Treat analytics security as its own design: a security predicate or sharing inheritance with a backup predicate (`'false'` blocks users sharing cannot cover) on every dataset with restricted data. Test with real personas. Note that changes to security after a dataset exists must be made on the dataset; editing `rowLevelSharingSource`, `rowLevelSecurityFilter`, or the recipe's Security Predicate has no effect.

**Source:** Security Guide, Add Row-Level Security with a Security Predicate (warning on no row-level security; editing-the-dataset note; `'false'` default with sharing); Add Row-Level Security by Inheriting Sharing Rules (time cost of inheritance); overview note ("If you use sharing inheritance, you must also set a security predicate"). Setup Guide, CRM Analytics Limitations, Field-Level Security.

---

## Gotcha 5: The Integration User Decides What Can Be Extracted, And A Missing Field Fails The Job

**What happens:** A recipe or dataflow that extracts a field the internal Integration User cannot read fails. The Integration User has View All Data, so it can also pull sensitive fields into datasets nobody meant to expose. A predicate on a custom User field errors unless the internal Security User can read that field.

**When it occurs:** After new fields are added to a source object, after FLS clean-ups, and when predicates use custom User fields.

**How to avoid:** Grant the Integration User field-level security on every field the app uses, and restrict it on sensitive fields that must stay out of datasets. Grant the Security User read access on every custom User field used in a predicate. Do not delete either internal user.

**Source:** Setup Guide, Learn about Internal Analytics Users ("If the dataflow or recipe is configured to extract data from an object or field on which the Integration User does not have permission, the job fails"; Security User predicate rule; "do not delete either of these users"); CRM Analytics Limitations, Field-Level Security.

---

## Gotcha 6: Disabling CRM Analytics Strips The Permission Sets

**What happens:** An admin disables CRM Analytics to stop a runaway pilot. "If you disable CRM Analytics, user permissions are removed from each defined permission set. If you re-enable CRM Analytics later, you must define the permission sets again."

**When it occurs:** Trial clean-ups, licence disputes, and sandboxes where someone toggles the feature.

**How to avoid:** Keep the CRM Analytics permission sets in source control (Example 2 in `references/examples.md`) and redeploy them after any re-enable. Prefer revoking permission set assignments to disabling the platform.

**Source:** Setup Guide, Learn about CRM Analytics Platform Licenses and Permission Sets (Important box).

---

## Gotcha 7: One Currency, One Locale Per Dataset, And Changed `$User` Values Wait For A New Session

**What happens:** A global dashboard shows amounts in the corporate currency only, and dates in one format for everyone. CRM Analytics "doesn't convert to another currency," and "each dataset can have a single locale" that individual user settings do not override. Predicates that read `$User` fields do not see a changed value until the user starts a new session. UNVERIFIED (2026-10-03): `AnalyticsSettings.enableWaveMulticurrency` (Beta, API 56.0+) suggests a multiple-currency option exists; the Setup Guide's limitations page still says multiple currencies are not supported, so test before promising it.

**When it occurs:** Multi-country rollouts, multi-currency orgs, and territory or role changes that should change what a user sees.

**How to avoid:** State the reporting currency and locale in the requirement. If users need local currency, that is a point for Reports or a pre-converted field. Tell users to log out and in after access-affecting changes.

**Source:** Setup Guide, CRM Analytics Limitations, Localization and Internationalization. Security Guide: "Security predicates referencing $User information require a new user session before a new value is recognized." Metadata API Developer Guide, Version 67.0, AnalyticsSettings (`enableWaveMulticurrency`).
