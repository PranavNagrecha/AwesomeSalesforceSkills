# Examples — Flow Migration From Trigger

## Example 1: Account region derivation

**Context:** 8-year-old AccountTrigger sets `Region__c` from `BillingCountry`. 40 countries mapped via if/else in Apex.

**Problem:** Adding a new country requires a deploy. Sales ops waits days for trivial changes.

**Solution:** Replace with a Before-Save record-triggered Flow using a Decision element. Admin-maintainable; new countries added in 5 minutes. Same transaction semantics; no DML cost (Before-Save).

---

## Example 2: Partial migration

**Context:** OpportunityTrigger handler does (a) set Territory from BillingState (simple) + (b) call external pricing API with SavePoint + recursion control (complex).

**Problem:** Migrating the whole handler would fight Flow's limits; keeping the whole handler as Apex blocks admin ownership.

**Solution:** Split. Flow owns (a) — Before-Save field derivation. Apex retains (b). Test suite verifies both coexist correctly (Before-Save Flow fires before the After-Save Apex).

---

## Example 3: Shadow-mode migration

**Context:** Legacy Case-trigger handler computes SLA due dates. Engineering wants to migrate; risk of regression is high.

**Problem:** Full cutover is scary.

**Solution:** Deploy new Flow in-active. Use `FeatureManagement.checkPermission` in the Apex handler to conditionally skip logic if a Custom Permission is granted. Grant the Custom Permission to a 1-user PSG first; verify; ramp to 10%; ramp to 100%. Rollback = revoke PSG.

---

## Anti-Pattern: Migration without test parity

Team migrates the handler; doesn't re-run the existing test class. Later discovers a Before-Save Flow fires before another trigger's Before-Save; order changed. Fix: run the full test suite after every migration step.

---

## Anti-Pattern: Migrating hot-path high-volume triggers

Flow has per-element overhead. A tight Apex loop at 10k records/transaction can outrun the Flow equivalent by 3x. Fix: benchmark before migrating performance-sensitive triggers; keep Apex if the gap is material.
