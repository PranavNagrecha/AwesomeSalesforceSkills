# Examples — Experience Cloud Security

## Example 1: Sharing Set for Customer Portal Case Access

**Context:** A financial services company launched a Customer Community portal where account holders can submit and track service cases. After launch, support staff discovered portal users could not see their own cases even though cases existed linked to their Account.

**Problem:** External OWD for Case was set to Private (correct), but no Sharing Set was configured. Portal users had no mechanism to access records linked to their Account.

**Solution:**
1. Navigate to Setup > Sharing Settings > Sharing Sets.
2. Create a new Sharing Set named "Customer Portal Case Access".
3. Set the associated site to the Customer Community Experience Cloud site.
4. Under "Access Mapping", add: Object = Case, Access = Read Only, User = User.ContactId.AccountId, Target = Case.AccountId.
5. Save.

Portal users can now read all Cases where `Case.AccountId` matches their Account.

**Why it works:** Sharing Sets create a relationship-based sharing path without requiring internal OWD to be made more permissive. The lookup chain (`User.Contact.Account → Case.Account`) is evaluated at query time and grants least-privilege access scoped to the portal user's relationship.

---

## Example 2: Guest User Hardening After Security Audit

**Context:** An Experience Cloud site was initially built to serve authenticated external users but inadvertently had guest user access enabled. A security audit found that guest users could access Contact records because the guest profile had "Read" on Contact and Contact external OWD was Public Read Only.

**Problem:** Guest users (unauthenticated visitors hitting the site URL) could browse Contact data that should require authentication.

**Solution:**
1. Enable "Secure Guest User Record Access" in Setup > Sharing Settings (if not already enabled).
2. Set external OWD for Contact to Private.
3. Open the Guest User profile for the site, remove "Read" permission on Contact.
4. Run SOQL query to verify: `SELECT Id, IsActive FROM User WHERE Profile.Name LIKE '%Guest%'` — confirm guest users exist and then test access.
5. If the site requires guest access for a subset of objects (e.g., Knowledge articles), create explicit guest sharing rules only for those objects.

**Why it works:** "Secure Guest User Record Access" forces all objects to private for guest users at the platform level, overriding any broader external OWD. Combined with removing object permissions from the guest profile, unauthenticated users are fully isolated from record data.

---

## Anti-Pattern: Setting External OWD More Permissive Than Internal OWD

**What practitioners do:** Set Case internal OWD to Private for internal data protection, then attempt to set external OWD to Public Read Only to give portal users broad case access without Sharing Sets.

**What goes wrong:** Salesforce does not allow external OWD to be more permissive than internal OWD. The UI may appear to accept the setting, but the effective external OWD is capped at the internal OWD value. Portal users get no broader access than internal users with equivalent profiles. The developer is confused because Setup shows different values for internal vs external OWD.

**Correct approach:** Set internal OWD appropriately for internal users first. Use Sharing Sets or explicit sharing rules to give portal users relationship-based access to records beyond their profile permissions. External OWD should be equal to or more restrictive than internal OWD — never use it as a mechanism to grant broader external access.
