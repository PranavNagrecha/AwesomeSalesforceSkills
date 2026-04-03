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

| Choice | Selected? | Reason |
|---|---|---|
| Before-save | | |
| After-save | | |
| Apex instead | | |

## Review Checklist

- [ ] Start criteria match the real business event.
- [ ] Same-record updates use before-save where possible.
- [ ] After-save work is justified and guarded against recursion.
- [ ] Mixed automation on the object was reviewed.
- [ ] A field-change check exists when the requirement depends on a transition.

## Notes

Document any recursion guard, prior-value logic, or reason the solution should move to Apex later.
