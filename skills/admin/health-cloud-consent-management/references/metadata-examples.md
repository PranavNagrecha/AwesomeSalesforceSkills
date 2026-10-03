# Metadata Examples: Health Cloud Consent Management

The settings that make consent safe to operate, as deployable files: the Data Protection and Privacy switch under change control, evidence capture for electronic authorization, Health Cloud portal sharing for consent forms, and field history on the consent status for the "update with history" withdrawal design.

Grounding: Metadata API Developer Guide, PartyDataModelSettings (`api_meta L123939-123995`), PrivacySettings (`api_meta L124598-124700`), IndustriesSettings Health Cloud fields (`api_meta L119538-119546`), CustomField `trackHistory` and CustomObject `enableHistory` (`api_meta L43675-43682`, `L42040`); Object Reference, consent objects (`object_reference L45946-46560`).

Licence gate: the consent objects require Data Protection and Privacy. `IndustriesSettings` fields are available only in editions where Health Cloud is enabled. `PrivacySettings` needs the Customize Application or Modify Data Classification permission.

## 1. Keep consent management on

`force-app/main/default/settings/PartyDataModel.settings-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PartyDataModelSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableAutoSelectIndividualOnMerge>true</enableAutoSelectIndividualOnMerge>
    <enableConsentManagement>true</enableConsentManagement>
</PartyDataModelSettings>
```

`enableConsentManagement` must stay `true`: "Setting this field to false purges all data protection details, such as privacy preferences and stored consent forms." `enableAutoSelectIndividualOnMerge` keeps the most recently modified privacy record when patient records are merged, instead of asking the user. UNVERIFIED (2026-10-03): the guide's sample uses the element `enableConsentManagementEnabled` while its field table says `enableConsentManagement`; retrieve `Settings:PartyDataModel` from your org and keep the element name it returns.

## 2. Capture evidence for electronic authorization

`force-app/main/default/settings/Privacy.settings-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PrivacySettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <authorizationCaptureBrowser>true</authorizationCaptureBrowser>
    <authorizationCaptureEmail>true</authorizationCaptureEmail>
    <authorizationCaptureIp>true</authorizationCaptureIp>
    <authorizationCaptureLocation>false</authorizationCaptureLocation>
    <authorizationLockingAndVersioning>true</authorizationLockingAndVersioning>
</PrivacySettings>
```

| Field | Value | Reason |
|---|---|---|
| `authorizationCaptureBrowser`, `authorizationCaptureEmail`, `authorizationCaptureIp` | `true` | Evidence for electronic signatures (API 59.0; default false) |
| `authorizationCaptureLocation` | `false` | Location is more personal data than most programs need; enable only if compliance requires it |
| `authorizationLockingAndVersioning` | `true` | Locking and versioning for authorization consent records (API 59.0) |

## 3. Health Cloud portal sharing for consent forms

`force-app/main/default/settings/Industries.settings-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<IndustriesSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableAuthorizationCustomSharingPCU>false</enableAuthorizationCustomSharingPCU>
</IndustriesSettings>
```

Set it to `true` only when Customer Community Plus users must share Authorization Form Texts and Data Use Purpose records "with Accounts, Contracts, and Users specified in the Information Authorization Request record". Retrieve `Settings:Industries` first and merge, because the file holds every Industries setting.

## 4. History on consent status (for the "update with history" withdrawal design)

`force-app/main/default/objects/AuthorizationFormConsent/AuthorizationFormConsent.object-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableHistory>true</enableHistory>
</CustomObject>
```

`force-app/main/default/objects/AuthorizationFormConsent/fields/Status.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Status</fullName>
    <trackHistory>true</trackHistory>
</CustomField>
```

`trackHistory` is available for standard object fields that are picklist or lookup fields, and requires `enableHistory` on the object. `AuthorizationFormConsentHistory` is listed as an associated object. UNVERIFIED (2026-10-03): deploying a standard object file that contains only `enableHistory` is a common partial-definition pattern; retrieve `CustomObject:AuthorizationFormConsent` and merge rather than overwrite if your project already tracks it.

## 5. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>AuthorizationFormConsent</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>AuthorizationFormConsent.Status</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Industries</members>
        <members>PartyDataModel</members>
        <members>Privacy</members>
        <name>Settings</name>
    </types>
    <version>67.0</version>
</Package>
```

## Deploy order

1. `Settings: PartyDataModel` (consent objects exist only with Data Protection and Privacy on).
2. `Settings: Privacy` and `Settings: Industries`.
3. `CustomObject` and `CustomField` for history.
4. Consent records (purposes, forms, texts, data uses) by data load or the script in `examples.md`.

## Verification

- `SELECT Id FROM AuthorizationForm LIMIT 1` succeeds.
- After a test signature on an electronic form, the captured details are present.
- Changing a test consent from `Signed` to `Rejected` creates an `AuthorizationFormConsentHistory` row.
- A diff of `PartyDataModel.settings-meta.xml` that sets consent management to false is rejected in code review.
