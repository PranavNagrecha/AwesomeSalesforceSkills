# Examples — Case Management Setup

## Example 1: Email-to-Case Threading Verification

**Context:** A Service Cloud org receives high volumes of customer support emails. The admin configured Email-to-Case but customers report that their replies are creating new cases instead of threading into the original case.

**Problem:** The mail server's "clean HTML" filter strips custom email headers and modifies the message body before forwarding to the Salesforce routing address. The thread ID token embedded in the outgoing case email is lost in transit, so Salesforce cannot match the reply to the parent case.

**Solution:**

Enable the "Thread ID in Email Subject" option as a fallback:

```
Setup → Email-to-Case → Routing Addresses → Edit [routing address]
  Enable: Thread ID in Email Subject Line = checked
```

With this setting, Salesforce appends the thread token to the email subject line as well as the body. Even if the body is modified, the subject line token survives most mail processing. Additionally, verify the reply-to header on outgoing case emails:

```
Setup → Email-to-Case → Routing Addresses
  Verify: "Route to this email address" points to the Salesforce-hosted address
  Verify: the outbound case email "reply-to" is set to the routing address, not a custom from-address that bypasses routing
```

**Why it works:** Placing the thread token in the subject line provides a second lookup channel. Mail servers rarely modify subject lines as aggressively as message bodies. Subject-line threading is the recommended fallback when body threading is unreliable.

---

## Example 2: Auto-Response Not Firing for Web-to-Case Submissions

**Context:** An admin configured a Web-to-Case form and an auto-response rule with an acknowledgment email template. The form submits successfully and cases are created, but customers never receive the confirmation email.

**Problem:** The auto-response rule is active and correctly configured, but the case assignment rule is not active. The auto-response rule depends entirely on the assignment rule firing — without an active assignment rule (or with an assignment rule whose entries do not match the submitted case), the auto-response never executes.

**Solution:**

1. Navigate to Setup → Case Assignment Rules. Confirm there is exactly one active rule.
2. Open the active rule and verify at least one entry has criteria that match the Web-to-Case submission (or add a catch-all entry with no criteria).
3. Create a test Web-to-Case submission and inspect the case's History related list for a "Rule Assignment" entry — this confirms the assignment rule fired.
4. Once the assignment rule is confirmed to fire, retest the auto-response.

If no active assignment rule exists:
```
Setup → Case Assignment Rules → New
  Name: Default Case Assignment Rule
  Active: checked
  Add rule entry: (no criteria) → assign to [General Support Queue]
Save and activate.
```

**Why it works:** Auto-response rule execution is gated on assignment rule execution. The platform uses the same event trigger — confirming an active, matching assignment rule is the prerequisite step that many configurations miss.

---

## Example 3: Escalation Rule with Business Hours Configuration

**Context:** Cases opened on Friday afternoons are escalating over the weekend and routing to a manager queue. The escalation threshold is 8 hours but the support team only works Monday–Friday, 8 AM–6 PM.

**Problem:** The escalation rule entry has no business hours record attached. Salesforce measures 8 elapsed clock hours from case creation regardless of day or time.

**Solution:**

```
Setup → Business Hours → New
  Name: Standard Support Hours
  Active: checked
  Time Zone: [org's primary timezone]
  Hours: Monday–Friday, 8:00 AM – 6:00 PM
  Saturday: closed
  Sunday: closed
Save.

Setup → Escalation Rules → [Active Rule] → Rule Entries → Edit entry
  Business Hours: Standard Support Hours    ← this was blank before
  Time Trigger: 8 hours
Save.
```

Test: create a case on Friday at 5 PM. Confirm it does NOT escalate until 8 hours of business time have elapsed (which would be Monday at 1 PM). Check Case history for escalation event timestamp.

**Why it works:** Attaching business hours to the rule entry instructs Salesforce to count only hours within the defined schedule. Without this attachment, the threshold is wall-clock time and escalations fire on nights, weekends, and holidays.

---

## Example 4: Case Team Role and Predefined Team Creation

**Context:** A support team wants to add a field engineer and an account manager to cases when a high-priority issue is opened. The admin creates a predefined team but team members still cannot see the cases.

**Problem:** Case team roles were not created before the predefined team was built. The predefined team was created with no roles assigned, so members have no access level defined and the system does not grant them record access.

**Solution:**

Step 1 — Create roles first:
```
Setup → Case Team Roles → New
  Name: Field Engineer
  Case Access: Read/Write
  Save.

Setup → Case Team Roles → New
  Name: Account Manager
  Case Access: Read Only
  Save.
```

Step 2 — Create predefined team:
```
Setup → Predefined Case Teams → New
  Name: High Priority Response Team
  Add member: [Field Engineer user] → Role: Field Engineer
  Add member: [Account Manager user] → Role: Account Manager
  Save.
```

Step 3 — Add team to cases:
```
On the Case record → Case Team related list → Add Predefined Team → High Priority Response Team
```

**Why it works:** Case team roles are a prerequisite — they define what access each position on the team receives. A predefined team without roles defined does not grant access. Roles must exist independently before they can be referenced in predefined teams.

---

## Example 5: Swapping the Active Assignment Rule Without a Routing Gap

**Context:** Support is reorganizing from a product-based queue structure to a region-based one. The admin has authored a new case assignment rule with the region entries and wants to cut over on Monday morning.

**Problem:** Only one case assignment rule can be active at a time. The admin's instinct is to deactivate the current rule, verify the new one looks right, then activate it. That sequence opens a window — however short — in which no assignment rule is active. Cases created in that window fall to the default case owner and, because auto-response rules fire only when an assignment rule fires, those customers receive no acknowledgment email. Nothing errors and nothing is logged; the gap is only discoverable by hunting for cases owned by the default owner.

**Solution:**

Step 1 — Record the incumbent before touching anything:

```
Setup → Case Assignment Rules
  Note the name of the rule with Active = checked.
  Example: "Case Assignment — Product Queues (2024)"
  This name is the rollback target.
```

Step 2 — Rehearse the swap in a sandbox with representative traffic:

```
Sandbox → activate "Case Assignment — Region Queues (2026 Q3)"
  Submit one test case per inbound channel: Web-to-Case, Email-to-Case, manual, API.
  For each, open the case → History related list → confirm a "Rule Assignment" entry.
  Confirm the auto-response fired for the channels that require one.
  Confirm no case landed on the default case owner.
```

Step 3 — Cut over in production by activating the new rule directly:

```
Setup → Case Assignment Rules → "Case Assignment — Region Queues (2026 Q3)" → Active: checked → Save

The incumbent rule is deactivated by this action. Do NOT deactivate it first.
```

Step 4 — Verify within the first hour:

```
Report: Cases created today WHERE Owner = [default case owner]
  Expected result: zero rows. Any rows mean an entry gap in the new rule —
  add or fix the catch-all entry.
```

Rollback, if needed, is one action: activate `Case Assignment — Product Queues (2024)`.

**Why it works:** Activating a rule deactivates whichever rule holds that slot, so the swap is atomic — there is never a moment with zero active rules. Deactivating first would introduce exactly the gap the atomic activation avoids. Naming rules with a version marker makes the incumbent identifiable, which is what turns rollback into a single click rather than a rebuild. The same procedure applies to auto-response and escalation rules, which share the identical single-active-slot behavior.

---

## Anti-Pattern: Configuring Auto-Response Rules Before Verifying Assignment Rules

**What practitioners do:** An admin sets up an auto-response rule with a polished email template and an activation condition, then cannot understand why customers are not receiving the email. They spend time debugging the template, the "from" address, the organization-wide email address permissions, and deliverability settings.

**What goes wrong:** None of those factors are the problem. The auto-response rule is conditional on the case assignment rule firing. Without an active assignment rule that fires for this case creation context, the auto-response never executes. The entire debugging session is directed at the wrong layer.

**Correct approach:** Always configure and validate the case assignment rule first. Confirm it fires (check Case history for "Rule Assignment"). Only after the assignment rule is working should the auto-response rule be configured and tested.
