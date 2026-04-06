# LLM Anti-Patterns — Permission Set Architecture

Common mistakes AI coding assistants make when generating or advising on Salesforce permission set architecture design.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Creating permission sets that mirror job titles instead of capabilities

**What the LLM generates:** "Create permission sets: Sales_Rep_PS, Sales_Manager_PS, Service_Agent_PS, Marketing_User_PS."

**Why it happens:** LLMs map permission sets 1:1 to job titles, recreating the profile sprawl problem that permission sets are meant to solve. When a Sales Manager needs Service Cloud access, the admin clones the manager permission set instead of composing capability-based sets.

**Correct pattern:**

```
Design permission sets around capabilities, not job titles:
- Sales_Read_Write (CRUD on Opportunity, Quote, Lead, Contact)
- Service_Read_Write (CRUD on Case, Entitlement, Knowledge)
- Reports_Advanced (create custom report types, export)
- Discount_Approval (custom permission for discount override)
- API_Access (API Enabled permission)

Compose via Permission Set Groups per persona:
  PSG: Sales Rep = Sales_Read_Write + Reports_Advanced
  PSG: Sales Manager = Sales_Read_Write + Reports_Advanced + Discount_Approval
  PSG: Service Agent = Service_Read_Write + Reports_Advanced
```

**Detection hint:** If permission set names match job titles rather than capabilities, the architecture recreates profile sprawl. Check if permission set names contain role/title words (Rep, Manager, Agent, Director) instead of capability words (Read, Write, Access, Approval).

---

## Anti-Pattern 2: Ignoring Permission Set Groups and muting permission sets

**What the LLM generates:** "Assign all five permission sets individually to each user."

**Why it happens:** LLMs assign permission sets directly to users, skipping Permission Set Groups (PSGs). PSGs bundle multiple permission sets into a single assignable unit, reducing administrative overhead. Muting permission sets within PSGs can selectively suppress permissions for specific personas without creating duplicate permission sets.

**Correct pattern:**

```
Permission Set Group architecture:
1. Create capability-based Permission Sets (atomic units).
2. Create Permission Set Groups per persona:
   PSG: Field Sales = [Base_Sales, Reports, Mobile_Access]
   PSG: Inside Sales = [Base_Sales, Reports, Dialer_Access]
3. Muting Permission Set (optional):
   - If Inside Sales should NOT have export-to-Excel from Reports:
     Create a Muting PS that suppresses "Export Reports" permission.
     Add the Muting PS to the Inside Sales PSG.
4. Assign ONE PSG per persona, not 5 individual permission sets.
5. When a new capability is needed: add it to the PSG, not to
   each user individually.
```

**Detection hint:** If the output assigns multiple individual permission sets to users without using Permission Set Groups, the architecture misses the grouping benefit. Search for `Permission Set Group` or `PSG` in the design.

---

## Anti-Pattern 3: Putting all permissions in profiles instead of moving to permission sets

**What the LLM generates:** "Clone the Standard User profile and add the required object permissions for each team."

**Why it happens:** LLMs trained on older Salesforce practices default to profile cloning. Salesforce has been moving toward minimal profiles with additive permission sets. Profile cloning creates drift (each clone diverges over time) and makes access audits difficult.

**Correct pattern:**

```
Minimal profile strategy:
1. Use 1-3 base profiles across the org:
   - Minimum Access (Salesforce license) — no CRUD, no tabs.
   - Minimum Access (Platform license) — for Platform-only users.
   - System Administrator — for admins only.
2. All feature permissions are additive via Permission Sets.
3. Profiles retain only:
   - Login hours and IP restrictions.
   - Page layout assignments.
   - Default record type assignments.
   - Default app assignment.
4. Never clone a profile to add CRUD/FLS — create a Permission Set instead.
```

**Detection hint:** If the output clones profiles for different teams or adds CRUD/FLS to profiles instead of permission sets, the design is profile-centric. Search for `clone profile` or CRUD permissions being set on profiles.

---

## Anti-Pattern 4: Not considering license restrictions when composing permission sets

**What the LLM generates:** "Create a permission set that enables Service Cloud features and assign it to all users."

**Why it happens:** LLMs ignore that some permissions require specific user licenses or feature licenses. A permission set enabling Knowledge or Entitlements requires the Service Cloud User feature license. Assigning a permission set with permissions beyond the user's license causes an assignment error.

**Correct pattern:**

```
License-aware permission set design:
1. Check which license each permission requires:
   - Knowledge: requires Knowledge User feature license.
   - Marketing: requires Marketing User feature license.
   - Service Console: requires Service Cloud User feature license.
   - CRM Analytics: requires CRM Analytics permission set license.
2. If a permission set requires a feature license:
   - Assign the feature license to the user FIRST.
   - Then assign the permission set.
3. Some Permission Set Licenses are required for specific permission sets.
   Check: Setup → Permission Set Licenses for available licenses.
4. Document license dependencies on each permission set for the admin team.
```

**Detection hint:** If the output creates permission sets with Service Cloud, Knowledge, or Marketing permissions without mentioning the required feature license, the assignment will fail. Search for `feature license` or `Permission Set License` in the design.

---

## Anti-Pattern 5: Creating one massive permission set instead of composable atomic sets

**What the LLM generates:** "Create a permission set called 'All_Sales_Permissions' that includes every object, field, and feature a sales user needs."

**Why it happens:** LLMs optimize for fewer moving parts. A single large permission set is hard to reuse, hard to audit, and creates a monolithic access model. When a new team needs 80% of the same permissions, the admin clones the set, creating the same drift problem as profile cloning.

**Correct pattern:**

```
Atomic permission set design:
1. One permission set per logical capability (5-15 permissions each).
   - Sales_Object_CRUD: Opportunity, Quote, Lead, Contact CRUD.
   - Discount_Override: custom permission for discount approval.
   - Report_Builder: create/edit reports and dashboards.
   - API_Enabled: API access for integration-connected users.
2. Each permission set should make sense as a standalone grant.
3. Compose permission sets into PSGs for each persona.
4. When a new team needs similar access: reuse existing sets,
   add or mute individual capabilities in the PSG.
5. Audit rule: if a permission set has > 20 object permissions
   or > 50 field permissions, it is too large. Break it apart.
```

**Detection hint:** If a single permission set grants CRUD on more than 5 objects or has more than 50 FLS entries, it is too monolithic. Count the object and field permissions in the set.
