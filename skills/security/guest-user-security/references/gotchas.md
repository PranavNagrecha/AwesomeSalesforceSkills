# Gotchas — Guest User Security

## 1. `with sharing` Does NOT Prevent Field Exposure

**What happens:** A developer adds `with sharing` to a guest-facing Apex class and considers the security review complete. An internal audit later discovers that the class returns sensitive fields (BillingCity, AnnualRevenue) from Account records because `with sharing` only enforces which RECORDS are visible, not which FIELDS.

**Why:** `with sharing` enforces the sharing model (row visibility). It does not enforce field-level security. On Public OWD objects, all records are visible to the guest user, so `with sharing` has no effect on rows either. The class can still return every field on every record.

**How to avoid:** Combine `with sharing` with `WITH USER_MODE` in SOQL or explicit `Schema.SObjectType.Account.fields.AnnualRevenue.isAccessible()` checks. Return DTOs (data transfer objects) that explicitly whitelist returned fields.

---

## 2. Each Experience Cloud Site Has Its Own Guest User

**What happens:** An admin hardens the guest profile on Site A (removes Create/Edit permissions, tightens FLS). Six months later, Site B is launched and has a completely separate guest profile that inherited the org's default profile configuration — which still has Create, Edit, and access to sensitive fields.

**Why:** Every Experience Cloud site generates a distinct guest user and guest user profile. Changing the profile on one site does not affect other sites.

**How to avoid:** When any new Experience Cloud site is created, immediately audit its guest profile using the same hardening checklist applied to existing sites. Treat each new site as a separate security surface.

---

## 3. Guest Users Can Be Assigned Permission Sets Since Spring '22

**What happens:** A developer needs to give guest users the ability to submit a specific type of form. Rather than modifying the guest profile, they create a permission set with Create access on a few objects and assign it to the guest user. Later, the permission set is expanded (by a different developer who doesn't realize it's on the guest user) to include access to Contact records. Guest users can now query Contact records.

**Why:** Salesforce added permission set assignment to guest users in Spring '22. Permission sets on the guest user can grant object, field, and even system permissions beyond what the profile provides.

**How to avoid:** Regularly audit permission set assignments to the guest user: `SELECT Id, PermissionSet.Name FROM PermissionSetAssignment WHERE AssigneeId = :guestUserId`. Treat the guest user's effective permission set as the union of profile + all assigned permission sets.

---

## 4. Secure Guest User Record Access Toggle Breaks Pre-Spring '21 Sites

**What happens:** An org that was configured before Spring '21 with Private OWD on an object and guest sharing rules (granting Read access to specific records) stops working after upgrading. Guest users can no longer see the records they previously accessed via sharing rules.

**Why:** Spring '21 made "Secure Guest User Record Access" mandatory. This toggle enforces OWD-based access for guest users — Private OWD records are completely hidden from guests regardless of sharing rules. The sharing rules from before Spring '21 are still present in the org but have no effect for Private OWD objects.

**How to avoid:** For sites that need guest users to access records, change the OWD for those objects to Public Read Only. Use Apex filtering (WITH USER_MODE + where clauses) to restrict which Public records the guest actually sees.
