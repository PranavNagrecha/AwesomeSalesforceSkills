# Data Seeding For Testing — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `data-seeding-for-testing`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- **Target org type:** [ ] Scratch Org  [ ] Developer Sandbox  [ ] Partial Sandbox  [ ] Full Sandbox
- **Record volume:** (estimated count and relationship depth)
- **PII sensitivity:** (does data contain real personal information?)
- **CI integration:** (will seeding run in an automated pipeline?)

## Seeding Layer Decision

| Layer | Use When |
|---|---|
| Apex `@testSetup` | Unit/integration tests in Apex |
| `sf data import tree` plan | Scratch org or dev sandbox, < 200MB |
| CumulusCI dataset | Partial/full sandbox, production-sourced, PII masking required |
| Snowfakery recipe | Fully synthetic data, large volume, no production source |
| Scratch Org Snapshot | Pre-bake seeded state for repeated CI use |

**Selected layer:** _______________

**Reason:** _______________

## sf data import tree Plan (if applicable)

```json
[
  {"sobject": "ParentObject__c", "saveRefs": true, "resolveRefs": false, "files": ["ParentObject.json"]},
  {"sobject": "ChildObject__c", "saveRefs": false, "resolveRefs": true, "files": ["ChildObject.json"]}
]
```

## Checklist

- [ ] No `@isTest(SeeAllData=true)` mixed with `@testSetup` in the same class
- [ ] Plan JSON has parent objects before child objects
- [ ] All `@sf_reference_id` values in child JSON match parent `referenceId` values
- [ ] Plan total JSON size is under 200MB
- [ ] PII masking configured for any data sourced from production
- [ ] Query fixture confirmed: skill appears in top 3 results for a practitioner search

## Notes

(Record any deviations from the standard pattern and why.)
