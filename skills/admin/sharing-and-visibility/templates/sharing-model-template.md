# Sharing Model Template

Use this to document or redesign record-level access for an object. One object per copy. Fill it before writing metadata (workflow step 1) and keep it as the one-page answer to "who can see record X, and why".

---

## Object Overview

| Property | Value |
|----------|-------|
| Object (API name) | `<Object__c>` |
| Data sensitivity | Low / Medium / High |
| Business owner | `<name / team>` |
| Admin owner | `<name / team>` |
| Internal users only? | Yes / No |
| External users involved? | Yes / No — if yes, which licence and profile |
| Master-detail child? | Yes / No — if yes, there is no Owner field, no `__Share` table, and no sharing rules; the model belongs to the master |

## Baseline Access

| Layer | Design | File |
|-------|--------|------|
| Object access (CRUD) | `<permission sets granting Read / Create / Edit / Delete>` | `permissionsets/` |
| OWD — `sharingModel` | `Private` / `Read` / `ReadWrite` / `ControlledByParent` | `objects/<Obj>/<Obj>.object-meta.xml` |
| External OWD — `externalSharingModel` | `Private` / `Read` / `ReadWrite` / N/A | same file |
| Ownership pattern | `<who owns a record at creation, and what changes it>` | — |
| Role hierarchy assumptions | `<which roles must inherit, and whether Grant Access Using Hierarchies is on>` | `roles/` |

## Sharing Grants

Each row is one deployable grant. `accessLevel` must be strictly more permissive than the OWD above, or the platform will not store the share row.

| Mechanism | Who gets access (`sharedTo`) | Access level | Why | File |
|-----------|------------------------------|--------------|-----|------|
| Owner-based rule | `<group / role / roleAndSubordinatesInternal>` | Read / Edit | `<requirement>` | `sharingRules/<Obj>.sharingRules-meta.xml` |
| Criteria-based rule | `<group>` | Read / Edit | `<requirement, plus the includeRecordsOwnedByAll decision>` | same file |
| Team access | `<team role>` | Read / Edit | `<requirement>` | — |
| Sharing set (external) | `<profiles>` | Read / Edit | `<objectField → userField mapping>` | `sharingSets/` |
| Apex managed sharing | `<custom RowCause>` | Read / Edit | `<why no declarative path exists>` | `classes/` |
| Manual sharing | `<who may grant>` | Read / Edit | Exception only — with a review date | — |

## Bypasses and Narrowing

| Grant | Held by | Justification | Reviewed |
|-------|---------|---------------|----------|
| Object `View All` | `<permission set>` | `<why>` | `<date>` |
| Object `Modify All` | `<permission set>` | `<why>` | `<date>` |
| `View All Data` / `Modify All Data` | `<permission set>` | `<why>` | `<date>` |
| Restriction rule | `<rule name>` | `<what it removes>` | `<date>` |

## Risk Checks

- [ ] OWD is the most restrictive the business can live with, and every grant is more permissive than it
- [ ] `doesIncludeBosses` is set deliberately on every group and queue receiving a grant
- [ ] `includeRecordsOwnedByAll` decided per criteria rule (it cannot be edited after creation)
- [ ] No unnecessary `View All` / `Modify All`, and each remaining one has a named owner and review date
- [ ] Repeated manual sharing pattern identified or ruled out
- [ ] Public group membership exists in the target org — the deployment does not carry it
- [ ] Experience Cloud access modelled with a sharing set, not the role hierarchy, if applicable
- [ ] Access proved with a `UserRecordAccess` query for a real user and record, and explained by a `__Share` row
- [ ] Troubleshooting path documented for both "too much" and "too little" access
