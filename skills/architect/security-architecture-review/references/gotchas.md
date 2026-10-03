# Gotchas — Security Architecture Review

Each gotcha names its source. "Security Guide" means the *Salesforce Security Guide* (Summer '26). Claims no fetched source confirms carry an inline `UNVERIFIED (date):` marker. Each gotcha ends with a **How to avoid** step.

## Gotcha 1: External OWD Defaults Depend on When the Org Was Created

**What happens:** A reviewer checks only the internal OWD column and misses what external users get. Correction (2026-10-03): earlier text said an object can be Private internally yet open externally because the external OWD "did not inherit" a later tightening. The Security Guide ("Organization-Wide Sharing Defaults") says the external access level for an object cannot be more permissive than the internal level. What it does say is that for orgs created before Spring '20, default external access was set to the original default access level (so a Public Read Only internal default produced a Public Read Only external default), while orgs created after Spring '20 default external access to Private. It recommends Private external defaults unless the business requires otherwise, and notes that an object's external default must be Private for external users to see it in reports.

**When it occurs:** Older orgs with Public internal defaults on Account, Contact, or Case that later added an Experience Cloud site.

**Why it matters:** External users include portal customers, partners, and in some architectures, authenticated API consumers using community licenses. A "Private" internal OWD with an open external OWD means the sharing model is only private for internal employees — external parties can access data broadly.

**How to avoid:** In Setup > Sharing Settings, review both the "Default Internal Access" and "Default External Access" columns for every object with sensitive data, and record the org's creation date beside them. Confirm they are both intentional and documented. Pay special attention to `Contact`, `Account`, `Case`, and any custom objects with PII or regulated data. If the org has no Experience Cloud sites, external OWD is irrelevant, but document that fact in the review.

---

## Gotcha 2: `with sharing` Does Not Enforce FLS — It Only Enforces Record Visibility

**What happens:** A developer declares `with sharing` on a class and a reviewer marks all FLS checklist items as "pass" because the class "enforces sharing." The class still returns field values for fields the running user has no FLS read access to, because at API 66.0 or earlier SOQL in a `with sharing` class retrieves all requested fields regardless of FLS unless an explicit FLS enforcement mechanism is used.

**When it occurs:** Consistently throughout orgs that learned Apex security from older training materials that equated sharing enforcement with security. The `with sharing` keyword controls record-level sharing only. FLS is entirely separate.

**Why it matters:** A user with read access to an Account record but no FLS read on `Account.AnnualRevenue__c` will still receive that field value if the Apex query includes it and the class, saved at API 66.0 or earlier, only declares `with sharing`.

**How to avoid:** For every Apex class identified in the review, check for FLS enforcement separately from sharing enforcement. The Apex Developer Guide ("Enforce Object and Field Permissions") states that object and field permissions are distinct from sharing and take precedence when they conflict. The valid mechanisms are:
- `WITH USER_MODE` on the query, or `as user` / `AccessLevel.USER_MODE` on DML and `Database` methods (GA in API 57.0, Spring '23; recommended for new code)
- `Security.stripInaccessible(AccessType.READABLE, records)` before returning data — it returns an `SObjectAccessDecision`, so return `.getRecords()`, not the original list
- `WITH SECURITY_ENFORCED` in SOQL — legacy only. It checks just the `SELECT` list, mishandles polymorphic fields, and reports one violation rather than all; at API 67.0+ it does not compile at all

Mark any class that queries sensitive fields in `with sharing` without FLS enforcement as a High finding — but read the class's `apiVersion` first, because at **67.0+** queries and DML run in user mode with no keyword at all and enforce FLS on their own, while at **66.0 and earlier** they do not. The gate is the `.cls-meta.xml`, not the org's release. Canonical table: [`agents/_shared/AGENT_CONTRACT.md`](../../../../agents/_shared/AGENT_CONTRACT.md) § *Apex security idiom by API version*.

---

## Gotcha 3: Connected App "IP Relaxation" Is Not the Same as "Trusted IP Range"

**What happens:** A reviewer sees a Named Credential or Connected App and notes "IP range is configured" and marks the IP restriction check as passing. The Connected App actually has "Relax IP restrictions" selected (not a restricted IP range), which means it accepts connections from any IP address — the opposite of what the reviewer assumed.

UNVERIFIED (2026-10-03): the connected app IP policy behavior described here is documented in Salesforce Help, which this pass could not fetch.

**When it occurs:** The Salesforce UI uses similar language for two opposing settings. "Relax IP restrictions" means "bypass IP restrictions." Trusted IP ranges configured on the org or profile are separate from Connected App IP policies.

**Why it matters:** A Connected App with IP relaxation enabled combined with a long-lived refresh token provides an attacker who has stolen a refresh token unrestricted access from any location, bypassing org-level IP range restrictions entirely.

**How to avoid:** In Setup > Apps > Connected Apps > Manage Connected Apps, review the "IP Relaxation" column for each app. The setting should be "Enforce IP restrictions" unless there is a documented business requirement for global access. Document each app's setting and the justification for any relaxation in the review report.

---

## Gotcha 4: Criteria-Based Sharing Rules Can Grant Broader Access Than Intended as Data Changes

**What happens:** A criteria-based sharing rule was created that shares all Opportunity records where `Stage != 'Closed Won'` with the Sales Operations role. Over time, the pipeline grows and 95% of Opportunity records match the criteria. When a deal closes, it falls out of the share rule but all related notes, attachments, and child records that were accessed during the deal lifecycle may have already been exported or cached.

**When it occurs:** Criteria-based rules that use negative conditions (`!=`, `NOT IN`) effectively share most records rather than a targeted subset. Rules that were designed for a small org can become overly permissive at scale without anyone explicitly changing a configuration.

**Why it matters:** Unlike role hierarchy visibility, criteria-based sharing rules are not visible in standard reports or dashboards. They require a deliberate audit to understand their scope. An org that has accumulated 50+ sharing rules over five years may have contradictory or overlapping rules that no one has reviewed since they were created.

**How to avoid:** Export all sharing rules from the org (Metadata API: `SharingCriteriaRule`, `SharingOwnerRule`). For each rule, document the criteria, the target group/role, the access level (Read Only or Read/Write), and the approximate number of records currently matching the criteria. Flag any rule that matches more than 50% of records in an object, any rule granting Read/Write access to groups larger than a specific named team, and any rule with no documented business owner.

---

## Gotcha 5: Below API 67.0, Apex Batch Jobs and Future Methods Default to System Context Regardless of the Submitting User's Sharing

**What happens:** An Apex batch job is reviewed in isolation and appears safe — the calling Visualforce or LWC enforces sharing correctly. But the batch job itself is annotated with `Database.Batchable`, is saved at API 66.0 or earlier, and has no sharing declaration — so it runs in system context. Data exported or processed by the batch is not limited by the submitting user's role or sharing access.

**When it occurs:** Batch jobs, future methods (`@future`), queueable Apex, and scheduled Apex saved at **API 66.0 or earlier** all run without a user context unless explicitly declared `with sharing`. At **67.0+** that default inverted — an undeclared class runs `with sharing` and its queries and DML run in user mode — so at that version the finding is an explicit `without sharing` or `as system`, not a missing keyword. The gate is the `apiVersion` in each class's `.cls-meta.xml`, not the org's release, so a Summer '26 org still has this exposure in every class pinned to an older version; see [`agents/_shared/AGENT_CONTRACT.md`](../../../../agents/_shared/AGENT_CONTRACT.md) § *Apex security idiom by API version*. Developers writing asynchronous Apex often do not consider sharing at all, assuming the trigger that initiated the work enforced it. Reason about the trigger on two separate axes before accepting or rejecting that assumption. A trigger can't carry an explicit sharing declaration and always runs implicitly in a `without sharing` context — but the body is not blanket system mode: SOQL, SOSL, DML, and `Database` methods inside a trigger run in **user mode** unless system mode is explicitly specified, and that user mode reapplies the running user's record sharing, effectively overriding the trigger's `without sharing` context inside the body. So an unannotated query in a trigger is not automatically a finding; an explicit system-mode opt-out is — and under that opt-out only object- and field-level permissions are bypassed, with record sharing falling back to the trigger's `without sharing` context. Either way that context does not propagate across the async boundary: the queued, future, or scheduled class executes under its own sharing declaration and its own access mode, so score the async class on its own terms instead of crediting or blaming the trigger that enqueued it.

**Why it matters:** A user who can trigger a batch job export but should not have access to all records in the object can exploit the system-context execution to bypass sharing. This is particularly relevant for reporting jobs, data migration utilities, or integration batch classes that export records to external systems.

**How to avoid:** For every async Apex class in scope (batch, queueable, future, scheduled), confirm the sharing declaration. If the class is intentionally running in system context (e.g., it processes records owned by multiple users on behalf of an automated process), document that reason. If the class was simply never given a sharing declaration, assess whether it should inherit the context of the submitting user and add `with sharing` or `inherited sharing` accordingly.

---

## Gotcha 6: New Connected Apps Are Restricted as of Spring '26

**What happens:** A remediation plan says "create a dedicated connected app with narrower scopes for each integration". The Security Guide ("Connected Apps") says connected app creation is restricted as of Spring '26. Existing connected apps keep working, but Salesforce recommends external client apps instead, and creating new connected apps requires contacting Salesforce Support.

**When it occurs:** Remediation backlogs written from pre-2026 playbooks.

**How to avoid:** Write remediation items that split or re-scope integrations as external client app work. Keep reviewing existing connected apps (they remain the largest OAuth surface in most orgs) and record both inventories: `ConnectedApplication` and `ExternalClientApplication` (Object Reference).

---

## Gotcha 7: User Personal-Information Settings Are Not Enforced in Apex

**What happens:** An Experience Cloud org hides personal user details from other users with its user-visibility settings, and a custom component built on Apex still shows them. The Apex Developer Guide ("Enforce Object and Field Permissions", Considerations) says those settings are not enforced in Apex, even with `WITH USER_MODE` or `stripInaccessible`, and points to its example code for hiding User fields.

**When it occurs:** Custom LWC or Aura components on Experience Cloud pages that query `User` or show record owners.

**How to avoid:** List every Apex method that returns `User` fields to external users and check it against the guide's "Comply with a User's Personal Information Visibility Settings" pattern. Rate a missing check on an external page as High.

---

## Gotcha 8: The Automated Process User Cannot Run Object and FLS Checks Without Permission Sets

**What happens:** Code that runs as the Automated Process user (for example, platform event triggers and some flows) fails or behaves unexpectedly when it calls describe-based access checks. The Apex Developer Guide ("Enforce Object and Field Permissions", Considerations) says Automated Process users cannot perform object and FLS checks in custom code unless the right permission sets are explicitly applied to them.

**When it occurs:** Event-driven designs reviewed only under an admin's context.

**How to avoid:** For each async entry point, record the running user. Where it is the Automated Process user, confirm the permission sets assigned and test the access checks under that user.

---

## Gotcha 9: Setup Audit Trail Evidence Expires

**What happens:** An auditor asks for evidence of who granted Modify All Data last year, and Setup Audit Trail cannot show it. The Object Reference (`SetupAuditTrail`) says the object represents Setup changes for at least the last 180 days. It also does not support aggregate queries other than `count()`.

**When it occurs:** Annual reviews and post-incident investigations that start more than six months after the change.

**How to avoid:** Export `SetupAuditTrail` on a schedule to a retained store. For field-level history, check whether Field Audit Trail is licensed (Security Guide, "Field History Tracking": without it, field history is kept 18 months, 24 via the API).

---

## Gotcha 10: Visualforce Escapes by Default, So the Findings Are the Exceptions

**What happens:** A reviewer raises every Visualforce merge field as an XSS finding, burying the real issues. The Apex Developer Guide ("Security Tips for Apex and Visualforce Development") says nearly all Visualforce tags escape XSS-vulnerable characters by default. The exposures it names are components with `escape="false"` and formulas used outside a Visualforce component.

**When it occurs:** Checklist-driven reviews that apply item 14 literally.

**How to avoid:** Search Visualforce markup for `escape="false"` and for raw `{!...}` expressions outside components, especially those that read `$CurrentPage.parameters`. Rate those, not every merge field.

---

## Gotcha 11: "Protected" Configuration Is Only Protected Inside a Managed Package

**What happens:** The review accepts secrets stored in a protected custom setting in an unpackaged org. The Apex Developer Guide ("Custom Settings") says protection applies only to custom settings marked protected and installed as part of a managed package; otherwise they are public and readable by all profiles, including the guest user. It says to use named credentials or encrypted custom fields for secrets outside a managed package. The "Metadata" section says protected custom metadata can be read only by Apex in the same namespace. UNVERIFIED (2026-10-03): whether a protected custom metadata type created directly in an unpackaged org gives any protection was not confirmed.

**When it occurs:** Orgs that followed advice to "use protected custom metadata or settings for secrets" without a managed package.

**How to avoid:** Treat any secret in an unpackaged custom setting or custom metadata type as exposed. Move it to a named credential with an external credential and rotate it.

