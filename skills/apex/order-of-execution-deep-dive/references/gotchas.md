# Gotchas — Order of Execution Deep Dive

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Before-Save Flow Runs at Step 3, Not Step 15

**What happens:** A before-save record-triggered Flow runs at step 3, the same step as Apex before triggers — not at step 15 where after-save Flows run. Because it modifies the in-memory record before the save, it does not require a separate DML operation. Practitioners who assume all Flows run late in the sequence are surprised when a before-save Flow value is visible in (or overwritten by) a before Apex trigger.

**When it occurs:** Any time a record-triggered Flow is configured with "Run when: A record is created or updated" and "Optimize for: Actions and Related Records" is NOT selected (i.e., before-save mode is active). The Flow label does not make the timing obvious.

**How to avoid:** Treat before-save Flows and before Apex triggers as peers at step 3. Assign field-write ownership explicitly: either the Flow writes the field or the trigger writes it, not both. If both must exist, the later writer in step 3 wins (order within step 3 is not guaranteed), so use a conditional check to avoid unconditional overwrites.

---

## Gotcha 2: Workflow Field Update Re-Fire Is Exactly Once — But Triggers Must Be Idempotent

**What happens:** If a workflow rule fires a field update, Salesforce re-runs all before triggers, validation rules, and after triggers one additional time. Triggers that unconditionally create child records, send emails, or perform side effects will execute those side effects twice: once in the original pass and once in the re-fire pass.

**When it occurs:** Any object that has both a workflow rule with a field update and an Apex trigger that performs side effects (inserts, callouts initiated in after triggers, etc.). This is especially common on objects like Case, Lead, Opportunity, and Account where workflow rules are heavily used.

**How to avoid:** Use a static `Set<Id>` or static Boolean in the trigger handler to track whether the side effect has already been performed. Check the guard before any non-idempotent side effect. Alternatively, audit all workflow rules on the object and migrate field updates to before-save Flows (step 3), which do not trigger a re-fire.

---

## Gotcha 3: Roll-Up Summary Update Starts a Full Order of Execution on the Parent

**What happens:** At step 17, if a child record's save affects a roll-up summary field on its master-detail parent, Salesforce updates the parent record. This starts the parent object's own full order of execution: parent before triggers, validation, parent after triggers, and so on. From the perspective of the parent trigger, the DML came "out of nowhere" — it was triggered by a child record save that had no visible parent DML in the code.

**When it occurs:** Any master-detail relationship with an active roll-up summary (COUNT, SUM, MIN, MAX). Common on Opportunity-to-Account, Case-to-Account, and custom master-detail objects.

**How to avoid:** Design parent triggers to be defensive about the source of the update. Use `Trigger.new` vs `Trigger.old` field comparisons to detect whether the parent's own meaningful fields changed. If the trigger only runs on specific field changes, add conditions that check those fields rather than firing on any update.

---

## Gotcha 4: Validation Rules Run After Before Triggers, Not Before

**What happens:** Custom validation rules run at step 5, after before triggers at step 3. This means a before trigger can supply a value for a required field and the validation rule will pass — even if the DML statement did not provide that field value. Conversely, if a before trigger introduces a bad value, the validation rule can catch it. Practitioners who expect validation to block bad input before any trigger code runs are surprised when triggers execute with invalid data and then validation fires.

**When it occurs:** Any time a validation rule is meant to act as a pre-condition check before automation runs. The automation (before trigger or before-save Flow) runs first.

**How to avoid:** If a before trigger must not run when the record is invalid, add the validation logic to the trigger itself (step 3) as an explicit check, throw an exception, or use `Trigger.new[i].addError()`. Do not rely on validation rules to prevent before trigger code from executing.

---

## Gotcha 5: @future and Post-Commit Email Send Are Not Rollback-Safe

**What happens:** `@future` method calls queued during a transaction do not execute until step 18, after the transaction commits. If the transaction rolls back (e.g., due to an unhandled exception in an after trigger), the `@future` method is also cancelled. However, post-commit emails sent by workflow email alerts or `Messaging.sendEmail()` called before commit may or may not be rolled back depending on when in the sequence they were sent. Email sends via workflow (step 11) are typically cancelled on rollback, but this is not guaranteed for all email mechanisms.

**When it occurs:** Any automation that sends outbound communication (email, callout, platform event publish) and also has risk of transaction rollback.

**How to avoid:** Put all external communication in `@future` methods or platform events published with `PublishBehavior.PUBLISH_AFTER_COMMIT` to guarantee they only fire after a successful commit.
