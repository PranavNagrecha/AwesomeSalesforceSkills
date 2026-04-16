# Apex shared templates

Canonical Apex building blocks. Deploy these to any SFDX project and the
rest of the skill library assumes they exist.

## Dependency order (deploy bottom-up)

```
Application_Log__c                              ← custom_objects/
    └── ApplicationLogger.cls
         ├── SecurityUtils.cls
         ├── HttpClient.cls
         └── BaseService.cls

Trigger_Setting__mdt + Logger_Setting__mdt      ← cmdt/
    └── TriggerControl.cls
         └── TriggerHandler.cls
              └── <your per-object handler subclasses>

BaseSelector.cls (standalone)
BaseDomain.cls  (standalone)
```

## Minimum to deploy for a new project

```bash
# From repo root, cherry-pick what you need:
cp -r templates/apex/custom_objects/*      force-app/main/default/objects/
cp -r templates/apex/cmdt/*__mdt.object-meta.xml  force-app/main/default/objects/
cp -r templates/apex/cmdt/fields/*         force-app/main/default/objects/<cmdt>/fields/

cp templates/apex/*.cls                    force-app/main/default/classes/
cp templates/apex/*.cls-meta.xml           force-app/main/default/classes/

cp -r templates/apex/tests/*.cls           force-app/main/default/classes/
cp -r templates/apex/tests/*.cls-meta.xml  force-app/main/default/classes/

sf project deploy start
```

## File reference

| File | What it is | When to use |
|---|---|---|
| `TriggerHandler.cls` | Base class with dispatch, recursion depth, skipOnce | Every object's trigger handler extends this |
| `TriggerControl.cls` | Reads `Trigger_Setting__mdt` + `Bypass_All_Triggers` permission | Called from inside `TriggerHandler.run()` — usually don't call directly |
| `BaseDomain.cls` | Domain layer — logic scoped to one SObject's records | When handler methods exceed ~30 lines |
| `BaseService.cls` | Service layer — cross-object orchestration + DML | When domain logic spans multiple objects |
| `BaseSelector.cls` | All SOQL, `WITH USER_MODE` by default | Every object gets its own selector subclass |
| `ApplicationLogger.cls` | Logging façade → `Application_Log__c` | Replace every `System.debug` and `try/catch` with this |
| `SecurityUtils.cls` | CRUD/FLS assertions + `stripInaccessible` | Any code touching user-supplied data |
| `HttpClient.cls` | Named-Credential-aware HTTP wrapper | Any outbound callout |
| `tests/TestDataFactory.cls` | Bulk-only factory for standard SObjects | Every test class uses this |
| `tests/TestRecordBuilder.cls` | Fluent builder for arbitrary SObjects | One-off records with many overrides |
| `tests/MockHttpResponseGenerator.cls` | `HttpCalloutMock` with routing + sequencing | Any test with a callout |
| `tests/TestUserFactory.cls` | Users for `System.runAs(...)` blocks | Sharing / FLS / CRUD tests |
| `tests/BulkTestPattern.cls` | Reference template — copy and rename | Starting a new handler/service test class |

## What these templates expect you to do

- Use `WITH USER_MODE` in SOQL (Summer '23+). BaseSelector does this by default.
- Assign the `Bypass_All_Triggers` Custom Permission to your data-load user.
- Create a Logger_Setting__mdt row named `Default` with `Minimum_Severity__c = 'INFO'`.
- Treat logger failures as non-fatal (`Database.insert(logs, false)`).
- Never edit these files in your downstream project without renaming — you'll
  fight every upstream change.
