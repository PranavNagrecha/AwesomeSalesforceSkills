# Flow Transaction Finalizer — Examples

## Example 1: Welcome Email On Contact Create

**Wrong:** Record-Triggered Flow on Contact before-save sends a Welcome
email. If a later validation fails, the Contact rolls back but the email
has already gone out.

**Right:** After-save flow triggers a 0-minute Scheduled Path. Scheduled
path runs in a new transaction. If the create DML rolled back, the path
does not fire.

---

## Example 2: Outbound Webhook On Opportunity Close-Won

**Wrong:** After-save Flow performs an HTTP callout via Apex. Callouts are
not allowed after DML without first doing Database.setSavepoint and
handling state — and the Flow may commit and then silently fail on the
callout.

**Right:** After-save Flow publishes a Platform Event `OpportunityClosedWon__e`
with publish-after-commit. An Apex trigger subscribes and enqueues a
Queueable, which registers a Finalizer that logs success or queues a
retry.

---

## Example 3: Audit Row For Every Committed Approval

Approval Flow completes; immediately after commit, a Queueable with
Finalizer writes an Audit__c record. The Finalizer runs even if the
Queueable itself errors, so the audit record always captures either
success or the failure reason.

---

## Anti-Pattern: Fault Path As Post-Commit Handler

A team used Flow fault paths to handle callout failures, not realizing the
Flow had already committed prior DML. When the fault handler "compensated"
by updating the same records, it was racing with downstream triggers.
Correct approach: do callouts in an async step, compensate via a separate
flow or Queueable finalizer.
