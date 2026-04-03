# Gotchas — Wire Service Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## An Undefined Reactive Parameter Looks Like A Silent Failure

**What happens:** The component renders, but no request is made and the developer assumes the wire service is broken.

**When it occurs:** A dynamic parameter such as `$recordId` or a parent-provided value is still `undefined`.

**How to avoid:** Treat wire configuration completeness as part of the component contract and guard for missing inputs explicitly.

---

## Wire Timing Does Not Follow Lifecycle Intuition

**What happens:** Developers expect data to be available at a specific lifecycle hook and then write brittle code around that assumption.

**When it occurs:** Components tie provisioning expectations to `connectedCallback()` or `renderedCallback()`.

**How to avoid:** Treat wire emissions as asynchronous state updates managed by the framework.

---

## Refresh Strategy Is Easy To Forget After Writes

**What happens:** The component successfully updates data, but the UI remains stale because the wired read is never refreshed.

**When it occurs:** Writes are performed imperatively or asynchronously by other automation.

**How to avoid:** Decide up front whether the component needs `refreshApex()` or another LDS-aware refresh path.
