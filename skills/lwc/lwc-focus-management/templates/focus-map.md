# LWC Focus Map

## Component

- Name:
- Role (modal / wizard / list / form / widget):

## State Transitions Requiring Focus

| Transition | Focus target | Restoration target | Announcement |
|---|---|---|---|
| Open modal | first input in modal | opener button | role="dialog" name |
| Close modal | opener button | n/a | n/a |
| Validation failure | error summary | n/a | role="alert" |
| Async load complete | results heading | n/a | "Loaded N results" |
| Row added | new row | n/a | "Row added" |
| Row removed | next / prev row | list heading | "Row removed" |

## Shadow DOM Boundaries

- Children needing `@api focus()`:
- Selectors used (must be via `this.template`):

## Keyboard Walk

- [ ] Tab reaches every interactive element in visual order.
- [ ] Modal traps Tab; Esc closes.
- [ ] No focus disappears after state change.

## Tests

- [ ] Jest: spy on `.focus()` for each transition.
- [ ] Manual: NVDA or VoiceOver walk.

## Sign-Off

- [ ] Every state transition has a focus target.
- [ ] Every trap has a restore path.
- [ ] Live regions announce.
