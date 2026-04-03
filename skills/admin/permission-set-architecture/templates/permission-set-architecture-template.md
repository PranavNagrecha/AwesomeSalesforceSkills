# Permission Set Architecture Review Template

## Scope

| Item | Value |
|---|---|
| User licenses in scope | |
| Current profiles | |
| Current permission sets | |
| Current PSGs | |
| Primary pain point | Provisioning / audit / sprawl / exception handling |

## Persona Matrix

| Persona | Baseline profile | Capability permission sets | PSG | Exceptions or muting |
|---|---|---|---|---|
| | | | | |
| | | | | |

## Review Checklist

- [ ] Profiles are intentionally thin and not feature-heavy.
- [ ] Permission sets represent coherent capabilities.
- [ ] Recurring personas use PSGs instead of many direct assignments.
- [ ] Muting is documented and limited.
- [ ] License constraints were validated for each persona.
- [ ] Sharing issues were separated from feature-entitlement issues.

## Migration Notes

**Immediate cleanup candidates:**  
List duplicate profiles, oversized permission sets, or personas that should become PSGs.

**Rollback plan:**  
Document how assignments can be reversed if the bundle model needs adjustment.
