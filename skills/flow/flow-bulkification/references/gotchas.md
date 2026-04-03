# Gotchas — Flow Bulkification

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## A Single UI Test Does Not Prove Bulk Safety

**What happens:** A flow appears correct because it works when one user updates one record in a sandbox.

**When it occurs:** The design was only validated through manual UI testing and never exercised through imports, APIs, or mass updates.

**How to avoid:** Test with realistic batches and review the element sequence for per-record queries or DML.

---

## Subflows Still Consume The Parent Transaction Budget

**What happens:** Teams move logic into a subflow and assume the limits reset.

**When it occurs:** A parent flow calls a subflow from inside a high-volume record-triggered transaction.

**How to avoid:** Treat subflows as organization tools, not limit boundaries. The bulk-safe design still has to exist end to end.

---

## Before-Save And After-Save Are Not Interchangeable

**What happens:** A same-record field update is implemented in after-save, consuming extra DML and sometimes re-triggering automation.

**When it occurs:** Teams default everything to after-save because it feels more flexible.

**How to avoid:** Use before-save whenever the requirement is only to update fields on the triggering record.

---

## Apex In The Middle Of A Bad Flow Is Still A Bad Flow

**What happens:** A loop calls invocable Apex and the team assumes the Flow is now bulkified.

**When it occurs:** Invocable methods are added without checking whether the method accepts lists and handles the batch efficiently.

**How to avoid:** Review the Flow and the Apex boundary together. The number of calls and the list contract both matter.
