# LLM Anti-Patterns — User Management

Common mistakes AI coding assistants make when generating or advising on Salesforce user management.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Deleting users instead of deactivating them

**What the LLM generates:** "Delete the user record for the departing employee to remove their access."

**Why it happens:** LLMs apply standard database logic (delete the row). Salesforce does not allow deleting user records. Users must be deactivated, which removes login access while preserving the user record for audit history, record ownership, and referential integrity. Deactivated users do not consume a license.

**Correct pattern:**

```
User offboarding:
1. Deactivate the user: Setup → Users → [User] → Edit → uncheck "Active."
2. The user can no longer log in.
3. The user record remains for:
   - Audit trail (setup changes, login history).
   - Record ownership (records still show the former owner).
   - Created By / Last Modified By references.
4. Reassign ownership: transfer the user's records BEFORE or AFTER
   deactivation using "Transfer Records" or mass transfer.
5. If urgently needed before deactivation: Freeze the user first
   (blocks login immediately without triggering ownership rules).
6. License is freed upon deactivation.
```

**Detection hint:** If the output says "delete the user," it is incorrect. Salesforce does not support user deletion. Search for `delete` combined with `user` — the correct term is `deactivate`.

---

## Anti-Pattern 2: Assigning the System Administrator profile to non-admin users

**What the LLM generates:** "Give the user the System Administrator profile so they can see everything they need."

**Why it happens:** LLMs solve access problems by over-provisioning. The System Administrator profile grants full access to all data, metadata, setup, and API access. Assigning it to a non-admin user violates least privilege, exposes the org to accidental configuration changes, and creates audit compliance issues.

**Correct pattern:**

```
Profile assignment based on least privilege:
1. Assign the Minimum Access - Salesforce profile (or equivalent
   base profile) for standard Salesforce license users.
2. Layer on Permission Sets for specific capabilities:
   - Sales_CRUD for sales object access.
   - Service_CRUD for service object access.
   - Report_Builder for report creation.
3. System Administrator profile should be assigned ONLY to:
   - Admins who manage org configuration.
   - Integration users (consider a custom Integration profile instead).
4. If a user "needs to see everything": grant via Permission Sets
   with appropriate CRUD/FLS, not the admin profile.
```

**Detection hint:** If the output assigns System Administrator to a non-admin user, the access is over-provisioned. Search for `System Administrator` assigned to roles like "sales rep," "agent," or "manager."

---

## Anti-Pattern 3: Ignoring the username uniqueness requirement

**What the LLM generates:** "Create a new user with username john.doe@company.com."

**Why it happens:** LLMs use the user's email address as the username without checking uniqueness. Salesforce usernames must be globally unique across ALL Salesforce orgs (production, sandboxes, developer orgs worldwide). If john.doe@company.com is already used in any org, the creation fails.

**Correct pattern:**

```
Username conventions:
1. Usernames must be globally unique across all Salesforce orgs.
2. Format: must look like an email address but does NOT need to be
   a real email. It is an identifier, not a mailbox.
3. Recommended patterns:
   - john.doe@company.com.prod (for production).
   - john.doe@company.com.uat (for UAT sandbox).
   - john.doe@company.salesforce (avoids real email conflicts).
4. The Email field (separate from Username) is the actual email address
   for notifications — this does not need to be globally unique.
5. Sandboxes automatically append the sandbox name to usernames
   (e.g., john.doe@company.com.sandboxname).
```

**Detection hint:** If the output uses a plain email address as the username without discussing global uniqueness or a naming convention, the username may conflict. Search for `globally unique` or `username convention` in the user creation steps.

---

## Anti-Pattern 4: Not distinguishing between Freeze and Deactivate

**What the LLM generates:** "Deactivate the user to immediately block their access while we sort out the offboarding."

**Why it happens:** LLMs jump to deactivation for urgent access removal. Deactivation has downstream effects: it can trigger ownership reassignment rules, unsubscribe from reports, and remove the user from teams and queues. For an immediate lock-out that preserves the user's current configuration, Freeze is the correct first step.

**Correct pattern:**

```
Freeze vs Deactivate:
- Freeze: immediately blocks login. No other changes.
  The user remains "Active" in the system.
  Records, teams, queue membership, and report subscriptions are unchanged.
  Use: immediate access removal while planning full offboarding.
  How: Setup → Users → [User] → Freeze button.

- Deactivate: permanently removes login access AND:
  - Frees the license.
  - May remove from queues and public groups (check settings).
  - Preserves the user record.
  Use: planned offboarding after records are reassigned.
  How: Setup → Users → [User] → Edit → uncheck "Active."

Recommended offboarding sequence:
1. Freeze (immediate access block).
2. Reassign records, remove from queues, transfer report subscriptions.
3. Deactivate (frees license, finalizes offboarding).
```

**Detection hint:** If the output deactivates a user for emergency access removal without mentioning Freeze as the immediate step, downstream side effects may occur. Search for `Freeze` in the offboarding instructions.

---

## Anti-Pattern 5: Forgetting to check license availability before user creation

**What the LLM generates:** "Create a new user with the Salesforce Platform license."

**Why it happens:** LLMs describe user creation without checking whether the org has available licenses. If all Salesforce Platform licenses are consumed, the user creation fails. License availability must be checked before creating a user.

**Correct pattern:**

```
Before creating a user:
1. Check license availability:
   Setup → Company Information → User Licenses section.
   Verify "Remaining Licenses" > 0 for the needed license type.
2. Common license types:
   - Salesforce: full CRM access.
   - Salesforce Platform: custom app access, limited standard objects.
   - Identity: SSO and authentication only.
   - Chatter Free / Chatter External: collaboration only.
3. If no licenses are available:
   - Deactivate an unused user to free a license.
   - Purchase additional licenses.
   - Consider a different license type that fits the user's needs.
4. Also check Feature Licenses:
   - Marketing User, Service Cloud User, Knowledge User.
   - These are separate from the user license and have their own limits.
```

**Detection hint:** If the output creates a user without checking license availability, the creation may fail. Search for `license`, `Company Information`, or `Remaining Licenses` before the user creation step.
