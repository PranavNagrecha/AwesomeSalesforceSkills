# Metadata Examples — Picklist and Value Sets

Four metadata types carry picklist values, and they are not interchangeable:

| Type | What it is | Guide |
|---|---|---|
| `GlobalValueSet` | "the metadata for a global picklist value set, which is the set of shared values that custom picklist fields can use. A global value set isn't a field itself." | api_meta.txt:79344–79346 |
| `CustomField` → `valueSet` | The picklist on one field. Either points at a global set or defines its own values | api_meta.txt:43704–43713 |
| `StandardValueSet` | "the set of values in a standard picklist field" — `Industry`, `LeadSource`, `CaseStatus`, `OpportunityStage` | api_meta.txt:130740–130741 |
| `GlobalValueSetTranslation` | Per-language labels for a global set's values | api_meta.txt:79429–79431 |

Field *dependency design* — which controlling value maps to which dependent value, and why the API
does not enforce it — is `admin/field-dependency-and-controlling`. This file owns only the shape of
the `valueSettings` element (§6). Per-record-type value visibility is
`admin/record-types-and-page-layouts`. Creating the field itself (type, FLS, help text) is
`admin/custom-field-creation`; nothing below repeats its inline-picklist example.

## Where the files live

| Component | DX source path | Root element |
|---|---|---|
| `GlobalValueSet` | `globalValueSets/Renewal_Risk_Band__gvs.globalValueSet-meta.xml` | `GlobalValueSet` |
| `StandardValueSet` | `standardValueSets/OpportunityStage.standardValueSet-meta.xml` | `StandardValueSet` |
| `CustomField` | `objects/Opportunity/fields/Renewal_Risk__c.field-meta.xml` | `CustomField` |
| `GlobalValueSetTranslation` | `globalValueSetTranslations/Renewal_Risk_Band__gvs-fr.globalValueSetTranslation-meta.xml` | `GlobalValueSetTranslation` |

Suffixes and folders are the guide's: `.globalValueSet` in `globalValueSets`
(api_meta.txt:79354), `.standardValueSet` in `standardValueSets` (api_meta.txt:130752),
`.globalValueSetTranslation` in `globalValueSetTranslations`, named
`ValueSetName-lang.globalValueSetTranslation` (api_meta.txt:79444–79447).

**The `__gvs` suffix is not optional.** "Any global value set created in API version 57.0 or later
automatically has the `__gvs` suffix appended to the developer name. When you make any CRUD-based
call with the GlobalValueSet type, you must append the suffix to the fullName field when you
reference the type" (api_meta.txt:79419–79421). A `package.xml` member of `Renewal_Risk_Band`
misses a set created in 57.0+; the member is `Renewal_Risk_Band__gvs`.

## The elements this skill cares about

| Element | On | What the guide says | Line |
|---|---|---|---|
| `masterLabel` | `GlobalValueSet` | "Required. A global value set's name … Appears as Label in the user interface." | 79371–79373 |
| `customValue` | `GlobalValueSet` | "Requires at least one value… A global value set can have up to 1,000 total values, including inactive values." | 79363–79367 |
| `sorted` | `GlobalValueSet`, `StandardValueSet`, `valueSetDefinition` | "Required. Indicates whether a global value set is sorted in alphabetical order. By default this value is false." | 79374–79376 |
| `description` | `GlobalValueSet` | "It's useful to state the global value set's purpose and which objects it's intended for. Limit: 255 characters." | 79368–79370 |
| `fullName` | `CustomValue` | Inherited from `Metadata`; the stored API value | 47476–47477 |
| `label` | `CustomValue` | "If you don't specify the label when creating a value it defaults to the API name." API 39.0+ | 47527–47528 |
| `default` | `CustomValue` | "Required… This field is set to true by default." | 47513–47516 |
| `isActive` | `CustomValue` | "The default value is true. Users can select only active values from a picklist." | 47521–47526 |
| `color` | `CustomValue` | "The color assigned to the picklist value when it's used in charts on reports and dashboards… hexadecimal format; for example, #FF6600." | 47499–47503 |
| `description` | `CustomValue` | "Limit: 255 characters." | 47517–47520 |
| `restricted` | `ValueSet` | "Whether the picklist's values are limited to only the values defined by a Salesforce admin." | 45847–45849 |
| `valueSetName` | `ValueSet` | "The masterLabel of the global value set to be used for this picklist field." | 45853 |
| `valueSetDefinition` | `ValueSet` | Holds `sorted` plus the local `value` list | 45850–45852, 45862–45869 |
| `controllingField` | `ValueSet` | "The fullname of the controlling field if this is a dependent picklist." | 45843–45846 |
| `valueSettings` | `ValueSet` | "You can add field dependency values via the Metadata API but not remove them." | 45855–45860 |
| `forecastCategory` | `StandardValue` | Enum: `Omitted`, `Pipeline`, `BestCase`, `Forecast`, `Closed`. "only relevant for the standard Stage field in opportunities" | 47578–47586 |
| `probability` | `StandardValue` | "only relevant for the standard Stage field in opportunities" | 47593–47596 |
| `won` | `StandardValue` | "associated with a closed or won status… only relevant for the standard Stage field in opportunities" | 47611–47614 |
| `closed` | `StandardValue` | "associated with a closed status… only relevant for the standard Status field in cases and tasks" | 47542–47546 |
| `converted` | `StandardValue` | "relevant for only the standard Lead Status field in leads" | 47547–47554 |

---

## 1. A global value set — five values, one inactive, one default, chart colours

```xml
<?xml version="1.0" encoding="UTF-8"?>
<GlobalValueSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>Renewal Risk Band</masterLabel>
    <description>Renewal risk band shared by Account, Opportunity, and Contract. Owned by RevOps; changes go through the quarterly picklist review.</description>
    <sorted>false</sorted>
    <customValue>
        <fullName>Low</fullName>
        <label>Low</label>
        <default>true</default>
        <isActive>true</isActive>
        <color>#4BCA81</color>
        <description>No open escalations, sponsor engaged in the last 90 days.</description>
    </customValue>
    <customValue>
        <fullName>Medium</fullName>
        <label>Medium</label>
        <default>false</default>
        <isActive>true</isActive>
        <color>#FFB75D</color>
    </customValue>
    <customValue>
        <fullName>High</fullName>
        <label>High</label>
        <default>false</default>
        <isActive>true</isActive>
        <color>#E74C3C</color>
    </customValue>
    <customValue>
        <fullName>Churn_Confirmed</fullName>
        <label>Churn Confirmed</label>
        <default>false</default>
        <isActive>true</isActive>
        <color>#7F1D1D</color>
    </customValue>
    <customValue>
        <fullName>Tier_1</fullName>
        <label>Legacy — Tier 1</label>
        <default>false</default>
        <isActive>false</isActive>
    </customValue>
</GlobalValueSet>
```

How to read it:

- The file name carries the developer name (`Renewal_Risk_Band__gvs.globalValueSet-meta.xml`); the
  `masterLabel` inside carries the human label. They are different strings and the guide treats
  them as different things (api_meta.txt:79371–79373, 79419–79421).
- `fullName` is the stored API value. `label` is what the user sees. `Tier_1` / `Legacy — Tier 1`
  is the shape a renamed value ends up in: the label moved, the stored key did not. The Object
  Reference is blunt about which one code uses — "Always use the value when inserting or updating a
  field. The `query()` call always returns the value, not the label"
  (object_reference.txt:2372–2374).
- `isActive` `false` on `Tier_1` retires it. It stays in the file. **Omitting a value is not the
  same as leaving it out of the UI**: "If picklist values are missing from a component definition,
  they get deactivated when deployed. Deactivation occurs for picklist values of both standard and
  custom fields" (api_meta.txt:47482–47483). A hand-trimmed file silently deactivates everything it
  forgot.
- Exactly one `default` is `true`. `default` is required on every `CustomValue` and "is set to
  `true` by default" (api_meta.txt:47513–47516) — leave it out on four of five values and the
  deploy does not do what the file looks like it says.
- `color` only affects report and dashboard charts: "If a color isn't specified, it's assigned
  dynamically upon chart generation" (api_meta.txt:47499–47503). Dynamic assignment is why the same
  stage is green in one dashboard and orange in another.
- `sorted` `false` preserves `Low, Medium, High` order. `true` alphabetises to
  `Churn Confirmed, High, Low, Medium` — wrong for a risk ladder.

## 2. The custom field that consumes it

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Renewal_Risk__c</fullName>
    <label>Renewal Risk</label>
    <description>Renewal risk band. Values are managed centrally in the Renewal Risk Band global value set — do not add values here.</description>
    <type>Picklist</type>
    <required>false</required>
    <trackHistory>true</trackHistory>
    <valueSet>
        <restricted>true</restricted>
        <valueSetName>Renewal_Risk_Band__gvs</valueSetName>
    </valueSet>
</CustomField>
```

How to read it:

- There is **no value list here**. That is the point of a global set: "the global value set is
  inherited by any custom picklist field that uses that value set" (api_meta.txt:79363–79366).
  Adding a `valueSetDefinition` alongside `valueSetName` is invalid — "a ValueSet component has
  either a `valueSetDefinition` or a `valueName` specified, but never both"
  (api_meta.txt:43710–43713; the guide writes `valueName`, the element is `valueSetName`).
- `restricted` `true` is written explicitly even though the guide says the state is implied: "A
  custom picklist that uses a global value set is restricted. You can only add or remove values by
  editing the global value set" (api_meta.txt:43704–43711). Writing it makes the intent readable in
  a diff and makes the checker's WARN in `scripts/check_picklist_and_value_sets.py` meaningful.
  Unrestricted is the state that lets data loads invent values — see §7 of `references/gotchas.md`.
- The `valueSetName` value here is the developer name including `__gvs`. The guide's own field table
  calls this element "the `masterLabel` of the global value set" (api_meta.txt:45853) while the
  GlobalValueSet page says CRUD calls must carry the `__gvs`-suffixed developer name
  (api_meta.txt:79419–79421). **UNVERIFIED (2026-09-04):** the two statements were not reconciled
  against a live org in this session. If a deploy rejects `Renewal_Risk_Band__gvs`, retrieve the
  field from an org that already has it and copy the exact string the retrieve emits.

## 3. `StandardValueSet` — `OpportunityStage`

Standard picklists are not `CustomField` value sets. `Opportunity.StageName` is the standard value
set named `OpportunityStage` (api_meta.txt:142674). The names are case-sensitive
(api_meta.txt:141686).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<StandardValueSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <sorted>false</sorted>
    <standardValue>
        <fullName>Prospecting</fullName>
        <label>Prospecting</label>
        <default>true</default>
        <isActive>true</isActive>
        <forecastCategory>Pipeline</forecastCategory>
        <probability>10</probability>
        <closed>false</closed>
        <won>false</won>
    </standardValue>
    <standardValue>
        <fullName>Needs Analysis</fullName>
        <label>Needs Analysis</label>
        <default>false</default>
        <isActive>true</isActive>
        <forecastCategory>Pipeline</forecastCategory>
        <probability>20</probability>
        <closed>false</closed>
        <won>false</won>
    </standardValue>
    <standardValue>
        <fullName>Proposal/Price Quote</fullName>
        <label>Proposal/Price Quote</label>
        <default>false</default>
        <isActive>true</isActive>
        <forecastCategory>BestCase</forecastCategory>
        <probability>50</probability>
        <closed>false</closed>
        <won>false</won>
    </standardValue>
    <standardValue>
        <fullName>Negotiation/Review</fullName>
        <label>Negotiation/Review</label>
        <default>false</default>
        <isActive>true</isActive>
        <forecastCategory>Forecast</forecastCategory>
        <probability>80</probability>
        <closed>false</closed>
        <won>false</won>
    </standardValue>
    <standardValue>
        <fullName>Closed Won</fullName>
        <label>Closed Won</label>
        <default>false</default>
        <isActive>true</isActive>
        <forecastCategory>Closed</forecastCategory>
        <probability>100</probability>
        <closed>true</closed>
        <won>true</won>
    </standardValue>
    <standardValue>
        <fullName>Closed Lost</fullName>
        <label>Closed Lost</label>
        <default>false</default>
        <isActive>true</isActive>
        <forecastCategory>Omitted</forecastCategory>
        <probability>0</probability>
        <closed>true</closed>
        <won>false</won>
    </standardValue>
</StandardValueSet>
```

How to read it:

- `StandardValue` "extends the CustomValue metadata type and inherits all its fields"
  (api_meta.txt:47533–47534), so `fullName`, `label`, `default`, `isActive`, `color` and
  `description` are all legal here too. The stage-specific additions are `forecastCategory`,
  `probability`, `won` and `closed`.
- `forecastCategory` is an enum with exactly five members — `Omitted`, `Pipeline`, `BestCase`,
  `Forecast`, `Closed` (api_meta.txt:47578–47586). No other string deploys. `Closed Lost` maps to
  `Omitted`, not to `Closed`: `Closed` is the forecast bucket for revenue you have booked.
- A stage without `probability` and `forecastCategory` deploys as a stage the forecast cannot
  categorise. `scripts/check_picklist_and_value_sets.py` treats that as an ERROR.
- `<standardValue>` "must contain at least one picklist value. Otherwise, you receive an error"
  (api_meta.txt:130771–130772) — and the deactivate-by-omission rule of api_meta.txt:47482–47483
  applies here too, so a partial file is a mass deactivation.
- The guide's own sample for this type shows only `<fullName>` per value
  (api_meta.txt:130786–130800); the stage-specific elements come from the older `StageName` sample
  (api_meta.txt:44857–44884) and from the `StandardValue` field table.
- New values loaded this way are **invisible until each record type is edited**: "new picklist
  values loaded into your organization through the Metadata API don't display in the picklist UI by
  default. For users to see the new values, go to the Record Types list for the object containing
  the picklist field, click Edit, and add the new value to the Selected Fields list"
  (api_meta.txt:130774–130779). That step is `admin/record-types-and-page-layouts`.

## 4. `StandardValueSet` — `CaseStatus`

`Case.Status` is the standard value set `CaseStatus` (api_meta.txt:141982). Its distinguishing
element is `closed`, which is what drives "is this case resolved" everywhere except a formula you
wrote yourself.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<StandardValueSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <sorted>false</sorted>
    <standardValue>
        <fullName>New</fullName>
        <label>New</label>
        <default>true</default>
        <isActive>true</isActive>
        <closed>false</closed>
    </standardValue>
    <standardValue>
        <fullName>Working</fullName>
        <label>Working</label>
        <default>false</default>
        <isActive>true</isActive>
        <closed>false</closed>
    </standardValue>
    <standardValue>
        <fullName>Escalated</fullName>
        <label>Escalated</label>
        <default>false</default>
        <isActive>true</isActive>
        <closed>false</closed>
    </standardValue>
    <standardValue>
        <fullName>Waiting on Customer</fullName>
        <label>Waiting on Customer</label>
        <default>false</default>
        <isActive>true</isActive>
        <closed>false</closed>
    </standardValue>
    <standardValue>
        <fullName>Closed</fullName>
        <label>Closed</label>
        <default>false</default>
        <isActive>true</isActive>
        <closed>true</closed>
    </standardValue>
    <standardValue>
        <fullName>Closed as Duplicate</fullName>
        <label>Closed as Duplicate</label>
        <default>false</default>
        <isActive>true</isActive>
        <closed>true</closed>
    </standardValue>
</StandardValueSet>
```

How to read it:

- `closed` "indicates whether this value is associated with a closed status (true), or not (false).
  This field is only relevant for the standard Status field in cases and tasks"
  (api_meta.txt:47542–47546). It is the flag behind `Case.IsClosed`, so a status named `Resolved`
  with `closed` `false` leaves every "open cases" report counting it.
- The same field table adds a version caveat — "available in API version 16.0 and up to version
  36.0. In version 37.0, this field is in GlobalPicklistValue" (api_meta.txt:47544–47546) — while
  still listing `closed` under `StandardValue`, the type used by `StandardValueSet` from API 38.0.
  **UNVERIFIED (2026-09-04):** whether a v62 `StandardValueSet` deploy honours `<closed>` was not
  confirmed against a live org. Retrieve `StandardValueSet:CaseStatus` from the target org first and
  diff; if the retrieve omits `closed`, set the flag in Setup instead of in the file.
- `Waiting on Customer` is *not* closed. Teams that mark it closed to stop the SLA clock should stop
  the clock with Entitlements instead — `admin/business-hours-and-holidays`.

## 5. Translating a global value set

```xml
<?xml version="1.0" encoding="UTF-8"?>
<GlobalValueSetTranslation xmlns="http://soap.sforce.com/2006/04/metadata">
    <valueTranslation>
        <masterLabel>Low</masterLabel>
        <translation>Faible</translation>
    </valueTranslation>
    <valueTranslation>
        <masterLabel>Medium</masterLabel>
        <translation>Moyen</translation>
    </valueTranslation>
    <valueTranslation>
        <masterLabel>High</masterLabel>
        <translation>Élevé</translation>
    </valueTranslation>
    <valueTranslation>
        <masterLabel>Churn Confirmed</masterLabel>
        <translation><!-- Churn Confirmed --></translation>
    </valueTranslation>
</GlobalValueSetTranslation>
```

How to read it:

- The pairing key is `masterLabel` — "Required. The original (untranslated) name of a value in a
  global value set" (api_meta.txt:79466–79468). That is the value's **label**, not its `fullName`.
  Rename a label in §1 and every translation file silently stops matching.
- The empty `Churn Confirmed` entry is the guide's own convention for an untranslated value: "When
  a value isn't translated, its translation becomes a comment that's paired with its masterLabel"
  (api_meta.txt:79475–79476). Retrieves emit that shape; do not "fix" it by deleting the element.
- File name is `Renewal_Risk_Band__gvs-fr.globalValueSetTranslation-meta.xml`
  (api_meta.txt:79446–79447).

## 6. The `valueSettings` shape (dependency wiring only)

This is the element that makes a local picklist dependent. The **design** of the matrix — which
combinations are legal, why the API ignores them, how to enforce them — is
`admin/field-dependency-and-controlling`. What follows is only the XML shape so a generated file
parses.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Excerpt: the <valueSet> element of
     objects/Asset/fields/Model__c.field-meta.xml, shown inside its real
     <CustomField> root so the fragment parses on its own. -->
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Model__c</fullName>
    <label>Model</label>
    <type>Picklist</type>
    <valueSet>
        <restricted>true</restricted>
        <controllingField>Manufacturer__c</controllingField>
        <valueSetDefinition>
            <sorted>false</sorted>
            <value>
                <fullName>Mustang</fullName>
                <label>Mustang</label>
                <default>false</default>
            </value>
            <value>
                <fullName>Prius</fullName>
                <label>Prius</label>
                <default>false</default>
            </value>
        </valueSetDefinition>
        <valueSettings>
            <valueName>Mustang</valueName>
            <controllingFieldValue>Ford</controllingFieldValue>
        </valueSettings>
        <valueSettings>
            <valueName>Prius</valueName>
            <controllingFieldValue>Toyota</controllingFieldValue>
        </valueSettings>
    </valueSet>
</CustomField>
```

How to read it:

- `valueName` "defines the values in the custom dependent picklist"; `controllingFieldValue` is "a
  list of values in the controlling or parent picklist" (api_meta.txt:45871–45878). It repeats: one
  `<controllingFieldValue>` element per allowed controlling value, not a delimited string.
- When the controller is a checkbox the legal strings are exactly `checked` and `unchecked`
  (api_meta.txt:79250–79256, and the guide's worked sample at api_meta.txt:44758–44781).
- **The matrix is append-only over the API**: "You can add field dependency values via the Metadata
  API but not remove them" (api_meta.txt:45855–45860). A deploy that drops a `valueSettings` entry
  does not un-map it. Removal is a Setup action. Plan the matrix before the first deploy.
- A GVS-backed field cannot be the dependent side — see §6 of `references/gotchas.md`. The
  `controllingField` element lives on `ValueSet`, so a field whose `valueSet` is just a
  `valueSetName` has nowhere to put it.

---

## 7. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>*</members>
        <name>GlobalValueSet</name>
    </types>
    <types>
        <members>OpportunityStage</members>
        <members>CaseStatus</members>
        <members>LeadStatus</members>
        <members>Industry</members>
        <members>LeadSource</members>
        <name>StandardValueSet</name>
    </types>
    <types>
        <members>Renewal_Risk_Band__gvs-fr</members>
        <name>GlobalValueSetTranslation</name>
    </types>
    <types>
        <members>Opportunity.Renewal_Risk__c</members>
        <name>CustomField</name>
    </types>
    <version>62.0</version>
</Package>
```

- **`GlobalValueSet` takes the wildcard; `StandardValueSet` does not.** "This metadata type supports
  the wildcard character `*` (asterisk)" for `GlobalValueSet` (api_meta.txt:79424–79426); "This
  metadata type doesn't support the wildcard character `*` (asterisk)" for `StandardValueSet`
  (api_meta.txt:130826–130828). Every standard value set you want must be named. That is why a
  "retrieve everything" manifest quietly ships zero standard picklists.
- Names are case-sensitive (api_meta.txt:141686) and are *not* the field names:
  `Opportunity.StageName` → `OpportunityStage`, `Case.Status` → `CaseStatus`, `Lead.Status` →
  `LeadStatus`, `Account.Industry` → `Industry`, `Lead.LeadSource` → `LeadSource`
  (api_meta.txt:142674, 141982, 142581, 142509, 142575). The full mapping is Appendix C,
  api_meta.txt:141680 onward.
- **Some standard value sets cannot be deployed at all.** Appendix C footnotes: footnote 2 — "You
  can only update the label in this standard value set or picklist field. You can't insert or delete
  picklist values" (api_meta.txt:143150), which covers `ForecastingItemCategory` and
  `RoleInTerritory`; footnote 3 — "You can't read or update this standard value set or picklist
  field" (api_meta.txt:143152), which covers `IdeaCategory` and `QuestionOrigin`. Naming a
  footnote-3 set in a manifest is a retrieve that comes back empty.
- `CustomField` also has no wildcard, so name each picklist field.
- `GlobalValueSetTranslation` members are `SetName-lang` (api_meta.txt:79446–79447).

## 8. Retrieve and deploy

```bash
# Retrieve first. StandardValueSet has no wildcard, so name each one.
sf project retrieve start \
  --metadata "GlobalValueSet:Renewal_Risk_Band__gvs" \
  --metadata "StandardValueSet:OpportunityStage" \
  --metadata "StandardValueSet:CaseStatus" \
  --metadata "CustomField:Opportunity.Renewal_Risk__c" \
  --target-org my-sandbox

# Everything: the wildcard works for global value sets only.
sf project retrieve start --metadata "GlobalValueSet" --target-org my-sandbox

# Lint before deploying — omission deactivates, so a hand-edited file is the risk.
python3 scripts/check_picklist_and_value_sets.py \
  --manifest-dir force-app/main/default

# Validate against production without saving anything.
sf project deploy start \
  --source-dir force-app/main/default/globalValueSets \
  --source-dir force-app/main/default/standardValueSets \
  --source-dir force-app/main/default/objects/Opportunity/fields/Renewal_Risk__c.field-meta.xml \
  --dry-run \
  --target-org production

# Deploy once the dry run is clean.
sf project deploy start \
  --source-dir force-app/main/default/globalValueSets \
  --source-dir force-app/main/default/standardValueSets \
  --source-dir force-app/main/default/objects/Opportunity/fields/Renewal_Risk__c.field-meta.xml \
  --target-org production
```

The retrieve is not optional here, and not for the usual "know your baseline" reason. Deploying a
`GlobalValueSet` or `StandardValueSet` file that is missing values **deactivates those values**
(api_meta.txt:47482–47483). Retrieve, edit, deploy — never author one of these files from scratch
against an org that already has the set.

Flag spellings verified against `sf project retrieve start --help` and `sf project deploy start
--help` on `@salesforce/cli` 2.149.9 (2026-09-04). `--target-org` is required unless the
`target-org` config variable is set.

## 9. Verification

A deploy that succeeded is not a value list that is correct. Two checks.

**What the platform thinks the field is**, from anonymous Apex. `getPicklistValues()` "returns a
list of active `PicklistEntry` objects… Only active picklist values are returned"
(apexrefguide.txt:190850–190852) — so this is also how you confirm a deactivation landed: the value
should be *absent*, not present-and-inactive.

```apex
Schema.DescribeFieldResult f = Opportunity.Renewal_Risk__c.getDescribe();

System.debug('restricted: ' + f.isRestrictedPicklist());   // expect true for a GVS-backed field
System.debug('dependent:  ' + f.isDependentPicklist());
if (f.isDependentPicklist()) {
    System.debug('controller: ' + f.getController());
}

for (Schema.PicklistEntry e : f.getPicklistValues()) {
    // getValue() is the stored API value; getLabel() is what the user sees.
    System.debug(e.getValue() + ' | ' + e.getLabel() + ' | default=' + e.isDefaultValue());
}
```

`isRestrictedPicklist()` "returns true if the field is a restricted picklist"
(apexrefguide.txt:191375–191381); `isDependentPicklist()` and `getController()` are
apexrefguide.txt:191169–191175 and 190710–190715. `PicklistEntry` exposes `getLabel()`,
`getValue()`, `isActive()` and `isDefaultValue()` (apexrefguide.txt:193677–193686) — and
`isDefaultValue()` is documented as "only one item in a picklist can be designated as the default",
which is the assertion worth making before you trust §1's `default` flags.

**What the data actually holds** — run this before deactivating or replacing anything, because a
value with rows behind it is a migration, not an edit:

```sql
SELECT Renewal_Risk__c, COUNT(Id) recordCount
FROM Opportunity
GROUP BY Renewal_Risk__c
ORDER BY COUNT(Id) DESC
```

Rows whose `Renewal_Risk__c` does not appear in the Apex output above are values the picklist no
longer offers but the data still carries — expected for a deactivated value, a defect for anything
else. Chasing down the second kind is `admin/picklist-field-integrity-issues`.
