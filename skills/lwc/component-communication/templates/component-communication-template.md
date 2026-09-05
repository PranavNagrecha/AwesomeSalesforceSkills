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

- Event name (lowercase, underscores between words, never an `on` prefix):
- `detail` payload (list each field and its primitive type):
- Should it bubble: Yes / No — reason:
- Should it be composed: Yes / No — reason:
- Is the component ever slotted, or wrapped by an Aura component / quick action:
- Who owns handling it:
- Jest assertion that pins `detail`, `bubbles`, `composed`:

## LMS Contract

- Message channel (`Name__c`) and `masterLabel`:
- `lightningMessageFields` — one `fieldName` per payload key:
- `isExposed` (default `false`; raising it is irreversible) — decision and owner:
- Publisher:
- Subscribers, and where each physically sits (active tab / background console subtab / utility bar / iframe / Experience Cloud site):
- Subscriber `scope` (default active area, or `APPLICATION_SCOPE`) — reason:
- Subscription lifecycle (`connectedCallback` guard + `disconnectedCallback` unsubscribe):
- Container check — is LMS supported here at all:
- Reason a local event is not enough:

## Public Child API

- Public properties (name, type, and for booleans confirm the default is `false`):
- Public methods (each must be an action with no natural reactive trigger):
- Properties needing an `@api` setter, and what the setter recomputes:
- Methods that should stay private:
- `js-meta.xml`: `apiVersion`, `isExposed`, and at least one `<target>` when exposed:
