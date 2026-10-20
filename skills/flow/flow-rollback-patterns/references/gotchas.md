# Gotchas — Flow Rollback Patterns

## Gotcha 1: Rollback doesn't undo Platform Events published "Publish Immediately"

**What happens:** Event already on the bus; subscribers may have acted. Rollback only erases local DML. The guide: "You can't roll back published event messages" with Publish Immediately (platform_events 264 L276-277), and "the event message is still published and can't be rolled back" (L660-661). With Publish After Commit "the event message is published only after a transaction commits successfully" (api_meta 264 L44517-44518); the default is `PublishImmediately` (L44513).

**How to avoid:** Use Publish After Commit whenever possible. If Publish Immediately is required, design compensating events.

---

## Gotcha 2: Rollback doesn't undo HTTP callouts

**What happens:** Vendor API call already completed; external state is changed.

**How to avoid:** Run the callout in its own transaction after the critical DML has committed (`flowTransactionModel` `NewTransaction`, or `Automatic` with pending DML, api_meta 264 L71022-71029), or before the DML; Apex does not allow a callout "when there are pending operations in the same transaction" (apexdev 264 L36340-36342). Otherwise design for vendor-side rollback via a second callout.

---

## Gotcha 3: Logging inside fault path gets rolled back too

**What happens:** Log record you wrote to capture the failure is itself erased by Rollback Records, which "cancels its pending record changes" (api_meta 264 L73986).

**How to avoid:** Log to a separate transaction (a Publish Immediately platform event, platform_events 264 L276-277) OR route the log write to a completely independent fault branch that doesn't trigger rollback. UNVERIFIED (2026-10-20): that an Apex `@future` log or a Create Records log after the rollback survives is not in the corpus.

---

## Gotcha 4: Rollback in a subflow affects the parent

**What happens:** Subflow rolls back; parent flow's DML from before the subflow call is also undone. UNVERIFIED (2026-10-20): subflow rollback scope is not in the corpus; `FlowSubflow` has a `connector` and no fault connector (api_meta 264 L75367-75368).

**How to avoid:** Design rollback scope at the parent level. Subflow fault paths should log and return an error flag; parent decides whether to rollback.

---

## Gotcha 5: Email is post-commit work, so a rollback can suppress the alert

**What happens:** The order of execution commits all DML at step 19 and only then "executes post-commit logic" including "Sending email" (apexdev 264 L15681-15690), so a rolled-back transaction does not send it. The earlier text said the Send Email element had already dispatched and rollback could not recall the email. UNVERIFIED (2026-10-20): that a flow's Send Email action follows the Apex post-commit rule is not stated for the Flow element.

**How to avoid:** Do not make email the only failure signal on a path that rolls back; write the evidence to a Publish Immediately platform event (platform_events 264 L276-277). Place Send Email AFTER all DML that could fault. UNVERIFIED (2026-10-20): the Chatter-post claim of the earlier text is not in the corpus.

---

## Gotcha 6: File uploads to ContentVersion persist

**What happens:** User uploaded a file mid-flow; Rollback doesn't remove the ContentVersion. UNVERIFIED (2026-10-20): not in the corpus.

**How to avoid:** Manually delete the ContentVersion in the fault path before Rollback.

---

## Gotcha 7: Approvals triggered before Rollback keep approval records

**What happens:** Approval Process submission created a ProcessInstance; Rollback doesn't cancel it. UNVERIFIED (2026-10-20): not in the corpus.

**How to avoid:** Submit approvals only AFTER all DML known-good checkpoints. Or manually recall approvals in the fault path.
