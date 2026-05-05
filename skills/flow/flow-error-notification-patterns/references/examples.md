# Examples — Flow Error Notification Patterns

## Example 1 — "Do-nothing" fault path silently succeeds, failure is invisible

**Context.** A record-triggered after-save flow updates a related
record via Update Records. Sometimes the update fails (locked record,
validation rule rejection on the related record). Admin added a Fault
connector "for safety" but didn't connect it to anything meaningful.

**Wrong code (Flow XML pseudo).**

```
Update_Related_Record
    │
    ├── Success → end
    │
    └── Fault → end   (do-nothing)
```

**What goes wrong.** The Fault path "succeeded" (it ended without
itself failing). Salesforce considers the flow a success. No
unhandled-fault email. The admin never finds out. The related record
stays out of sync.

**Right answer.** The Fault path must do *something* observable —
publish a Platform Event, insert a `Flow_Error_Log__c` record, or
re-throw via the no-such-API-just-publish-event-pattern:

```
Update_Related_Record
    │
    ├── Success → end
    │
    └── Fault → [Action: Publish Flow_Error_Event__e
                  with Element="Update_Related_Record",
                       Message=$Flow.FaultMessage]
                → end
```

The flow still completes (caller's transaction isn't aborted), but
the failure is observable.

---

## Example 2 — Validation-rule rejection drowning admin's inbox

**Context.** Screen flow that creates a Case from a customer-facing
form. A validation rule rejects cases without a phone number. Every
day, 30 customers don't fill in phone, the validation fires, the
flow's Fault path has no decision branch, the admin gets 30
"unexpected error" emails — and misses the one real error from a
governor-limit failure.

**Wrong setup.** Single Fault path that publishes
`Flow_Error_Event__e` for every fault.

**Right answer.** Decision branch differentiating known business
rejections (validation rules) from real errors:

```
Create_Case
    │
    ├── Success → confirm screen
    │
    └── Fault → [Decision]
                    │
                    ├── $Flow.FaultMessage CONTAINS
                    │       "FIELD_CUSTOM_VALIDATION_EXCEPTION"
                    │   → [Display Text: "{!$Flow.FaultMessage}"]
                    │   → user re-enters → loop back to form
                    │
                    └── any other error
                        → [Action: Publish Flow_Error_Event__e]
                        → [Display Text: "An unexpected error.
                                          Admins notified."]
                        → end
```

Validation rejections show inline ("Phone is required"); admin only
hears about programmer errors.

---

## Example 3 — Reusable `Log_Flow_Error` sub-flow

**Context.** Org has 40 production flows. Building the same Fault-path
log step into each one is repetitive and inconsistent.

**Right answer.** One reusable autolaunched sub-flow.

`Log_Flow_Error` (autolaunched, takes 5 input variables):
- `flowName` (Text)
- `elementName` (Text)
- `faultMessage` (Text)
- `recordId` (Text)
- `severity` (Text — "INFO", "WARN", "ERROR")

Body: single Create Records on `Flow_Error_Log__c`.

In every production flow's Fault path:

```
Fault → [Action: Log_Flow_Error
            flowName="Approval_Routing_v2",
            elementName="Update_Manager_Field",
            faultMessage=$Flow.FaultMessage,
            recordId={!$Record.Id},
            severity="ERROR"]
       → end
```

Every parent flow passes its own name as a string literal — no way
to derive that automatically inside the sub-flow.

Benefits: one place to change log schema, one place to change
severity logic, every flow stays consistent.

---

## Example 4 — Platform Event for cross-channel alert routing

**Context.** Different flows have different audiences. Sales flows
go to Slack-#sales-ops. Service flows go to PagerDuty. Compliance
flows go to a custom email distribution list. Admin doesn't want to
hardcode the channel inside each flow.

**Approach.** All flows publish to one `Flow_Error_Event__e`. An
Apex subscriber routes:

```apex
trigger FlowErrorEventSubscriber on Flow_Error_Event__e (after insert) {
    EventBus.TriggerContext ctx = EventBus.TriggerContext.currentContext();
    for (Flow_Error_Event__e e : Trigger.new) {
        try {
            FlowErrorRouter.route(e);
            ctx.setResumeCheckpoint(e.ReplayId);
        } catch (RoutingException ex) {
            // Fall back to the default email channel; don't lose the event.
            FlowErrorRouter.fallbackEmail(e);
            ctx.setResumeCheckpoint(e.ReplayId);
        }
    }
}
```

`FlowErrorRouter.route` reads a custom-metadata table mapping flow
prefix → channel. New flow domains just add a row in custom metadata;
no flow rebuild.

Note: this is exactly the `apex/apex-event-bus-subscriber` skill's
checkpoint-on-success pattern — same shape, different consumer.

---

## Example 5 — Daily digest instead of per-error real-time alerts

**Context.** Even with Pattern D suppression, a noisy week produces
50+ errors. Real-time alerts on every event train the admin to
ignore them. Within a month nobody reads them.

**Right approach.** Daily digest.

Schedule a Salesforce Report on `Flow_Error_Log__c` filtered to
`CreatedDate = LAST_24_HOURS AND Severity__c IN ('ERROR', 'WARN')`,
grouped by `Flow_Name__c`. Subscribe the admin team. Alert is the
report's daily delivery (8 AM Monday-Friday).

For real-time-critical flows (payment processing, identity
provisioning), still use the Platform Event subscriber to fire a
direct alert — but reserve that for the small subset of flows where
30 minutes of detection delay is unacceptable.

---

## Anti-Pattern: Custom error messages that hide the real failure

```
Fault → [Display Text: "Sorry, an error occurred. Please try again."]
```

**What goes wrong.** The user sees a useless message. They retry —
same failure (the underlying issue isn't transient). They escalate.
Admin investigates and the only signal is "user reports unspecified
error". `$Flow.FaultMessage` was discarded.

**Correct.** Either show `$Flow.FaultMessage` to the user (when
it's a friendly validation message) OR log it for the admin (when
it's a technical message) — but never throw it away.
