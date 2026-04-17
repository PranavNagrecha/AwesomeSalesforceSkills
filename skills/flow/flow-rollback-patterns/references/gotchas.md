# Gotchas — Flow Rollback Patterns

## Gotcha 1: Rollback doesn't undo Platform Events published "Publish Immediately"

**What happens:** Event already on the bus; subscribers may have acted. Rollback only erases local DML.

**How to avoid:** Use Publish After Commit whenever possible. If Publish Immediately is required, design compensating events.

---

## Gotcha 2: Rollback doesn't undo HTTP callouts

**What happens:** Vendor API call already completed; external state is changed.

**How to avoid:** Do callouts AFTER critical DML succeeds, or design for vendor-side rollback via a second callout.

---

## Gotcha 3: Logging inside fault path gets rolled back too

**What happens:** Log record you wrote to capture the failure is itself erased by Rollback Records.

**How to avoid:** Log to a separate transaction (Platform Event to subscriber, or Apex @future) OR route the log write to a completely independent fault branch that doesn't trigger rollback.

---

## Gotcha 4: Rollback in a subflow affects the parent

**What happens:** Subflow rolls back; parent flow's DML from before the subflow call is also undone.

**How to avoid:** Design rollback scope at the parent level. Subflow fault paths should log and return an error flag; parent decides whether to rollback.

---

## Gotcha 5: Email sends are NOT rolled back

**What happens:** Send Email element already dispatched; Rollback undoes the record writes but not the email.

**How to avoid:** Place Send Email AFTER all DML that could fault, so rollback occurs before the email is sent. Or use a notification pattern (Chatter post) that IS transaction-scoped.

---

## Gotcha 6: File uploads to ContentVersion persist

**What happens:** User uploaded a file mid-flow; Rollback doesn't remove the ContentVersion.

**How to avoid:** Manually delete the ContentVersion in the fault path before Rollback.

---

## Gotcha 7: Approvals triggered before Rollback keep approval records

**What happens:** Approval Process submission created a ProcessInstance; Rollback doesn't cancel it.

**How to avoid:** Submit approvals only AFTER all DML known-good checkpoints. Or manually recall approvals in the fault path.
