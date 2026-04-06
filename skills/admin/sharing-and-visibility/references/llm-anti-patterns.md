# LLM Anti-Patterns — Sharing and Visibility

Common mistakes AI coding assistants make when generating or advising on Salesforce sharing and record-level visibility.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Confusing OWD with FLS or CRUD permissions

**What the LLM generates:** "Set the OWD to Private to prevent users from editing Account fields they should not see."

**Why it happens:** LLMs conflate record-level access (OWD, sharing rules, role hierarchy) with field-level access (FLS) and object-level access (CRUD). OWD controls which records a user can see, not which fields on those records are visible. FLS controls field visibility. CRUD controls whether the user can create, read, update, or delete records on the object.

**Correct pattern:**

```
Three layers of Salesforce access:
1. Object-level (CRUD): can the user Create/Read/Update/Delete on this object?
   Controlled by: Profiles and Permission Sets.
2. Field-level (FLS): can the user see or edit this specific field?
   Controlled by: Field-Level Security on Profiles and Permission Sets.
3. Record-level (sharing): which specific records can the user see?
   Controlled by: OWD, Role Hierarchy, Sharing Rules, Manual Sharing,
   Apex Sharing, Teams.

A user needs ALL THREE layers to grant access:
- Object Read (CRUD) + Field Visible (FLS) + Record Access (Sharing).
Missing any layer blocks access.
```

**Detection hint:** If the output uses OWD to control field visibility or uses FLS to control record access, the layers are being confused. Search for `OWD` combined with `field` or `FLS` combined with `record access`.

---

## Anti-Pattern 2: Using manual sharing as a primary access model

**What the LLM generates:** "Manually share the record with each user who needs access."

**Why it happens:** LLMs solve individual access requests with manual sharing. Manual sharing is designed for exceptions, not as a scalable access model. It does not survive ownership changes (manual shares are removed when the owner changes), creates unauditable access, and requires individual intervention for every access request.

**Correct pattern:**

```
Sharing mechanisms by scalability:
1. OWD + Role Hierarchy: baseline access for all users. Set once.
2. Sharing Rules: criteria-based or owner-based. Automated, auditable.
   Use for repeatable access patterns (e.g., all West region Accounts
   shared with West Sales team).
3. Teams (Account Teams, Opportunity Teams, Case Teams):
   semi-automated, user-managed team membership.
4. Apex Sharing (programmatic): for complex conditional sharing
   not possible with declarative rules.
5. Manual Sharing: for one-off exceptions only.
   Does NOT survive ownership changes.

If you need manual sharing more than occasionally, the sharing
model is under-designed. Add a sharing rule or team configuration.
```

**Detection hint:** If the output uses manual sharing as the solution for a repeatable access pattern, the model is under-designed. Search for `manual share` or `Share button` as the primary access mechanism.

---

## Anti-Pattern 3: Assuming role hierarchy always grants visibility

**What the LLM generates:** "The VP of Sales can see all Opportunities because they are above the Sales Reps in the role hierarchy."

**Why it happens:** LLMs assume role hierarchy always opens up access. The "Grant Access Using Hierarchies" setting can be disabled on custom objects (not standard objects). When disabled, higher roles do NOT automatically see records owned by lower roles. Additionally, for some objects, the setting may be intentionally turned off for compliance reasons.

**Correct pattern:**

```
Role hierarchy access rules:
- Standard objects (Account, Contact, Opportunity, Case):
  "Grant Access Using Hierarchies" is always ON and cannot be disabled.
  Managers always see their subordinates' records.
- Custom objects:
  "Grant Access Using Hierarchies" can be disabled per object.
  Setup → Sharing Settings → [Object] → "Grant Access Using Hierarchies" checkbox.
  If unchecked: role hierarchy does NOT open record access.
- When disabled: the VP of Sales does NOT automatically see
  custom object records owned by subordinate reps.

Check this setting before assuming hierarchy-based visibility.
```

**Detection hint:** If the output assumes role hierarchy grants access to a custom object without checking the "Grant Access Using Hierarchies" setting, the access may not exist. Search for `Grant Access Using Hierarchies` when custom objects are involved.

---

## Anti-Pattern 4: Opening OWD to Public to solve a specific access problem

**What the LLM generates:** "Change the Account OWD to Public Read/Write so the marketing team can see all accounts."

**Why it happens:** LLMs solve specific access requests by widening the OWD to the most permissive level. Changing OWD to Public Read/Write means EVERYONE can see and edit every record. The correct approach is a targeted sharing rule that grants access to the marketing team without opening access to everyone.

**Correct pattern:**

```
Solve specific access needs with sharing rules, not OWD changes:
1. Keep OWD restrictive (Private or Public Read Only).
2. Create a criteria-based or owner-based sharing rule:
   - Share Accounts WHERE Region = 'All' WITH Marketing Group → Read.
   - Or: Share Accounts OWNED BY Sales Reps WITH Marketing Group → Read.
3. If the marketing team needs access to ALL Accounts:
   - Consider Public Read Only (not Read/Write) as the OWD.
   - Or create a sharing rule sharing all Accounts with the marketing
     public group (but this may have performance implications at scale).
4. NEVER change OWD to Public Read/Write to solve a single team's access need.
```

**Detection hint:** If the output changes OWD to Public to solve one team's access need, the solution is over-broad. Search for `OWD` change combined with a specific team or user group name.

---

## Anti-Pattern 5: Forgetting that sharing rule changes trigger recalculation

**What the LLM generates:** "Add a new sharing rule for the 500,000 Account records. Access will be granted immediately."

**Why it happens:** LLMs describe sharing rules as instant. Adding or modifying a sharing rule triggers a sharing recalculation across all affected records. For large data volumes, this recalculation can take hours and may cause lock contention, slow page loads, and "unable to lock row" errors during the processing window.

**Correct pattern:**

```
Sharing rule change impact:
1. Adding or modifying a sharing rule triggers asynchronous recalculation.
2. Recalculation time depends on:
   - Number of records affected.
   - Number of existing sharing rules.
   - Depth of role hierarchy.
   - Current org load.
3. For large orgs (100K+ records):
   - Schedule sharing rule changes during off-peak hours.
   - Monitor: Setup → Sharing Settings → check for "Recalculation in Progress."
   - Consider using "Defer Sharing Calculations" (available via Salesforce Support)
     to batch multiple changes before recalculating.
4. During recalculation, some users may temporarily see more or fewer
   records than expected. Communicate the maintenance window.
```

**Detection hint:** If the output adds a sharing rule on a large-volume object without mentioning recalculation time or scheduling, the performance impact is being ignored. Search for `recalculation`, `off-peak`, or `defer` in the sharing rule instructions.
