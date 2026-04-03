# Wire Service Review Template

## Data Path

| Item | Value |
|---|---|
| Read source | UI API / Apex / GraphQL |
| Writes performed? | Yes / No |
| Reactive parameters | |
| Refresh trigger | |

## Review Checklist

- [ ] Wire is used only for read/provisioning scenarios.
- [ ] Reactive parameters are defined intentionally.
- [ ] Wired data is cloned before mutation.
- [ ] Refresh behavior after writes is explicit.
- [ ] Error handling matches the adapter shape (`error` vs `errors`).

## Notes

Document whether the component should remain wired, move to imperative access, or use LDS base components instead.
