# Decision Element Review

## Flow

Name:
Decision element label:

## Outcomes (ordered most-specific → widest)

| # | Name | Condition | Null-Safe? | Notes |
|---|------|-----------|------------|-------|
| 1 |      |           | [ ]        |       |
| 2 |      |           | [ ]        |       |
| 3 |      |           | [ ]        |       |
| D | Default (named): | | [ ] | |

## Checks

- [ ] Default outcome is explicitly named.
- [ ] Every field reference handles null explicitly or acknowledges
      null-goes-to-default is intentional.
- [ ] Pick-list comparisons use API value, not label.
- [ ] Boolean comparisons use raw variable.
- [ ] Custom condition logic uses explicit parentheses.
- [ ] Nesting depth from this Decision ≤ 2.
- [ ] Repeated conditions extracted to formula resource.

## Logging

- Log outcome name in:
  - [ ] Before-save: set on log-level variable (written after commit)
  - [ ] After-save: written to log object
  - [ ] Screen: breadcrumb variable
