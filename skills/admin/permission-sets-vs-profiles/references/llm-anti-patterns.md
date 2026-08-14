# LLM Anti-Patterns — Permission Sets vs Profiles

Common mistakes AI coding assistants make when generating or advising on the Salesforce Profiles vs Permission Sets decision.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending profile cloning as the default access model

**What the LLM generates:** "Clone the Standard User profile for each department: Sales User, Service User, Marketing User."

**Why it happens:** LLMs trained on older Salesforce practices treat profiles as the primary access mechanism. Profile cloning creates drift -- each clone diverges over time as admins make one-off changes. Salesforce's direction is toward minimal profiles with additive permission sets.

**Correct pattern:**

```
Modern access model:
1. Minimal base profile(s): 1-3 profiles for the whole org.
   - Salesforce License base: Minimum Access - Salesforce.
   - Platform License base: Minimum Access - Platform.
   - Admin: System Administrator.
2. Profiles handle ONLY:
   - Login hours, IP restrictions.
   - Page layout assignments.
   - Default record type.
   - Default app.
3. ALL CRUD, FLS, and feature permissions → Permission Sets.
4. Compose permission sets into Permission Set Groups per persona.
5. Never clone profiles to differentiate department access.
```

**Detection hint:** If the output says "clone the profile" as the solution for different department access, it is using the legacy model. Search for `clone` combined with `profile`.

---

## Anti-Pattern 2: Treating the Spring '26 "permissions in profiles" retirement as a live deadline

**What the LLM generates:** "Permissions in profiles reach end of life in Spring '26 — decompose every profile before the upgrade or your users lose access." Or the stronger version: "Salesforce is removing profiles in the next release."

**Why it happens:** Salesforce announced the retirement in 2023, and models trained before mid-2026 still carry it as settled fact. Salesforce **cancelled** the enforcement on 6 Jun 2026, citing customer feedback and remaining feature gaps, and published no replacement end-of-life date. Profiles themselves were never scheduled for removal. Both the deadline and the urgency built on top of it are fabricated, and a migration plan sold on that deadline is a plan the customer did not need to fund this quarter.

**Correct pattern:**

```
Profile status (as of Summer '26):
- Permissions in profiles: retirement CANCELLED
  (Salesforce Help 003834041, 6 Jun 2026). No new end-of-life date.
  Existing profile grants keep working; nothing breaks on upgrade.
- Salesforce still RECOMMENDS a permission-set-led model.
  Recommendation, not cutoff.
- Profiles remain the home for these settings:
  - Default assigned apps.
  - Default record types and page layouts.
  - Login hours.
  - Login IP ranges.
  - Password policies.
  - Session settings.
- Strategy: move CRUD/FLS/features to permission sets because it is
  easier to audit, assign and unwind — sequenced on business value.
  Do not promise it as compliance with a release deadline.
```

**Detection hint:** If the output attaches a release name ("Spring '26"), "end of life," or "must migrate before" to profile permissions, it is quoting a cancelled retirement. Search for `retire`, `end of life`, or `Spring '26` near `profile`.

---

## Anti-Pattern 3: Not understanding that permission sets are additive only

**What the LLM generates:** "Use a permission set to remove the Delete permission that the profile grants."

**Why it happens:** LLMs treat permission sets as bidirectional (grant and revoke). Permission sets can ONLY add permissions. They cannot revoke a permission granted by the profile or another permission set. The only way to remove a permission is to remove it from the profile or use a muting permission set within a Permission Set Group.

**Correct pattern:**

```
Permission sets are ADDITIVE ONLY:
- If the profile grants Delete on Account, a permission set
  CANNOT revoke it.
- To restrict a permission:
  1. Remove it from the profile (so no one has it by default).
  2. Grant it via a permission set only to users who need it.
  3. Or use a Muting Permission Set inside a Permission Set Group
     to suppress specific permissions for a persona.

Muting example:
  PSG: Junior Sales = [Base_Sales_PS] + [Mute_Delete_PS]
  Where Mute_Delete_PS suppresses Delete on Account within this PSG.
```

**Detection hint:** If the output uses a permission set to "remove," "revoke," or "restrict" a permission, it misunderstands the additive model. Search for `remove`, `revoke`, or `restrict` combined with `permission set`.

---

## Anti-Pattern 4: Ignoring the interaction between profiles and permission sets for FLS

**What the LLM generates:** "Grant FLS on the Salary field via a permission set. Only users with this permission set can see it."

**Why it happens:** The LLM assumes FLS is exclusively controlled by the permission set. If the profile ALSO grants visibility to the field, the permission set is redundant — and removing the permission set will not hide the field if the profile still grants it. FLS is the UNION of profile and all assigned permission sets.

**Correct pattern:**

```
FLS is the UNION of all grants:
- If Profile grants Read on Salary__c → user can see it.
- If Permission Set grants Read on Salary__c → user can see it.
- If EITHER grants it → user has access.
- To truly restrict a field:
  1. Remove FLS from ALL profiles that should not see it.
  2. Grant FLS ONLY via a permission set assigned to authorized users.
  3. Verify with Field Accessibility viewer:
     Setup → Object Manager → [Object] → Fields → [Field] → Field Accessibility.
```

**Detection hint:** If the output grants FLS via a permission set without also checking/removing the same FLS from the profile, the field may be visible to unintended users. Search for `profile` FLS verification alongside `permission set` FLS grants.

---

## Anti-Pattern 5: Not considering managed package profiles in the migration plan

**What the LLM generates:** "Migrate all profiles to the minimal profile model. Replace all CRUD/FLS with permission sets."

**Why it happens:** LLMs produce clean migration plans that ignore managed package constraints. Some managed packages require specific profile configurations (e.g., certain profiles must have object access for the package to function). Removing CRUD from profiles may break managed package functionality.

**Correct pattern:**

```
Managed package considerations:
1. Before migrating to minimal profiles, inventory managed packages:
   - Which packages have profile-dependent configurations?
   - Do any packages require specific profile CRUD/FLS?
2. Check package installation guides for profile requirements.
3. Test the minimal profile model in a sandbox with all
   managed packages installed.
4. Some packages ship their own Permission Sets — use those
   instead of profile-level grants.
5. Contact the ISV if unclear whether their package supports
   the permission-set-based access model.
```

**Detection hint:** If the output migrates all profiles to minimal without mentioning managed package impact, package functionality may break. Search for `managed package` or `ISV` in the migration plan.
