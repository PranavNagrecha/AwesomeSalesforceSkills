# Gotchas — Guest User Security

## 1. `with sharing` Does NOT Prevent Field Exposure

**What happens:** A developer adds `with sharing` to a guest-facing Apex class and considers the security review complete. An internal audit later discovers that the class returns sensitive fields (BillingCity, AnnualRevenue) from Account records because `with sharing` only enforces which RECORDS are visible, not which FIELDS.

**Why:** `with sharing` enforces the sharing model (row visibility). It does not enforce field-level security. For a guest user the row set is whatever the guest user sharing rules grant — so on an object with a broad sharing rule, `with sharing` filters out almost nothing, and the class still returns every field on every matched record.

**How to avoid:** Combine `with sharing` with `WITH USER_MODE` in SOQL or explicit `Schema.SObjectType.Account.fields.AnnualRevenue.isAccessible()` checks. Return DTOs (data transfer objects) that explicitly whitelist returned fields.

---

## 2. Each Experience Cloud Site Has Its Own Guest User

**What happens:** An admin hardens the guest profile on Site A (removes Create/Edit permissions, tightens FLS). Six months later, Site B is launched and has a completely separate guest profile that inherited the org's default profile configuration — which still has Create, Edit, and access to sensitive fields.

**Why:** Every Experience Cloud site generates a distinct guest user and guest user profile. Changing the profile on one site does not affect other sites.

**How to avoid:** When any new Experience Cloud site is created, immediately audit its guest profile using the same hardening checklist applied to existing sites. Treat each new site as a separate security surface.

---

## 3. Permission Sets Assigned to the Guest User Are an Access Path Most Audits Miss

**What happens:** A developer needs to give guest users the ability to submit a specific type of form. Rather than modifying the guest profile, they create a permission set with Create access on a few objects and assign it to the guest user. Later, the permission set is expanded (by a different developer who doesn't realize it's on the guest user) to include access to Contact records. Guest users can now query Contact records.

**Why:** Permission sets on the guest user grant object, field and system permissions on top of the profile, and nothing about the guest user makes that union visible in one place.

Do not date this risk to Spring '22 — assigning permission sets to guest users predates that release, and the Spring '22 event was a *restriction*, not a grant. The actual timeline runs the other way:

- **Spring '21** — Edit, Delete, View All Records and Modify All Records can no longer be given to guest users at all, "even with a permission set or permission set group." Existing assignments carrying them were removed automatically.
- **Spring '22** — Salesforce began restricting assignment of guest users to permission sets and permission set groups associated with permission set *licences* that contain those restricted object permissions, and shipped a release update to prepare orgs for enforcement.
- **Winter '23** — that release update, "Remove Guest User Assignments from Permission Sets Associated with Permission Set Licenses with Restricted Object Permissions," was enforced and the affected assignments were auto-removed.

So the surviving exposure is narrower than "guests can be given anything through a permission set": read and create on standard objects is what remains reachable. That is still worth auditing — a permission set expanded by a developer who does not realise it is assigned to the guest user is exactly how read access to Contact leaks onto a public site.

**How to avoid:** Regularly audit permission set assignments to the guest user: `SELECT Id, PermissionSet.Name FROM PermissionSetAssignment WHERE AssigneeId = :guestUserId`. Treat the guest user's effective permission set as the union of profile + all assigned permission sets.

---

## 4. Secure Guest User Record Access Breaks Pre-Winter '21 Sharing Mechanisms

**What happens:** An org configured before Winter '21 granted guests access by adding the guest user to a public group or queue, by manual/Apex managed sharing, or by an ordinary sharing rule. After enforcement, guests can no longer see those records.

**Why:** Since Winter '21, "Secure guest user record access" is enabled in every org with Experience Cloud sites and can't be disabled. Guest org-wide defaults are Private for all objects and that access level can't be changed. Guests can't be members of public groups or queues, can't receive manual or Apex managed shares, and can't own records. The only surviving grant path is a **guest user sharing rule** — a criteria-based rule that grants Read Only.

**How to avoid:** Replace each broken grant with a guest user sharing rule whose criteria match only the genuinely public records. Do **not** raise the object's OWD: guest visibility is not evaluated against it, so the change grants guests nothing while widening exposure for authenticated internal users. Also remove the guest user from any group or queue by hand — legacy memberships are not cleaned up automatically. Keep `WITH USER_MODE` in Apex for field enforcement; the sharing-rule criteria remain the row-level backstop.
