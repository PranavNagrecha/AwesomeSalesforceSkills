# Shared Templates

**Canonical, copy-pasteable building blocks that every skill references.**

Each skill in this repo explains *how* to do something. These templates are
*the* implementation the skill points to — one version of each idiom across
the entire library.

## Why this layer exists

Before shared templates, each skill had to inline its own example of
`TriggerHandler`, `TestDataFactory`, `wire(...)` pattern, etc. That meant:

- AI tools reading three skills saw three subtly different versions and
  merged them incorrectly.
- Consumers could not test the skill's guidance without re-typing the whole
  scaffold first.
- When a pattern evolved (e.g. `WITH USER_MODE` over `with sharing`), every
  skill had to be rewritten.

Now every skill can say *"see `templates/apex/TriggerHandler.cls`"* and both
the human and the AI get the same reference implementation.

## Layout

```
templates/
├── apex/
│   ├── TriggerHandler.cls           ← dispatch + depth + bypass
│   ├── TriggerControl.cls           ← activation bypass via Custom Metadata
│   ├── BaseDomain.cls               ← FFLIB-lite domain layer
│   ├── BaseService.cls              ← transaction-aware service layer
│   ├── BaseSelector.cls             ← all SOQL, WITH USER_MODE by default
│   ├── ApplicationLogger.cls        ← standard log façade → Application_Log__c
│   ├── SecurityUtils.cls            ← CRUD/FLS + stripInaccessible helpers
│   ├── HttpClient.cls               ← Named Credential + retry + timeout
│   ├── cmdt/                        ← Trigger_Setting__mdt + Logger_Setting__mdt
│   ├── custom_objects/              ← Application_Log__c and its fields
│   └── tests/
│       ├── TestDataFactory.cls
│       ├── TestRecordBuilder.cls
│       ├── MockHttpResponseGenerator.cls
│       ├── TestUserFactory.cls
│       └── BulkTestPattern.cls      ← reference bulk test to copy+rename
├── lwc/
│   ├── jest.config.js
│   ├── component-skeleton/          ← full LWC with tests
│   └── patterns/
│       ├── wireServicePattern.js
│       ├── imperativeApexPattern.js
│       └── ldsRecordEditForm.html
├── flow/
│   ├── RecordTriggered_Skeleton.flow-meta.xml
│   ├── FaultPath_Template.md
│   └── Subflow_Pattern.md
└── agentforce/
    ├── AgentSkeleton.json
    ├── AgentActionSkeleton.cls
    └── AgentTopic_Template.md
```

## How to use these in your SFDX project

1. Copy the files you need into your SFDX project. Structure maps directly:
   - `templates/apex/*.cls` + `-meta.xml` → `force-app/main/default/classes/`
   - `templates/apex/cmdt/` → `force-app/main/default/customMetadata/` (and the
     `*__mdt.object-meta.xml` → `force-app/main/default/objects/`)
   - `templates/apex/custom_objects/*.object-meta.xml` → `force-app/main/default/objects/`
   - `templates/lwc/component-skeleton/` → `force-app/main/default/lwc/componentSkeleton/`
   - `templates/flow/*.flow-meta.xml` → `force-app/main/default/flows/`
2. Rename the component / class to match your concern (`ComponentSkeleton` →
   `AccountTile`, `BulkTestPattern` → `AccountTriggerHandlerTest`, etc.).
3. Deploy with `sf project deploy start`.

## Versioning

- All Apex classes target `apiVersion 64.0` (Spring '26). Adjust `-meta.xml`
  on copy if you're on an older release.
- LWC jest config tracks `@salesforce/sfdx-lwc-jest` defaults.
- Breaking changes to any template are called out in `CHANGELOG.md` (to be added).

## What's *not* here

- Business logic. Every template is scaffolding — none encodes a specific
  use case.
- Managed-package namespace prefixes. Add your namespace at copy time.
- Auto-generated scaffolds. This is the canonical hand-written reference —
  `scripts/new_skill.py` scaffolds *skills*, not source code.

## Relationship to `skills/<domain>/<skill-name>/templates/`

- **This folder (`templates/`)** — canonical, cross-skill, reused by many
  skills. Change requires a `validate_repo.py` run and affects multiple skills.
- **`skills/.../templates/`** — skill-specific artifacts (e.g. a particular
  trigger framework's `[ObjectName]Trigger.trigger` placeholder). Changes
  local to one skill.

If a skill-local template starts being referenced by a second skill, promote
it up to `templates/`.
