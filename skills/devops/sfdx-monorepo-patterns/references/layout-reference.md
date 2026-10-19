# Layout Reference — SFDX Monorepo

## Directory tree

```text
repo/
├── .forceignore                       <- the only .forceignore unless a package truly needs its own
├── sfdx-project.json
├── config/                            <- scratch and sandbox definition files
├── tools/                             <- NOT in packageDirectories: seeders, scripts, one-offs
└── packages/
    ├── base-utils/main/default/
    │   ├── classes/                   <- trigger framework, logging, test data factory
    │   └── objects/Customer_Profile__c/
    │       ├── Customer_Profile__c.object-meta.xml   <- object definition: owned here only
    │       └── fields/Tier__c.field-meta.xml
    ├── sales-core/main/default/
    │   └── objects/Customer_Profile__c/fields/Sales_Region__c.field-meta.xml
    └── service-core/main/default/
        └── objects/Customer_Profile__c/fields/Support_Level__c.field-meta.xml
```

`sales-core` and `service-core` each declare a dependency on `base-utils`; neither contains `Customer_Profile__c.object-meta.xml`.

## An extension field file

The field file in `sales-core` is an ordinary `CustomField` component; nothing in it names the package — ownership comes from which directory it sits in and from the declared dependency:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- packages/sales-core/main/default/objects/Customer_Profile__c/fields/Sales_Region__c.field-meta.xml -->
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Sales_Region__c</fullName>
    <label>Sales Region</label>
    <length>80</length>
    <required>false</required>
    <type>Text</type>
</CustomField>
```

## `.forceignore` placement

| Layout | Effect |
|---|---|
| One root `.forceignore` | Applies to every package directory |
| Root file + `packages/sales-core/.forceignore` | Files under `sales-core` use only the `sales-core` file; the root rules no longer apply to them |

If a package needs extra rules, copy the root rules it still needs into its own file. The checker prints the root patterns a per-package file omits.

## Ownership table (fill in)

| Shared custom object | Owning directory | Directories with fields on it | Dependency declared? |
|---|---|---|---|
| `Customer_Profile__c` | `packages/base-utils` | `sales-core`, `service-core` | yes / yes |
| | | | |
