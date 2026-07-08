# Record-Triggered Flow Design Template

## Trigger Summary

| Item | Value |
|---|---|
| Object | |
| Event | Create / Update / Delete |
| Same-record only? | Yes / No |
| Related-record work? | Yes / No |
| Existing automation on object | |

## Pattern Choice

| Choice | Flow Builder option | Selected? | Reason |
|---|---|---|---|
| Before-save | Fast Field Updates | | |
| After-save | Actions and Related Records | | |
| Apex instead | n/a | | |

## Trigger Order (same object, same phase)

| Flow API name | Phase | Trigger order (1–2,000) | Must run before / after |
|---|---|---|---|
| | before-save / after-save | | |
| | before-save / after-save | | |

Leave gaps between values (10, 20, 30). Every flow in the phase gets a value —
an unset flow sequences between the 1–1,000 and 1,001–2,000 bands, not last.
Trigger order cannot move a flow ahead of an Apex trigger or across the
before-save/after-save boundary.

## Review Checklist

- [ ] Start criteria match the real business event.
- [ ] Same-record updates use before-save where possible.
- [ ] After-save work is justified and guarded against recursion.
- [ ] Mixed automation on the object was reviewed.
- [ ] A field-change check exists when the requirement depends on a transition.
- [ ] Every flow in the phase has an explicit trigger order value, verified in Flow Trigger Explorer.

## Notes

Document any recursion guard, prior-value logic, or reason the solution should move to Apex later.
