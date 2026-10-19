# Worked Example — Three-Wave CDS Release for Account and Opportunity

A platform-native FSC org gets Compliant Data Sharing on Account and Opportunity with two participant roles. Person accounts are already enabled (checked with `SELECT Id FROM RecordType WHERE SobjectType='Account' AND IsPersonType=true`), and the Account and Opportunity OWDs were set to Private last weekend. The Background Jobs page showed that recalculation as complete before wave 1 started.

## Source tree

```text
force-app/main/default/
├── objects/Account/recordTypes/Household.recordType-meta.xml
├── settings/Industries.settings-meta.xml
└── participantRoles/
    ├── Advisor.participantRole-meta.xml
    └── DealLead.participantRole-meta.xml
```

`Industries.settings` is the single file that holds every `IndustriesSettings` value. Each `ParticipantRole` gets its own file in `participantRoles/`. Neither one goes under `customMetadata/`.

## Wave manifests

Each wave is a separate `sf project deploy start --manifest <file> --target-org <alias>`, and a wave starts only after the previous one passes its gate.

```xml
<!-- wave1-package.xml: structure only -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Account.Household</members>
        <name>RecordType</name>
    </types>
    <version>67.0</version>
</Package>
```

```xml
<!-- wave2-package.xml: CDS flags. Industries.settings carries
     enableCompliantDataSharingForAccount and enableCompliantDataSharingForOpportunity = true -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Industries</members>
        <name>Settings</name>
    </types>
    <version>67.0</version>
</Package>
```

```xml
<!-- wave3-package.xml: roles, only after both flags are confirmed in the target -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Advisor</members>
        <members>DealLead</members>
        <name>ParticipantRole</name>
    </types>
    <version>67.0</version>
</Package>
```

## The two roles

| File | masterLabel | parentObject | defaultAccessLevel | isActive | Flag that must be true |
|---|---|---|---|---|---|
| `Advisor.participantRole-meta.xml` | Advisor | Account | Read | true | `enableCompliantDataSharingForAccount` |
| `DealLead.participantRole-meta.xml` | Deal Lead | Opportunity | Edit | true | `enableCompliantDataSharingForOpportunity` |

## Gates

1. **Before wave 1:** run `python3 skills/devops/fsc-deployment-patterns/scripts/check_fsc_deployment_patterns.py --manifest-dir force-app/main/default --strict`. On this tree it exits 0 and prints one NOTE about the household record type, which tells you to run the person-account query first. If someone had left `DealLead` with `isActive` false, or with no Opportunity flag in `Industries.settings`, `--strict` would exit 1 before anything was deployed.
2. **After wave 2:** open Setup and confirm CDS shows as on for Account and Opportunity. A deploy that succeeds proves only that the settings file was accepted.
3. **After wave 3:** add `Advisor` to one test account, then check `SELECT UserOrGroupId, RowCause FROM AccountShare WHERE AccountId = '<test id>'` for a row that names the advisor. Log in as that advisor and open the record. Do the same on a test opportunity for `DealLead`.
4. **Existing records:** run the CDS share recalculation for accounts and opportunities created before wave 2. Activating CDS doesn't backfill their share rows (Gotcha 2).

## What the checker would have caught in the first draft

The first draft of this release modelled the roles as `customMetadata/ParticipantRole.Advisor.md-meta.xml` and put all three waves in one `package.xml`. The checker printed an ERROR for the custom-metadata file and for the `CustomMetadata` member, plus a WARN because RecordType and ParticipantRole were in one manifest. That WARN alone was enough to fail the build under `--strict`.
