# LLM Anti-Patterns — Flow Governance

Common mistakes AI coding assistants make when generating or advising on Flow governance standards.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Suggesting generic naming conventions without org context

**What the LLM generates:**

```
"Name your flows descriptively, like 'Account_Update_Flow'."
```

**Why it happens:** LLMs provide generic advice because they lack org-specific context. Without a structured convention, flows accumulate with inconsistent names that are hard to search, sort, or attribute to teams.

**Correct pattern:**

Define a structured naming convention that includes the object, trigger type, and purpose:

```
Pattern: {Object}_{TriggerType}_{Purpose}
Examples:
  Account_BeforeSave_SetDefaultOwner
  Case_AfterSave_EscalateToManager
  Lead_Screen_QualificationWizard
  Contact_Scheduled_DeduplicationCleanup
```

Include the team or domain prefix if multiple teams build flows in the same org.

**Detection hint:** Naming convention advice that is a single example without a structured pattern or taxonomy.

---

## Anti-Pattern 2: Not recommending flow version cleanup

**What the LLM generates:**

```
"Create a new version of the flow for each change."
```

**Why it happens:** LLMs correctly advise versioning but never mention cleaning up old versions. Salesforce limits total flow versions per flow, and accumulated inactive versions clutter the setup page.

**Correct pattern:**

Establish a version lifecycle:
1. Keep only the active version and 1-2 prior versions as rollback candidates
2. Delete older inactive versions after confirming they are not referenced by Apex or subflows
3. Document the version history in an external change log or commit messages
4. Before deleting, check for paused interviews running on the old version

**Detection hint:** Governance advice about flow versioning without mentioning cleanup of inactive versions.

---

## Anti-Pattern 3: Recommending a single "Flow Admin" owner for all flows

**What the LLM generates:**

```
"Assign one Salesforce admin as the owner of all flows for consistency."
```

**Why it happens:** LLMs simplify ownership to a single person. This creates a bottleneck and a single point of failure. When that admin leaves or is unavailable, no one knows the intent behind individual flows.

**Correct pattern:**

Assign ownership at the team or domain level:

```
Sales Flows       --> Sales Operations team
Service Flows     --> Service Cloud team
Integration Flows --> Integration team
```

Document the owner in the flow's Description field and in a central inventory (spreadsheet, custom metadata, or a governance tool).

**Detection hint:** Governance recommendation assigning all flows to one person rather than distributing ownership by domain.

---

## Anti-Pattern 4: Not including a retirement or deactivation process

**What the LLM generates:**

```
"Document all active flows in a spreadsheet."
```

**Why it happens:** LLMs focus on inventory but not lifecycle. Flows that are no longer needed remain active, consuming governor limits and increasing the risk of unexpected behavior.

**Correct pattern:**

Establish a retirement process:
1. Quarterly review: identify flows that have not triggered in 90+ days
2. Check for dependent references (Apex, subflows, process builders, external calls)
3. Deactivate first, then delete after a grace period
4. Document the deactivation reason and date
5. Monitor for regression after deactivation

**Detection hint:** Governance advice that covers creation and documentation but not retirement or deactivation criteria.

---

## Anti-Pattern 5: Ignoring the interaction between multiple automations on the same object

**What the LLM generates:**

```
"Create a new record-triggered flow on the Account object for this use case."
```

**Why it happens:** LLMs suggest new flows without checking what already runs on that object. Multiple record-triggered flows, workflow rules, and Apex triggers on the same object can cause order-of-execution conflicts and recursion.

**Correct pattern:**

Before creating a new flow:
1. Inventory all existing automation on the target object (flows, triggers, workflow rules, process builders)
2. Check for order-of-execution conflicts (before-save flows run before validation rules and triggers)
3. Consider consolidating into fewer flows using Decision elements
4. Document the intended execution order
5. Test with all automations active, not in isolation

**Detection hint:** Advice to create a new record-triggered flow without asking what other automation exists on the same object.

---

## Anti-Pattern 6: Not including testing requirements in the governance standard

**What the LLM generates:**

```
"Each flow should be documented with its purpose, owner, and trigger conditions."
```

**Why it happens:** LLMs describe documentation as the primary governance control. Without testing requirements, flows are deployed based on manual verification alone.

**Correct pattern:**

Include testing in the governance standard:
1. Every flow must have at least one Flow Test covering the happy path
2. Fault paths must be tested with intentional error scenarios
3. Bulk scenarios must be tested with Data Loader or Apex test classes
4. Flow Tests must pass before activation in production
5. Record the test coverage in the flow's description or linked documentation

**Detection hint:** Governance standard that covers naming, ownership, and documentation but does not mention testing requirements.
