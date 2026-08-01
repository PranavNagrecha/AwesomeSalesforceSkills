# Apex shared templates

Canonical Apex building blocks. Deploy these to any SFDX project and the
rest of the skill library assumes they exist.

## Read this before you copy anything

Two of these classes depend on declarative metadata:

| Class | Depends on | Shipped here? |
|---|---|---|
| `TriggerControl.cls` | `Trigger_Setting__mdt` + 3 fields | Yes — `cmdt/Trigger_Setting__mdt/` |
| `TriggerControl.cls` | `TriggerControl_BypassAll` Custom Permission | **No** — you must create it, see below |
| `ApplicationLogger.cls` | `Application_Log__c` + 8 fields | Yes — `custom_objects/` |
| `ApplicationLogger.cls` | `Logger_Setting__mdt` + 1 field | Yes — `cmdt/Logger_Setting__mdt/` |
| `ApplicationLogger.cls` | a `Logger_Setting__mdt` record named `Default` | **No** — you must create it, see below |

`TriggerControl.cls` will not compile until `Trigger_Setting__mdt` and its three
fields exist in the target org. Deploy the metadata before the classes.

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

## Metadata shipped here

These directories are already in SFDX **source format** — one folder per object,
fields decomposed into a `fields/` subfolder. Copy the object folder whole; do not
flatten it, and do not merge the two `fields/` folders.

```
cmdt/
├── Trigger_Setting__mdt/
│   ├── Trigger_Setting__mdt.object-meta.xml
│   └── fields/
│       ├── Object_API_Name__c.field-meta.xml   Text(255), required
│       ├── Handler_Class__c.field-meta.xml     Text(255), required
│       └── Is_Active__c.field-meta.xml         Checkbox, default true
└── Logger_Setting__mdt/
    ├── Logger_Setting__mdt.object-meta.xml
    └── fields/
        └── Minimum_Severity__c.field-meta.xml  Restricted picklist

custom_objects/
├── Application_Log__c.object-meta.xml
└── fields/                                     8 fields — see note below
```

> `custom_objects/` is still laid out flat (`Application_Log__c.object-meta.xml`
> beside a bare `fields/`). Nest it as `objects/Application_Log__c/{Application_Log__c.object-meta.xml, fields/}`
> when you copy it into your package directory.

## Minimum to deploy for a new project

```bash
# From repo root. Note the per-object nesting — source format requires it.
mkdir -p force-app/main/default/objects/Application_Log__c
cp    templates/apex/custom_objects/Application_Log__c.object-meta.xml \
      force-app/main/default/objects/Application_Log__c/
cp -r templates/apex/custom_objects/fields \
      force-app/main/default/objects/Application_Log__c/

# Custom metadata types already have the right shape — copy the folders whole.
cp -r templates/apex/cmdt/Trigger_Setting__mdt  force-app/main/default/objects/
cp -r templates/apex/cmdt/Logger_Setting__mdt   force-app/main/default/objects/

cp templates/apex/*.cls                    force-app/main/default/classes/
cp templates/apex/*.cls-meta.xml           force-app/main/default/classes/

cp templates/apex/tests/*.cls              force-app/main/default/classes/
cp templates/apex/tests/*.cls-meta.xml     force-app/main/default/classes/

sf project deploy start
```

## You must create these two components yourself

### 1. `TriggerControl_BypassAll` Custom Permission

`TriggerControl.cls` calls
`FeatureManagement.checkPermission('TriggerControl_BypassAll')`. This is the
break-glass switch: assign it to a data-load or incident-response user and every
handler short-circuits.

**Why this is not shipped:** Custom Permissions are org-level security metadata.
Silently deploying a bypass-all-triggers permission into someone's org is not
something a template should do. Create it deliberately.

Save as `force-app/main/default/customPermissions/TriggerControl_BypassAll.customPermission-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomPermission xmlns="http://soap.sforce.com/2006/04/metadata">
    <isLicensed>false</isLicensed>
    <label>Trigger Control: Bypass All</label>
    <description>Break-glass. When assigned, TriggerControl.isActive() returns false for every handler, disabling all Apex trigger logic for this user. Grant only for supervised data loads and incident response, and revoke immediately after.</description>
</CustomPermission>
```

Then assign it through a Permission Set — never a Profile, and never to a
Permission Set that is assigned broadly.

**If you skip this step, nothing breaks.** `TriggerControl.hasBypassAllPermission()`
wraps the call in a try/catch and fails closed (bypass unavailable, triggers stay
on). This guard is required, not decorative: since Winter '20,
`FeatureManagement.checkPermission` throws `System.NoDataFoundException` for an
API name that does not exist in the org rather than returning `false`, and
`TriggerControl.isActive()` is the first thing `TriggerHandler.run()` calls — so
an unguarded call would fatal every trigger in the org.

### 2. A `Logger_Setting__mdt` record named `Default`

`ApplicationLogger.getMinimumSeverity()` calls
`Logger_Setting__mdt.getInstance('Default')`. Custom metadata *records* are a
separate metadata type (`customMetadata/`) from the type definition, so the record
is not part of the object folder.

Save as `force-app/main/default/customMetadata/Logger_Setting.Default.md-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <label>Default</label>
    <protected>false</protected>
    <values>
        <field>Minimum_Severity__c</field>
        <value xsi:type="xsd:picklist">INFOL</value>
    </values>
</CustomMetadata>
```

`Minimum_Severity__c` is a picklist, so the record uses `xsi:type="xsd:picklist"`,
not `xsd:string`.

The API values are `DEBUGL`, `INFOL`, `WARN`, `ERROR`, `FATAL` — they must match
the `ApplicationLogger.Severity` enum constants exactly, because
`getMinimumSeverity()` does `Severity.valueOf(setting.Minimum_Severity__c.toUpperCase())`. The
labels shown in Setup are the unsuffixed `DEBUG` and `INFO`; do not write those
into the record. If the record is missing, or the value does not resolve,
`ApplicationLogger` falls back to `INFOL`.

## Populating `Trigger_Setting__mdt`

Records are optional. `TriggerControl.isActive()` returns `true` on a cache miss,
so you only need a record for a handler you want to be able to switch **off**.
The lookup key is `Object_API_Name__c + '::' + Handler_Class__c`, lower-cased —
nothing enforces that pair to be unique, so keep one record per handler by
convention.

```xml
<!-- customMetadata/Trigger_Setting.Account_AccountTriggerHandler.md-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <label>Account / AccountTriggerHandler</label>
    <protected>false</protected>
    <values>
        <field>Object_API_Name__c</field>
        <value xsi:type="xsd:string">Account</value>
    </values>
    <values>
        <field>Handler_Class__c</field>
        <value xsi:type="xsd:string">AccountTriggerHandler</value>
    </values>
    <values>
        <field>Is_Active__c</field>
        <value xsi:type="xsd:boolean">true</value>
    </values>
</CustomMetadata>
```

## File reference

| File | What it is | When to use |
|---|---|---|
| `TriggerHandler.cls` | Base class with dispatch, recursion depth, skipOnce | Every object's trigger handler extends this |
| `TriggerControl.cls` | Reads `Trigger_Setting__mdt` + `TriggerControl_BypassAll` permission | Called from inside `TriggerHandler.run()` — usually don't call directly |
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

- Use `WITH USER_MODE` in SOQL (Spring '23+, API 57.0). BaseSelector does this by
  default. `WITH SECURITY_ENFORCED` is removed in API 67.0 (Summer '26) — do not
  reintroduce it.
- Create the `TriggerControl_BypassAll` Custom Permission and assign it to your
  data-load user (section above).
- Create a `Logger_Setting__mdt` record named `Default` with
  `Minimum_Severity__c = 'INFOL'` (section above).
- Treat logger failures as non-fatal. `ApplicationLogger.flush()` currently does an
  all-or-nothing `insert buffer` inside a try/catch, so one bad row loses the whole
  batch — switch it to `Database.insert(buffer, false)` if you need partial success.
- Never edit these files in your downstream project without renaming — you'll
  fight every upstream change.
