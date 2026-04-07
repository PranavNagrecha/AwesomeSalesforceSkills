# Gotchas — External User Data Sharing

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Sharing Sets Have No Effect on Customer Community Plus or Partner Community Users

**What happens:** A Sharing Set is created and associated with a Customer Community Plus or Partner Community profile. The Sharing Set saves without error. When a CC Plus or Partner Community test user logs in, the records the Sharing Set was intended to grant access to are not visible.

**When it occurs:** Any time a Sharing Set configuration includes a non-HVP profile. This is easy to do accidentally when an org has multiple community license types and a practitioner copies a Sharing Set configuration for a new user type without checking the license.

**How to avoid:** Confirm the target profile is a High-Volume Portal (Customer Community) profile before creating a Sharing Set. CC Plus and Partner Community users must receive access through criteria-based sharing rules, external sharing rules, or manual sharing. Sharing Sets are exclusively for HVP.

---

## Gotcha 2: External OWD Inherits Internal OWD Value by Default — Not Private

**What happens:** When an org first enables Experience Cloud or adds a new object to the sharing model, the External OWD for that object defaults to the current internal OWD value, not to Private. If internal OWD is Public Read Only, external users immediately inherit that access level with no explicit action by an admin.

**When it occurs:** Occurs silently on org setup, when a new custom object is created (and External OWD defaults to internal), and when an admin adds a new community to an org that already has permissive internal OWD settings. It is frequently discovered during a security review after go-live.

**How to avoid:** Immediately after enabling Experience Cloud or adding a new object, audit Setup > Security > Sharing Settings for the External Access column. Explicitly set External OWD to Private on every object where external users should not have blanket access, then grant access selectively via Sharing Sets or sharing rules.

---

## Gotcha 3: Changing External OWD Triggers an Org-Wide Sharing Recalculation

**What happens:** Any change to External OWD for any object queues a background sharing recalculation job that processes all records in the org. For orgs with large data volumes, this job can run for hours. During recalculation, external user access to records may be temporarily inconsistent — users may see records they should not, or fail to see records they should.

**When it occurs:** Every External OWD change, including changes that appear minor (e.g., Private → Public Read Only on a low-volume object). The recalculation scope is org-wide, not scoped to the affected object alone.

**How to avoid:** Plan External OWD changes during low-traffic maintenance windows. Monitor Setup > Background Jobs for the recalculation status. Do not consider the access configuration live until the job shows "Completed." For large data volume orgs, estimate recalculation time in advance and coordinate with stakeholders.

---

## Gotcha 4: Portal Users Only See Their Own Account's Records When External OWD Is Private

**What happens:** A practitioner sets External OWD to Private on an object, then expects that portal users can browse all records of that type regardless of account. Users log in and see nothing.

**When it occurs:** Misunderstanding of how Private external OWD interacts with the portal sharing model. Private means a user can only see records explicitly shared with them. Without a Sharing Set or sharing rule, no records are shared, so nothing appears.

**How to avoid:** Treat Private External OWD as the starting point, then build explicit sharing. For HVP users, add a Sharing Set with the correct relationship path. For CC Plus/Partner, add criteria-based or manual sharing rules. Confirm the complete chain: OWD → Sharing mechanism → Relationship path → Access level.

---

## Gotcha 5: Sharing Set Relationship Path Must Match the Field on the Object — Mismatches Grant No Access

**What happens:** A Sharing Set is configured with the relationship path `User.ContactId → Case.ContactId`. However, the Cases in the org are linked to the Account, not the Contact (the `ContactId` field on Case is null). The Sharing Set evaluates the relationship, finds no matching records, and grants no access. No error is raised.

**When it occurs:** When practitioners assume the portal user's Contact is directly on the record, but the actual relationship is through the Account. Also occurs when a custom object has a non-standard field name that differs from the expected relationship field.

**How to avoid:** Before configuring the Sharing Set relationship path, inspect actual data to confirm which field links the target object to the user's Account or Contact. Run a SOQL query to verify the field is populated: `SELECT Id, AccountId, ContactId FROM Case WHERE AccountId != null LIMIT 5`. Use `AccountId` if Cases are linked to accounts; use `ContactId` only if Cases are consistently linked directly to contacts.
