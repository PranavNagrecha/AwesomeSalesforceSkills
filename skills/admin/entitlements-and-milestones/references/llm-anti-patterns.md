# LLM Anti-Patterns — Entitlements and Milestones

Common mistakes AI coding assistants make when generating or advising on Salesforce Entitlement Management.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Hardcoding SLA Deadlines in Flow Instead of Using Entitlement Processes

**What the LLM generates:** A Record-Triggered Flow on Case creation that calculates `{!Case.CreatedDate} + 4 hours` and stores the result in a custom `SLA_Deadline__c` field, then uses a Scheduled Path to send an email alert when the deadline is reached.

**Why it happens:** LLMs are trained on large volumes of Flow automation examples that handle time-based logic via date arithmetic. Entitlement processes are less commonly covered in training data. The LLM defaults to the most general-purpose tool (Flow) rather than the domain-specific one (Entitlement Management).

**Correct pattern:**
```
Use an Entitlement Process with a milestone:
  - Time limit: 4 hours
  - Business hours: assigned at process or milestone level
  - Warning action at 75% (3 hours)
  - Violation action at 100% (4 hours)
Flow role: only populate Case.EntitlementId on case creation
```

**Detection hint:** Look for Flow nodes that add a duration (hours/minutes) to `Case.CreatedDate` or `Case.LastModifiedDate` and store the result in a custom field. This is the SLA-hardcoding pattern.

---

## Anti-Pattern 2: Recommending Entitlement Template Product Attachment in Lightning

**What the LLM generates:** Instructions telling the user to navigate to the Product2 record, find the "Entitlement Templates" related list, and attach the template to the product. The LLM may describe this as a standard configuration step without noting that the related list is absent in Lightning Experience.

**Why it happens:** Official Salesforce documentation describes entitlement template product attachment as a valid configuration path. Training data likely includes older documentation and Classic-era help articles that describe this UI without noting the Lightning limitation.

**Correct pattern:**
```
In Lightning Experience:
1. Create the entitlement template in Setup > Entitlement Templates
2. Build a Record-Triggered Flow on OpportunityLineItem (Opportunity.StageName = 'Closed Won')
   or on Order activation
3. In the Flow, create an Entitlement record with:
   - EntitlementTemplateId = <template ID>
   - AccountId = related account
   - StartDate = today
   - EndDate = today + contract duration
   - EntitlementProcessId = <process ID>
```

**Detection hint:** Any response that says "on the Product record, add the entitlement template using the related list" without qualifying "this requires Classic" is suspect.

---

## Anti-Pattern 3: Assuming Milestone Timers Start Automatically Without EntitlementId on Case

**What the LLM generates:** Configuration instructions that end after creating the entitlement process and entitlement records, without addressing how `Case.EntitlementId` is populated on cases created via Email-to-Case or Web-to-Case.

**Why it happens:** The LLM treats entitlement process configuration as self-contained. The dependency on the `EntitlementId` lookup being populated on each case is an operational detail that requires separate automation, and LLMs often omit this connection step.

**Correct pattern:**
```
After configuring the entitlement process, build a Before-Save
Record-Triggered Flow on Case (Create):
  - Query: SELECT Id FROM Entitlement
      WHERE AccountId = :triggerCase.AccountId
      AND Status = 'Active'
      LIMIT 1
  - If found: set Case.EntitlementId = queried entitlement Id
  - If not found: optionally set a fallback default entitlement
```

**Detection hint:** Any entitlement configuration walkthrough that does not mention populating `Case.EntitlementId` for automated case creation channels is incomplete.

---

## Anti-Pattern 4: Conflating Case Escalation Rules with Entitlement Milestones

**What the LLM generates:** When asked to "set up SLA alerts when a case is overdue," the LLM recommends configuring a Case Escalation Rule (Setup > Escalation Rules) instead of — or in addition to — an entitlement milestone violation action.

**Why it happens:** Escalation rules and milestone violation actions both send alerts for overdue cases. LLMs conflate the two because they appear in similar help articles and address superficially similar problems. However, escalation rules do not pause for business hours, do not distinguish by support tier, and cannot use percentage-based thresholds.

**Correct pattern:**
```
Use entitlement milestones for:
  - Time-based SLA tracking per support tier
  - Business-hours-aware timer pausing
  - Warning (50%/75%/90%) + violation (100%) action thresholds
  - Milestone completion tracking (Success actions)

Use escalation rules only for:
  - Simple age-based case reassignment when entitlement management is not in use
  - Scenarios where SLA tiers are not required
```

**Detection hint:** A response that mixes Setup > Escalation Rules configuration with entitlement process configuration for the same SLA use case is conflating the two systems.

---

## Anti-Pattern 5: Recommending Independent Recurrence for All Response Milestones

**What the LLM generates:** When asked to track "how quickly agents respond to cases," the LLM recommends setting all response milestones to Independent recurrence so the timer resets whenever a case is updated.

**Why it happens:** Independent recurrence sounds like the most comprehensive option — it tracks every interaction. LLMs optimize for apparent completeness without understanding the operational consequences: action storms, stacking timers, and difficulty completing milestones cleanly.

**Correct pattern:**
```
Use Independent recurrence ONLY when:
  - Each recurrence represents a distinct contractual commitment
    (e.g., "respond to every customer comment within 2 hours")
  - The reset event is well-defined and bounded
    (e.g., a specific field change, not every case update)
  - Violation actions include suppression conditions
    (e.g., only alert if Case.Status != 'Waiting on Customer')

Use No Recurrence for:
  - First-response SLAs (milestone fires once when agent first responds)
  - Resolution SLAs (milestone fires once when case is resolved)
  - Any SLA where the commitment is for the lifetime of the case, not per-interaction
```

**Detection hint:** A configuration that sets Independent recurrence on a milestone without also specifying a suppression condition on violation actions should be flagged for review.

---

## Anti-Pattern 6: Ignoring Entitlement Process Versioning When Updating SLA Terms

**What the LLM generates:** Instructions to "edit the existing entitlement process" and change the milestone time limits when a customer's SLA contract terms change, without mentioning that a new version must be published and that in-flight cases remain on the old version.

**Why it happens:** LLMs treat Salesforce configuration objects as directly editable. The versioning behavior of entitlement processes — where active cases are locked to the version in effect at entitlement creation — is a runtime behavior that is not obvious from the configuration UI.

**Correct pattern:**
```
To update milestone time limits:
1. Open the existing entitlement process
2. Click "New Version" to create a new version (do not edit the active version)
3. Update milestone time limits in the new version
4. Activate the new version
5. Identify open cases on the old version via report
6. (Optional) Build a Flow to migrate open cases to the new version
   if the change must apply immediately
```

**Detection hint:** Any response that says "update the milestone time limit in the entitlement process" without mentioning versioning and in-flight case impact should be challenged.
