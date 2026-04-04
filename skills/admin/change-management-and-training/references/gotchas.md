# Gotchas — Change Management and Training

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: In-App Guidance Prompts Ignore Permission Sets — Profile-Only Targeting

**What happens:** In-App Guidance in Salesforce allows you to target prompts by user profile. If your org has moved to a "one profile fits all" model with permission sets controlling access, every user in that profile sees the prompt — including users who are not affected by the change.

**When it occurs:** Most frequently in orgs that standardized on a single "Standard User" profile and use permission sets for all granular access. A BA sets up a walkthrough for "Agents who use the new Case Status field" but targets the "Standard User" profile — which also includes Managers, Admins, and Sales Reps.

**How to avoid:** Before configuring In-App Guidance, confirm whether affected users share a profile that is NOT used by unaffected users. If not, use the "User Segment" filter (available in Spring '23+) which supports Custom Permissions alongside profile targeting. Assign a custom permission to affected users and use it as the In-App Guidance filter. Test in sandbox with multiple test users covering both affected and unaffected scenarios before go-live.

---

## Gotcha 2: Path Coaching Text Does Not Inherit Across Record Types

**What happens:** When you add coaching text to a stage in Path Settings, the configuration applies to a specific combination of Object + Record Type + Picklist field. If you configure coaching for the "Enterprise Opportunity" record type and later add a "Mid-Market Opportunity" record type, the new record type has no coaching text — it is not inherited.

**When it occurs:** During rollouts that add new record types to an existing object where Path is already configured. Admins assume that since the picklist values are shared, the coaching text is shared. It is not. Users assigned the new record type see an empty Path.

**How to avoid:** After adding a new record type, navigate to Setup > Path Settings and explicitly configure coaching text for every new record type + picklist combination. Include a Path review in your deployment checklist whenever a record type is added or cloned.

---

## Gotcha 3: Adoption Dashboard Login Metrics Include API and Integration Logins

**What happens:** The Salesforce Adoption Dashboards package (Salesforce Labs, AppExchange) measures user activity using the LoginHistory standard object. This object records all successful authentications — including OAuth logins from connected apps, integration users, and scheduled jobs. If an integration user runs nightly syncs, it will appear as a daily "active user" in the adoption reports.

**When it occurs:** Any org with integration users, connected apps, or API-based automations running under named user credentials. The inflated active user count makes adoption appear higher than it is, masking real adoption gaps.

**How to avoid:** When building or reviewing adoption reports, filter LoginHistory by `LoginType = 'Application'` to capture only standard browser-based logins. Exclude integration users by filtering out known service account usernames or by using a dedicated Integration profile that is excluded from adoption report filters. Document this filter in the report description so future admins do not remove it.

---

## Gotcha 4: Trailhead myTrailhead Content Is Org-Specific and Not Shared Across Orgs

**What happens:** myTrailhead (the branded, org-specific Trailhead experience) allows companies to create custom modules and trails. Content created in one Salesforce org's myTrailhead instance is not accessible from another org or from standard public Trailhead. Users assigned to a trail in one org cannot access it from a different org login.

**When it occurs:** When a company has multiple Salesforce orgs (e.g., separate EMEA and AMER instances) and attempts to roll out a myTrailhead learning path across all of them. Admins set up the trail in one org and share the link — users in other orgs cannot authenticate.

**How to avoid:** For multi-org environments, either (a) use standard public Trailhead trails which are org-agnostic, or (b) confirm that myTrailhead licenses cover all target orgs before investing in custom content creation. If only one org has myTrailhead, host custom training in that org and grant cross-org access via SSO or a dedicated training org.
