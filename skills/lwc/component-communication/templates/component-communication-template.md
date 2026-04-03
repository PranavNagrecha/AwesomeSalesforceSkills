# Component Communication Decision Worksheet

## Relationship

- Parent to child:
- Child to ancestor:
- Sibling or workspace-wide:
- Message scope:

## Mechanism Selection

| Need | Preferred Mechanism | Notes |
|---|---|---|
| Pass context or state down | `@api` property | Keep the child declarative |
| Trigger reset, validate, or focus | Public `@api` method | Narrow imperative surface |
| Notify owner that something happened | Custom Event | Event name should be lowercase |
| Cross-hierarchy coordination | LMS | Keep payloads small and clean up subscriptions |

## Event Contract

- Event name:
- `detail` payload:
- Should it bubble: Yes / No
- Should it be composed: Yes / No
- Who owns handling it:

## LMS Contract

- Message channel:
- Publisher:
- Subscribers:
- Subscription lifecycle:
- Reason a local event is not enough:

## Public Child API

- Public properties:
- Public methods:
- Methods that should stay private:
