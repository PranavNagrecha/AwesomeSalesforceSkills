# GraphQL API Design Worksheet

## Client Context

| Item | Value |
|---|---|
| Client type | |
| Offline requirement | Yes / No |
| Query or mutation | |
| Pagination required | Yes / No |

## Query Discipline

- Operation name:
- Variables:
- Selected fields:
- Expected page size:
- Partial-error handling approach:

## Guardrails

- [ ] Variables used instead of string interpolation
- [ ] Field selection is minimal
- [ ] Adapter choice is justified
- [ ] Cursor strategy is documented when paging is required
