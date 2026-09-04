# Troubleshooting — "The assignment rule didn't fire"

Work top to bottom. Each step has one check and one fix. Stop at the first step that fails; later steps assume the earlier ones pass. The same order applies to Lead and Case.

## 0. Establish the facts before touching Setup

| Fact | How to get it |
|---|---|
| How was the record created? | Owner is the integration user → API / Data Loader path (step 1). Owner is the rep who created it → UI checkbox (step 1). Owner is a queue, but the wrong one → criteria or entry order (step 3). |
| Which rule is active right now? | `SELECT Id, Name, Active FROM AssignmentRule WHERE SobjectType = 'Lead'` — the `AssignmentRule` object is read-only and queryable; `Active`, `Name`, `SobjectType` are its only business fields. |
| What did the record look like at save? | The payload the integration sent, or field history. Rule criteria evaluate the values at save time, not values an after-save automation wrote later. |

## 1. Did the creation channel invoke the rule at all?

Assignment rules are opt-in for every channel except the three web/email intake channels.

| Channel | Rule runs by default? | What to check | Fix |
|---|---|---|---|
| Web-to-Lead, Web-to-Case, Email-to-Case | Yes | Nothing here — go to step 2 | — |
| Lightning UI, new record | No | "Assign using active assignment rule" (Lead) / "Run assignment rules" (Case) checkbox was ticked | Train users, or replace manual entry with a screen flow + invocable Apex that sets the header (see gotchas #3) |
| REST API | No | Request carries `Sforce-Auto-Assign: true` (or a rule Id) | Add the header in the integration |
| SOAP API | No | Envelope carries `AssignmentRuleHeader` with `useDefaultRule` or `assignmentRuleId` | Add the header |
| Bulk API / Bulk API 2.0 / Data Loader | No | Job or Settings specifies the assignment rule Id | Set `sfdc.assignmentRule` (Data Loader) or the job's assignment rule; the Id is per org — look it up with the SOQL in step 0 |
| Apex | No | `Database.DMLOptions` with `assignmentRuleHeader.useDefaultRule = true` passed to `Database.insert` | Plain `insert` never invokes rules — switch to `Database.insert(records, dmo)` (see references/testing.md) |
| Flow "Create Records" | No | Flow has no assignment-rule option on Create Records | Call an invocable Apex action that inserts with `DMLOptions`, or let the Flow set `OwnerId` itself and deactivate the rule for that path |

## 2. Is there exactly one active rule for this object?

Run the step 0 query. Zero active rules → activate one. The platform never allows two active rules on an object; if two admins each "activated" one, the second activation silently deactivated the first (gotchas #2).

## 3. Did an entry match, and was it the entry you expected?

- **First match wins.** A broad entry above a specific one swallows every record the specific one was meant to catch. Read the entries in Setup order, not alphabetical order.
- **Null values never match an equals entry.** `Lead.State equals CA` skips a lead with no State. Add a final catch-all entry with no criteria so unmatched records land somewhere visible instead of with the Default Lead Owner or the API user.
- **Values are compared at save.** A before-save Flow's writes are visible to the rule; formula and roll-up values may not be (gotchas #5). Route on a plain field the Flow populates.
- **Reproduce the match** by putting the entry's criteria into a list view or SOQL `WHERE` clause and checking whether the record appears. If it does not, the entry cannot have matched.
- **Picklist and boolean values** must be spelled exactly as the API value (`True` / `False` for checkboxes, comma-separated values for "equals any of").

## 4. Was the target usable?

- Queue exists **and supports the object**: `SELECT Queue.DeveloperName, SobjectType FROM QueueSobject WHERE SobjectType = 'Lead'`. A queue that does not list the object cannot own it.
- Queue has at least one active member (gotchas #4 has the `GroupMember` query).
- User target is still active. Audit entries after every offboarding; prefer queues so a departure does not break routing.

## 5. Did something overwrite the owner afterwards?

The rule's result is not the last word in the transaction. In save order the rule runs after before-save Flows and before after-save Flows and triggers, so:

- a **before-save Flow** that sets `OwnerId` loses to the rule;
- an **after-save Flow, Apex trigger, or legacy Process Builder** that sets `OwnerId` wins over the rule.

List every record-triggered Flow and trigger on the object and search them for `OwnerId`. Also check Omni-Channel push routing, escalation-rule reassignments, and lead conversion, all of which change ownership later. The full ordering is in `flow/flow-record-save-order-interaction`.

## 6. Auto-response email was not sent

The auto-response rule is only evaluated when the assignment rule fires, so steps 1 to 3 must pass first. Then check, in order:

1. The auto-response rule is active and its first matching entry is the one you expect (first match wins here too).
2. The entry's template exists, is active, and is a Classic template if the rule is deployed by metadata.
3. The sender address is a verified org-wide email address, and is **not** the Email-to-Case routing address (that creates a reply loop — `admin/email-to-case-configuration` gotchas).
4. In a sandbox, email deliverability is set to "All Email"; refreshed sandboxes default to system email only (`devops/sandbox-data-isolation-gotchas`).
5. Apex inserts set `dmo.emailHeader.triggerAutoResponseEmail = true` if the auto-response is expected from code.

Deeper treatment: `admin/case-management-setup` (Case) and `admin/lead-management-and-conversion` (Lead).

## 7. Escalation did not fire

Escalation is a timer, not a save-time rule, so it does not belong in steps 1 to 5. Check the escalation-rules skill's gotchas for the four usual causes: the engine's polling cadence, business hours pausing the clock, the age-over basis resetting on edit, and a rule that was deactivated and later reactivated. See `admin/escalation-rules`.
