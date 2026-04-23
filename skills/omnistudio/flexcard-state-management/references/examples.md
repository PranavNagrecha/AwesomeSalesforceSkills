# FlexCard State Management — Examples

## Example 1: Sibling Refresh Via Pubsub

**Context:** A parent layout renders two FlexCards: `Account_Summary` and `Recent_Cases`. When the user opens a new case from the summary card, the case list should refresh.

**Problem:** Binding the case list to refresh on every cache event causes flicker and redundant data source calls.

**Solution:**

```text
Account_Summary action:
  On Success → Pubsub publish event "case.created" with payload { accountId }

Recent_Cases config:
  Subscribe to "case.created" → Refresh Card Data
```

**Why it works:** Sibling coupling via named event; neither card reads the other's cache.

---

## Example 2: Parameter-Driven Child Rerender

**Context:** A parent card has a picklist of contacts; the child card should render details of the selected contact.

**Solution:** Pass `contactId` as an input parameter to the child FlexCard. When the parent selection changes, update the binding — the child rerenders automatically.

---

## Anti-Pattern: `Refresh Card State` After Server Write

Calling `Refresh Card State` after an Apex action that mutates a record shows stale data because state refresh reads the cached response. Use `Refresh Card Data` (or re-invoke the data source) instead.
