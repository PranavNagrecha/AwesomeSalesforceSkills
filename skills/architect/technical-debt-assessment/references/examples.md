# Examples — Technical Debt Assessment

## Example 1: Pre-Project Audit for a Service Cloud Expansion

**Scenario:** A company is planning a significant Service Cloud feature expansion — introducing a new Case categorisation taxonomy, SLA automation, and an agent productivity console. Before the build starts, the Architect runs a full technical debt assessment to understand what debt will affect the project.

**What the audit found:**

- **40 inactive Process Builder flows** on the Case object, accumulated over 4 years. Most were "paused" rather than deleted when teams shipped Flow replacements. None were cleaned up. The org had 1,847 active Flow versions out of the 2,000 limit — leaving only 153 version slots before the org would reject new Flow activations.
- **3 automation overlap conflicts** on the Case object: a Record-Triggered Flow setting `Status` to `In Progress` on assignment, an Apex trigger also updating `Status` on the same `after update` event, and a Workflow Rule sending an email on status change. The Workflow Rule was supposed to have been migrated two years earlier. Result: the email was sometimes sent twice (once from the Workflow Rule's email alert and once from the Flow's Send Email action), and the final value of `Status` depended on which automation ran last — non-deterministic behavior.
- **Hardcoded Queue ID** in an Apex trigger: a 15-character Queue ID embedded in an `if` statement that routed escalated cases. This ID was valid in production but broken in all three sandboxes, which is why the QA team had been manually re-routing escalated test cases for months without understanding why.
- **2 Apex classes at 0% coverage**: `CaseMergeUtility` and `LegacyIntegrationHelper`. Both were written in 2019 and had never been updated since. Neither was referenced by any other class or metadata. Both were safe to delete.

**Remediation backlog produced:**

| Finding | Severity | Effort | Owner |
|---|---|---|---|
| Automation overlap: Flow + Apex both write `Status` | Critical | M | Developer + Architect |
| 40 inactive Process Builder flows — version limit risk | High | S | Admin |
| Hardcoded Queue ID in Apex trigger | High | XS | Developer |
| Duplicate email alert from Workflow Rule and Flow | Medium | S | Admin |
| 2 dead Apex classes (0% coverage, no references) | Medium | XS | Developer |

**Outcome:** The team cleaned inactive Flow versions and deleted dead code before the project started. The automation overlap was redesigned to use a single Record-Triggered Flow as the canonical owner of `Status` changes, with the Apex trigger refactored to a read-only audit log writer. The build proceeded with a clean baseline.

---

## Example 2: Targeted Automation Overlap Review — Duplicate Email Alerts on Case

**Scenario:** The support team reports that agents are receiving two copies of the same email notification when a Case is escalated. The CRM admin has checked the Flow and sees only one Send Email action. The ticket is escalated to the Architect for investigation.

**Investigation using this skill (Mode 2: Targeted Automation Review):**

1. The Architect pulls all active automation on the Case object: 1 Record-Triggered Flow (active), 0 Process Builder flows (confirmed inactive), 1 Workflow Rule (status: Active — this was not expected).
2. Both the Record-Triggered Flow and the Workflow Rule respond to `after update` on Case when `Escalated__c` changes to `true`.
3. The Record-Triggered Flow has a Send Email action using a Flow template. The Workflow Rule has an Email Alert action using a classic email template. Both target the `OwnerId` of the Case.
4. **Root cause confirmed:** two active automations responding to the same trigger event, both executing an email action to the same recipient. The Workflow Rule predates the Flow by 3 years. When the Flow was built, no one checked for existing Workflow Rules.

**Findings documented:**

- **Finding:** Active Workflow Rule `Case_Escalation_Email_Alert` overlaps with Record-Triggered Flow `Case_Escalation_Notifications` — both send an email to Case Owner when `Escalated__c` = true.
- **Severity:** High (user experience degradation — agents receive duplicate notifications on every escalation).
- **Remediation:** Deactivate the Workflow Rule. Confirm the Flow's email template covers the same content. If not, update the Flow template first, then deactivate the Workflow Rule.
- **Effort:** XS (30 minutes for a developer or admin with access to both Setup and Flow Builder).
- **Prevention note added to backlog:** The org needs an automation registry — a single table mapping each object's trigger events to their canonical automation owner — to prevent this class of overlap from recurring silently.

**Outcome:** The Workflow Rule was deactivated after confirming the Flow email template covered the same message content. Duplicate alerts stopped within 15 minutes of the change. The Architect added an automation overlap check to the org's standard pre-release checklist.
