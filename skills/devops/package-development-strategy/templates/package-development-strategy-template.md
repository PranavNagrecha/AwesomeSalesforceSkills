# Package Development Strategy — Decision Template

Use this template when selecting a Salesforce package type for a new product or internal modularization effort.

---

## Scope

**Project name:** _______________
**Use case:** [ ] ISV product for AppExchange  [ ] Internal org modularization  [ ] Shared utility library
**Existing namespace registered?** [ ] Yes: ___ [ ] No

---

## Package Type Selection

| Criterion | Answer | Notes |
|---|---|---|
| Will this be listed on AppExchange? | Y/N | If Y → managed package required |
| Is IP protection required? | Y/N | If Y → managed package required |
| Is namespace acceptable as permanent? | Y/N | Required for managed packages |
| Is DX / scratch org development required? | Y/N | If Y → unlocked or 2GP (not 1GP) |
| Is this a net-new product? | Y/N | If Y → 2GP over 1GP |
| Multiple sub-packages with dependencies? | Y/N | If Y → 2GP unlocked or managed |

---

## Recommended Package Type

Based on assessment:

- [ ] **2GP Managed Package** — new ISV product, AppExchange listing, IP protection required
- [ ] **Unlocked Package** — internal org modularization, no AppExchange listing, no namespace required
- [ ] **1GP Managed Package** — existing 1GP product migration only; avoid for new development
- [ ] **Unmanaged Package** — one-time template distribution only; no versioning lifecycle

**Rationale:** _______________

---

## Namespace Decision (Managed Packages Only)

**Proposed namespace:** _______________

Checklist before registering:
- [ ] Namespace is short (< 10 characters preferred)
- [ ] Namespace is brand-stable (not tied to a product name that may change)
- [ ] Namespace availability verified in Dev Hub
- [ ] AppExchange Partner Community namespace conflict check completed
- [ ] Team understands namespace is PERMANENT and cannot be changed

---

## Package Architecture

| Package Name | Type | Dependencies | Owner Team |
|---|---|---|---|
| ___ | ___ | None | ___ |
| ___ | ___ | ___ | ___ |

---

## Release Process

- [ ] Beta versions used for internal developer testing
- [ ] Released versions used for production subscriber / sandbox installation
- [ ] CI/CD pipeline target: `sf package version create`
- [ ] Version promotion gate: _______________
