# Gotchas — Security Architecture Review

## 1. External OWD Is Independent of Internal OWD and Defaults to the Internal Setting

**What happens:** A reviewer confirms that the `Contact` object OWD is set to "Private" for internal users and marks the sharing model as secure. External users on an Experience Cloud site can still read all Contacts because the External OWD was never explicitly set and defaulted to match an older, more permissive internal OWD from before it was tightened.

**When it occurs:** Any org with an Experience Cloud site where the internal OWD was changed after the site was configured. The external OWD does not automatically inherit changes to the internal OWD.

**Why it matters:** External users include portal customers, partners, and in some architectures, authenticated API consumers using community licenses. A "Private" internal OWD with an open external OWD means the sharing model is only private for internal employees — external parties can access data broadly.

**What to do:** In Setup > Sharing Settings, review both the "Default Internal Access" and "Default External Access" columns for every object with sensitive data. Confirm they are both intentional and documented. Pay special attention to `Contact`, `Account`, `Case`, and any custom objects with PII or regulated data. If the org has no Experience Cloud sites, external OWD is irrelevant, but document that fact in the review.

---

## 2. `with sharing` Does Not Enforce FLS — It Only Enforces Record Visibility

**What happens:** A developer declares `with sharing` on a class and a reviewer marks all FLS checklist items as "pass" because the class "enforces sharing." The class still returns field values for fields the running user has no FLS read access to, because SOQL in a `with sharing` class retrieves all requested fields regardless of FLS unless an explicit FLS enforcement mechanism is used.

**When it occurs:** Consistently throughout orgs that learned Apex security from older training materials that equated sharing enforcement with security. The `with sharing` keyword controls record-level sharing only. FLS is entirely separate.

**Why it matters:** A user with read access to an Account record but no FLS read on `Account.AnnualRevenue__c` will still receive that field value if the Apex query includes it and the class only declares `with sharing`.

**What to do:** For every Apex class identified in the review, check for FLS enforcement separately from sharing enforcement. The valid mechanisms are:
- `WITH SECURITY_ENFORCED` clause in SOQL (throws an exception if the user lacks field access; does not support sub-queries well)
- `WITH USER_MODE` on the DML or query statement (API 56.0+, Summer '22; recommended for new code)
- `Security.stripInaccessible(AccessType.READABLE, records)` before returning data

Mark any class that queries sensitive fields in `with sharing` without FLS enforcement as a High finding.

---

## 3. Connected App "IP Relaxation" Is Not the Same as "Trusted IP Range"

**What happens:** A reviewer sees a Named Credential or Connected App and notes "IP range is configured" and marks the IP restriction check as passing. The Connected App actually has "Relax IP restrictions" selected (not a restricted IP range), which means it accepts connections from any IP address — the opposite of what the reviewer assumed.

**When it occurs:** The Salesforce UI uses similar language for two opposing settings. "Relax IP restrictions" means "bypass IP restrictions." Trusted IP ranges configured on the org or profile are separate from Connected App IP policies.

**Why it matters:** A Connected App with IP relaxation enabled combined with a long-lived refresh token provides an attacker who has stolen a refresh token unrestricted access from any location, bypassing org-level IP range restrictions entirely.

**What to do:** In Setup > Apps > Connected Apps > Manage Connected Apps, review the "IP Relaxation" column for each app. The setting should be "Enforce IP restrictions" unless there is a documented business requirement for global access. Document each app's setting and the justification for any relaxation in the review report.

---

## 4. Criteria-Based Sharing Rules Can Grant Broader Access Than Intended as Data Changes

**What happens:** A criteria-based sharing rule was created that shares all Opportunity records where `Stage != 'Closed Won'` with the Sales Operations role. Over time, the pipeline grows and 95% of Opportunity records match the criteria. When a deal closes, it falls out of the share rule but all related notes, attachments, and child records that were accessed during the deal lifecycle may have already been exported or cached.

**When it occurs:** Criteria-based rules that use negative conditions (`!=`, `NOT IN`) effectively share most records rather than a targeted subset. Rules that were designed for a small org can become overly permissive at scale without anyone explicitly changing a configuration.

**Why it matters:** Unlike role hierarchy visibility, criteria-based sharing rules are not visible in standard reports or dashboards. They require a deliberate audit to understand their scope. An org that has accumulated 50+ sharing rules over five years may have contradictory or overlapping rules that no one has reviewed since they were created.

**What to do:** Export all sharing rules from the org (Metadata API: `SharingCriteriaRule`, `SharingOwnerRule`). For each rule, document the criteria, the target group/role, the access level (Read Only or Read/Write), and the approximate number of records currently matching the criteria. Flag any rule that matches more than 50% of records in an object, any rule granting Read/Write access to groups larger than a specific named team, and any rule with no documented business owner.

---

## 5. Apex Batch Jobs and Future Methods Default to System Context Regardless of the Submitting User's Sharing

**What happens:** An Apex batch job is reviewed in isolation and appears safe — the calling Visualforce or LWC enforces sharing correctly. But the batch job itself is annotated with `Database.Batchable` and has no sharing declaration, meaning it runs in system context. Data exported or processed by the batch is not limited by the submitting user's role or sharing access.

**When it occurs:** Batch jobs, future methods (`@future`), queueable Apex, and scheduled Apex all run without a user context unless explicitly declared with `with sharing`. Developers writing asynchronous Apex often do not consider sharing because the trigger that initiates the async work correctly enforces sharing.

**Why it matters:** A user who can trigger a batch job export but should not have access to all records in the object can exploit the system-context execution to bypass sharing. This is particularly relevant for reporting jobs, data migration utilities, or integration batch classes that export records to external systems.

**What to do:** For every async Apex class in scope (batch, queueable, future, scheduled), confirm the sharing declaration. If the class is intentionally running in system context (e.g., it processes records owned by multiple users on behalf of an automated process), document that reason. If the class was simply never given a sharing declaration, assess whether it should inherit the context of the submitting user and add `with sharing` or `inherited sharing` accordingly.
