# FlexCard State Management — Gotchas

## 1. `Refresh Card State` Does Not Re-Run Data Sources

`Refresh Card State` re-renders from cache. If the server record changed, the card still shows the cached value.

Avoid it: use `Refresh Card Data` after any action that could have mutated the record.

## 2. Conditional Visibility Reads Cache, Not Live Fields

If the field the visibility rule reads is not in the card's cached response, the rule is always false.

Avoid it: include the field in the data source projection OR write the value into the cache via the action's output mapping.

## 3. Pubsub Events Are Runtime-Only

Pubsub does not survive navigation or browser refresh. If you need durable signaling, use Platform Events or a data-layer poll.

## 4. Session Variables Are Page-Scoped

Session variables live at the runtime layer — two unrelated FlexCards on the same page can read and overwrite each other's values.

Avoid it: namespace every session variable (e.g. `accountSummary.selectedContactId`) and document the owner.

## 5. Child Cards Inside OmniScripts Reset Between Steps

Moving forward/back across steps reinitializes embedded FlexCards. Persist anything important in OmniScript data JSON, not in the child card's state.
