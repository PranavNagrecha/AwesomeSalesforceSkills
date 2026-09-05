# Metadata Examples — Multi-Language and Translation

Deployable XML for the four metadata types that carry Salesforce UI
translations, plus the one settings file that turns the Translation Workbench
on. Shapes are taken from the Metadata API Developer Guide's own sample
definitions and field tables and extended to a realistic German (`de`) rollout
on Account.

The `CustomLabels` master file itself belongs to `admin/custom-label-management`.
This page shows only the `<customLabels>` *translation* entries that live in a
`<locale>.translation` file, because that file also carries every other
org-level translation and you deploy it as one unit.

---

## Where the files live

| Metadata type | MDAPI file name (grounded) | Folder | Source of the naming rule |
|---|---|---|---|
| `LanguageSettings` | `Language.settings` | `settings/` | `api_meta.txt:120903` |
| `Translations` | `<localeCode>.translation` — e.g. `de.translation` | `translations/` | `api_meta.txt:135574-135575` |
| `Translations` (packaged) | `<pkgNamespace>__<localeCode>.translation` — e.g. `Acme__de.translation` | `translations/` | `api_meta.txt:135576-135577` |
| `CustomObjectTranslation` | `<Object>-<lang>.objectTranslation` — e.g. `Account-de.objectTranslation`, `myCustomObject__c-de.objectTranslation` | `objectTranslations/` | `api_meta.txt:45899-45908`, sample at `api_meta.txt:46345-46347` |
| `CustomObjectTranslation` (packaged) | `<Object>-<pkgNamespace>__c-<lang>.objectTranslation` — e.g. `myCustomObject-Acme__c-de.objectTranslation` | `objectTranslations/` | `api_meta.txt:45903-45907` |
| `GlobalValueSetTranslation` | `<ValueSetName>-<lang>.globalValueSetTranslation` | `globalValueSetTranslations/` | `api_meta.txt:79446-79448` |
| `StandardValueSetTranslation` | `<ValueSetName>-<lang>.standardValueSetTranslation` | `standardValueSetTranslations/` | `api_meta.txt:130842-130844` |

The `fullName` of a `CustomObjectTranslation` is `customObjectName-lang` — the
file name without the suffix (`api_meta.txt:45925-45929`). The `fullName` of a
`Translations` component is just the language code, "for example, `de` for
German" (`api_meta.txt:135633-135634`).

UNVERIFIED (2026-09-05): the Metadata API Developer Guide documents only the
MDAPI file names above. The `-meta.xml` suffix and the
`force-app/main/default/` layout are the Salesforce DX source-format
convention, and the corpus used for this revision (Metadata API, Object
Reference, Apex, REST, Bulk, Data Loader, LDV guides) says nothing about how
`sf project retrieve` decomposes `objectTranslations/` on disk — in
particular whether each field's translation is split into its own file.
Run `sf project retrieve start --metadata CustomObjectTranslation:Account-de`
once and record what your own tree looks like. Every path below is written in
the DX form because that is what agents edit; the *names* are grounded, the
suffixes are convention.

---

## 1. `settings/Language.settings-meta.xml` — turn the Workbench on

Nothing below deploys usefully until this file says `true`. Shape and field
values from the guide's own `LanguageSettings` sample
(`api_meta.txt:120974-120986`) and field table (`api_meta.txt:120911-120971`).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LanguageSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableTranslationWorkbench>true</enableTranslationWorkbench>
    <enableEndUserLanguages>true</enableEndUserLanguages>
    <enablePlatformLanguages>false</enablePlatformLanguages>
    <enableDataTranslation>false</enableDataTranslation>
    <useLanguageFallback>true</useLanguageFallback>
    <enableICULocaleDateFormat>true</enableICULocaleDateFormat>
    <enableCanadaIcuFormat>true</enableCanadaIcuFormat>
    <enableLocalNamesForStdObjects>false</enableLocalNamesForStdObjects>
</LanguageSettings>
```

### How to read it

- **`enableTranslationWorkbench` defaults to `false`** (`api_meta.txt:120965-120967`).
  A fresh org has no Workbench, so a `.translation` file deployed into it has
  nothing to attach to.
- **`enablePlatformLanguages` is not independent.** The guide states: "Setting
  this field to `true` also sets `enableEndUserLanguages` `true`"
  (`api_meta.txt:120961-120964`). You cannot have platform-only languages
  without end-user languages, so the decision is one decision, not two.
- **`useLanguageFallback` defaults to `true`** and "indicates whether
  translation follows the language fallback rule (`true`) or returns the
  primary label (`false`)" (`api_meta.txt:120968-120971`). This is the switch
  that makes an untranslated string render as the source-language value rather
  than blank — leave it on unless you have a reason, and know that leaving it
  on is why missing translations are invisible in testing.
- **`enableDataTranslation` is a different feature from everything else on this
  page.** It governs translating *record data*, not labels — the
  `Product2DataTranslation`, `ProductCategoryDataTranslation`,
  `ServiceResourceDataTranslation` and `ServiceTerritoryDataTranslation`
  objects, each of which requires "Translation Workbench and data translation
  must be enabled in your org" (`object_reference.txt:227889`,
  `object_reference.txt:228633`, `object_reference.txt:259996`,
  `object_reference.txt:260827`). Translating a picklist label does nothing for
  a product name stored in a record.
- **`enableLocaleInsensitiveFiltering`** (omitted above, default `false`)
  "indicates whether users can filter query results, regardless of the locale
  or language associated with the user" (`api_meta.txt:120952-120956`). It
  changes filtering behaviour org-wide; set it deliberately or not at all.

Settings are deployed by the `Settings` type with the member name `Language`
(`api_meta.txt:120988-120997`), not by a type called `LanguageSettings`.

---

## 2. `translations/de.translation-meta.xml` — everything that is not object-scoped

`Translations` is the org-level bucket: custom labels, apps, tabs, report
types, flows, global quick actions, home-page web links, s-controls and In-App
Guidance prompts. Its own sample is two entries long
(`api_meta.txt:136653-136664`); this is that shape with more of the documented
children (`api_meta.txt:135605-135666`).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Translations xmlns="http://soap.sforce.com/2006/04/metadata">
    <customApplications>
        <label>Angebot-Manager</label>
        <name>Quote_Manager</name>
    </customApplications>
    <customLabels>
        <label>Angebot speichern</label>
        <name>Quote_Save_Button</name>
    </customLabels>
    <customLabels>
        <label>{0} muss groesser als null sein.</label>
        <name>Error_Amount_Must_Be_Positive</name>
    </customLabels>
    <customTabs>
        <label>Angebote</label>
        <name>Quote__c</name>
    </customTabs>
    <reportTypes>
        <description>Angebote mit zugehoerigen Positionen</description>
        <label>Angebote und Positionen</label>
        <name>Quotes_with_Line_Items</name>
    </reportTypes>
    <flowDefinitions>
        <fullName>Submit_Quote_For_Approval</fullName>
        <label>Angebot zur Genehmigung senden</label>
    </flowDefinitions>
    <quickActions>
        <label>Neues Angebot</label>
        <name>New_Quote</name>
    </quickActions>
</Translations>
```

### How to read it

- **`<name>` on every child is the API name of the thing being translated, and
  it is Required** — `CustomLabelTranslation.name`
  (`api_meta.txt:135937`), `CustomTabTranslation.name`
  (`api_meta.txt:135966`), `CustomApplicationTranslation.name`
  (`api_meta.txt:135926`), `ReportTypeTranslation.name`
  (`api_meta.txt:136448`). A typo here does not fail loudly; it produces
  a translation that matches nothing.
- **`flowDefinitions` uses `fullName`, not `name`.**
  `FlowDefinitionTranslation.fullName` is "Required. The API name for the flow
  definition" (`api_meta.txt:136015`). Copying the `<name>` shape from a
  sibling element here is the single most common hand-edit error in this file.
- **`flowDefinitions` is version-scoped in a way the other children are not.**
  "By default, flow definitions inherit the label of the active flow version.
  If you provide a label here, the definition label no longer inherits changes
  to the active version label" (`api_meta.txt:136017-136020`). Translating a
  flow definition label freezes it against future version renames. Only `Flow`
  and `AutolaunchedFlow` types are supported (`api_meta.txt:135625-135627`).
- **Label maximums vary by child.** `CustomLabelTranslation.label` and
  `CustomApplicationTranslation.label` are "Maximum of 765 characters"
  (`api_meta.txt:135934-135935`, `api_meta.txt:135923-135924`);
  `CustomTabTranslation.label` carries no stated maximum
  (`api_meta.txt:135964`). 765 is *lower* than the 1000-character
  maximum on the source `CustomLabel.value` — a source label near its ceiling
  cannot be fully translated.
- **`quickActions` here means *global* quick actions.** The guide is explicit:
  "A list of global rather than object-specific quick actions"
  (`api_meta.txt:135656`). Object-scoped actions go in that object's
  `objectTranslation` file instead (`api_meta.txt:45958`).

---

## 3. `objectTranslations/Account-de.objectTranslation-meta.xml`

This is the file that does the visible work: object name, field labels, field
help text, picklist values, layout section names, record type names,
validation-rule error messages. Shape from the guide's own Account sample
(`api_meta.txt:46345-46420`), extended with the child types the sample omits.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObjectTranslation xmlns="http://soap.sforce.com/2006/04/metadata">
    <caseValues>
        <caseType>Nominative</caseType>
        <plural>false</plural>
        <value>Kunde</value>
    </caseValues>
    <caseValues>
        <caseType>Nominative</caseType>
        <plural>true</plural>
        <value>Kunden</value>
    </caseValues>
    <caseValues>
        <caseType>Genitive</caseType>
        <plural>false</plural>
        <value>Kunden</value>
    </caseValues>
    <gender>Masculine</gender>
    <startsWith>Consonant</startsWith>
    <nameFieldLabel>Kundenname</nameFieldLabel>

    <fields>
        <label>Kunden-Code</label>
        <help>Der interne Code, den die Finanzabteilung diesem Kunden zuweist.</help>
        <name>Account_Code__c</name>
    </fields>
    <fields>
        <label>Kundenstufe</label>
        <help>Bestimmt die Service-Level-Vereinbarung.</help>
        <name>Account_Tier__c</name>
        <picklistValues>
            <masterLabel>Platinum</masterLabel>
            <translation>Platin</translation>
        </picklistValues>
        <picklistValues>
            <masterLabel>Gold</masterLabel>
            <translation>Gold</translation>
        </picklistValues>
        <picklistValues>
            <masterLabel>Silver</masterLabel>
            <translation>Silber</translation>
        </picklistValues>
    </fields>
    <fields>
        <label>Uebergeordneter Kunde</label>
        <relationshipLabel>Untergeordnete Kunden</relationshipLabel>
        <name>Parent_Account__c</name>
        <lookupFilter>
            <errorMessage>Der uebergeordnete Kunde muss aktiv sein.</errorMessage>
            <informationalMessage>Es werden nur aktive Kunden angezeigt.</informationalMessage>
        </lookupFilter>
    </fields>

    <recordTypes>
        <label>Firmenkunde</label>
        <description>Kunden mit einem Rahmenvertrag.</description>
        <name>Enterprise_Account</name>
    </recordTypes>

    <validationRules>
        <errorMessage>Die Kundenstufe ist fuer aktive Kunden erforderlich.</errorMessage>
        <name>Tier_Required_When_Active</name>
    </validationRules>

    <layouts>
        <layout>Account Layout</layout>
        <sections>
            <label>Kundeninformationen</label>
            <section>Account Information</section>
        </sections>
        <sections>
            <label>Adressinformationen</label>
            <section>Address Information</section>
        </sections>
    </layouts>

    <webLinks>
        <label>Kundenportal oeffnen</label>
        <name>Open_Customer_Portal</name>
    </webLinks>

    <sharingReasons>
        <label>Regionaler Zugriff</label>
        <name>Regional_Access__c</name>
    </sharingReasons>

    <workflowTasks>
        <subject>Kundenstufe pruefen</subject>
        <description>Pruefen Sie die Kundenstufe vor der Vertragsverlaengerung.</description>
        <name>Review_Account_Tier</name>
    </workflowTasks>
</CustomObjectTranslation>
```

### How to read it

- **`<name>` inside `<fields>` is "the name of the field relative to the custom
  object; for example, `MyField__c`"** (`api_meta.txt:46016-46017`) — Required.
  Standard fields use their API name (`account_number` in the guide's own
  sample, `api_meta.txt:46410`), not their label.
- **`<label>` on a field caps at 40 characters** — "Translation for the label.
  Maximum of 40 characters" (`api_meta.txt:46000`). That is the tightest
  ceiling on this page, and German and Finnish compounds hit it. Contrast it
  with `LayoutSectionTranslation.label`, `RecordTypeTranslation.label`,
  `QuickActionTranslation.label` and `WebLinkTranslation.label`, all "Maximum
  of 765 characters" (`api_meta.txt:46069`, `api_meta.txt:46213`,
  `api_meta.txt:46203`, `api_meta.txt:46256-46257`), and `nameFieldLabel` and
  `relationshipLabel`, both "Maximum of 80 characters"
  (`api_meta.txt:45941`, `api_meta.txt:46024-46027`).
- **`<picklistValues>` takes `masterLabel` + `translation`, and both are
  Required** (`api_meta.txt:46186-46189`). `masterLabel` is "the picklist value
  defined on the setup page in the application. Displayed wherever a translated
  label isn't available" — i.e. the master *label*, which is what the setup
  page shows, and which for most fields equals the API value but does not have
  to. If a value's label and API name have drifted, match `masterLabel` to the
  label.
- **Only *local, custom* picklists belong here.** `PicklistValueTranslation`
  "contains details for translation of a picklist value from a local, custom
  picklist field" (`api_meta.txt:46182-46183`). A field that inherits a global
  value set is translated once in `GlobalValueSetTranslation` (§4); a standard
  picklist is translated in `StandardValueSetTranslation` — "In API versions
  37.0 and earlier standard picklist values could be translated with
  CustomFieldTranslation. In API version 38.0, use StandardValueSetTranslation
  instead" (`api_meta.txt:45982-45983`).
- **`<help>` translates field-level help hover text**
  (`api_meta.txt:45997-45998`) and `<description>` translates the field
  description (`api_meta.txt:45993`). Both are optional and both are routinely
  forgotten, which is how a fully "translated" org still shows English tooltips.
- **`<validationRules><errorMessage>` is Required when the element is present**
  (`api_meta.txt:46245-46246`). This is the *other* way to translate a
  validation message — the alternative to a `$Label` merge field. Pick one per
  org: a rule whose `errorMessage` is a literal string is translated here; a
  rule whose `errorMessage` is `$Label.X` is translated in the label's
  `Translations` file and must **not** also appear here.
- **`<gender>` and `<startsWith>` are grammar, not decoration.** `gender`
  "indicates the gender of the noun that represents the object"
  (`api_meta.txt:45935-45937`); `startsWith` "indicates whether the noun starts
  with a vowel, consonant, or is a special character" — `Consonant`, `Vowel`,
  or `Special` "(for nouns starting with z, or s plus consonants)"
  (`api_meta.txt:45815-45822`, `api_meta.txt:45964-45966`). Get them wrong and
  merge-field sentences in that language read wrong even though every label is
  correct. Swedish *Euter* and Dutch *Common* appear in the Setup UI but "are
  stored internally as 'Feminine'. When setting them through the Metadata API,
  use 'Feminine'" (`api_meta.txt:45790-45794`).
- **`<caseValues>` exists because some languages decline nouns.**
  `ObjectNameCaseValue` supports 25 `caseType` values plus `article`,
  `plural` and `possessive` (`api_meta.txt:46122-46177`), and `value` is
  Required. English needs Nominative singular and plural and nothing else;
  German needs Nominative, Accusative, Genitive and Dative; the guide warns
  "Not every language supports all the possible values"
  (`api_meta.txt:46111-46112`).
- **`lookupFilter` replaced `namedFilters`.** `namedFilters` "has been removed
  as of API version 30.0"; the lookup-filter error message now lives in
  `CustomFieldTranslation.lookupFilter` (`api_meta.txt:45951-45956`,
  `api_meta.txt:46011-46014`).

UNVERIFIED (2026-09-05): the exact form of `<layouts><layout>` — whether the
layout is named `Account Layout` or `Account-Account Layout` — is not stated in
the `LayoutTranslation` field table (`api_meta.txt:46051-46055`), which says
only "Required. The layout name". Retrieve one `objectTranslation` from your
own org before hand-writing layout sections; the rest of this file's shapes are
grounded.

---

## 4. `globalValueSetTranslations/Account_Tier__gvs-de.globalValueSetTranslation-meta.xml`

Values shared across objects are translated once, here — not per field.
Shape from the guide's own sample (`api_meta.txt:79477-79500`).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<GlobalValueSetTranslation xmlns="http://soap.sforce.com/2006/04/metadata">
    <valueTranslation>
        <masterLabel>Platinum</masterLabel>
        <translation>Platin</translation>
    </valueTranslation>
    <valueTranslation>
        <masterLabel>Gold</masterLabel>
        <translation>Gold</translation>
    </valueTranslation>
    <valueTranslation>
        <masterLabel>Silver</masterLabel>
        <translation><!-- Silver --></translation>
    </valueTranslation>
</GlobalValueSetTranslation>
```

### How to read it

- **The `__gvs` suffix in the file name is not a typo.** "Any global value set
  created in API version 57.0 or later automatically has the `__gvs` suffix
  appended to the developer name. When you make any CRUD-based call with the
  GlobalValueSet type, you must append the suffix to the `fullName` field"
  (`api_meta.txt:79419-79421`). The translation file is named
  `ValueSetName-lang.globalValueSetTranslation` (`api_meta.txt:79446-79448`),
  so a value set created after v57 needs `Account_Tier__gvs-de`, and one
  created before it needs `Account_Tier-de`. Both spellings exist in real orgs.
- **`masterLabel` is Required; `translation` is not**
  (`api_meta.txt:79466-79470`). That asymmetry is deliberate: "When a value
  isn't translated, its translation becomes a comment that's paired with its
  masterLabel" (`api_meta.txt:79475-79476`). `<translation><!-- Silver --></translation>`
  in a retrieved file means **untranslated**, not "translated to Silver". It is
  valid XML and it deploys without complaint.
- **This differs from `PicklistValueTranslation`**, where both `masterLabel`
  and `translation` are Required (`api_meta.txt:46186-46189`). Same-looking
  elements, different contracts.

`StandardValueSetTranslation` has the identical `valueTranslation` shape and
the same comment convention (`api_meta.txt:130863-130879`); its file is
`standardValueSetTranslations/LeadSource-de.standardValueSetTranslation`
(`api_meta.txt:130842-130844`), and the guide's own package.xml member for it
is `AccountRating-fr` (`api_meta.txt:130882-130889`).

---

## `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Language</members>
        <name>Settings</name>
    </types>
    <types>
        <members>Account_Tier__c</members>
        <members>Account_Code__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Account</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Account_Tier__gvs</members>
        <name>GlobalValueSet</name>
    </types>
    <types>
        <members>*</members>
        <name>CustomLabels</name>
    </types>
    <types>
        <members>Account-de</members>
        <name>CustomObjectTranslation</name>
    </types>
    <types>
        <members>Account_Tier__gvs-de</members>
        <name>GlobalValueSetTranslation</name>
    </types>
    <types>
        <members>LeadSource-de</members>
        <name>StandardValueSetTranslation</name>
    </types>
    <types>
        <members>de</members>
        <name>Translations</name>
    </types>
    <version>62.0</version>
</Package>
```

### Manifest rules that bite

- **Every translation type's member is `<name>-<lang>`, not `<name>`.**
  `CustomObjectTranslation` takes `Account-de`;
  `GlobalValueSetTranslation` takes `Numbers-fr` in the guide's own example
  (`api_meta.txt:79503-79510`); `StandardValueSetTranslation` takes
  `AccountRating-fr` (`api_meta.txt:130882-130889`). `Translations` is the
  exception — its member is the bare locale code, `de`
  (`api_meta.txt:135633-135634`).
- **`Settings` is the type name; `Language` is the member.** There is no
  `LanguageSettings` type in a manifest (`api_meta.txt:120988-120997`), and
  the wildcard "applies only when retrieving all settings, not for an
  individual setting" (`api_meta.txt:121006-121008`).
- **Retrieving `Translations` alone returns almost nothing.** "When you use the
  `retrieve()` call to get translations, the files returned in the
  `.translations` folder only include translations for the other metadata types
  referenced in package.xml" (`api_meta.txt:136670-136673`). That is why
  `CustomLabels` is listed above with a wildcard: drop it and the
  `<customLabels>` entries vanish from the retrieved `de.translation`. The
  guide's own worked example lists six types alongside `Translations`
  (`api_meta.txt:136674-136712`).
- **All four translation types support the wildcard** —
  `CustomObjectTranslation` (`api_meta.txt:46421-46422`), `Translations`
  (`api_meta.txt:136717-136718`), `GlobalValueSetTranslation`
  (`api_meta.txt:79514-79515`), `StandardValueSetTranslation`
  (`api_meta.txt:130893-130894`) — but a wildcard on `CustomObjectTranslation`
  pulls every object × every enabled language, which is how a "just grab the
  translations" retrieve turns into a thousand-file diff.

---

## Deploy order

Translation metadata is a set of pointers by name. Deploy it before the thing
it names exists and the deploy fails on the missing reference; deploy it after
and the pointer resolves. So the order is not a preference:

```bash
# 0. ALWAYS retrieve first — you are editing org-wide files.
sf project retrieve start \
  --metadata Settings:Language \
  --metadata CustomObjectTranslation:Account-de \
  --metadata Translations:de \
  --target-org my-sandbox

# 1. The Workbench and the languages. Nothing else lands until this is true.
sf project deploy start \
  --metadata Settings:Language \
  --target-org my-sandbox

# 2. The metadata being translated — objects, fields, value sets, labels,
#    record types, validation rules, layouts. Translation files name these.
sf project deploy start \
  --source-dir force-app/main/default/objects \
  --source-dir force-app/main/default/globalValueSets \
  --source-dir force-app/main/default/labels \
  --target-org my-sandbox

# 3. Only now, the translations.
python3 skills/admin/multi-language-and-translation/scripts/check_multi_language_and_translation.py \
  --manifest-dir force-app/main/default

sf project deploy start \
  --source-dir force-app/main/default/objectTranslations \
  --source-dir force-app/main/default/globalValueSetTranslations \
  --source-dir force-app/main/default/standardValueSetTranslations \
  --source-dir force-app/main/default/translations \
  --dry-run \
  --target-org my-sandbox

sf project deploy start \
  --source-dir force-app/main/default/objectTranslations \
  --source-dir force-app/main/default/globalValueSetTranslations \
  --source-dir force-app/main/default/standardValueSetTranslations \
  --source-dir force-app/main/default/translations \
  --target-org my-sandbox
```

Two order hazards that are not about steps 1–3:

- **A picklist value omitted from a `CustomObject`/`GlobalValueSet` payload is
  deactivated, not left alone.** "If picklist values are missing from a
  component definition, they get deactivated when deployed. Deactivation occurs
  for picklist values of both standard and custom fields"
  (`api_meta.txt:47482-47483`, `api_meta.txt:79237-79238`). A step-2 deploy
  built from a stale retrieve silently deactivates values whose translations
  you are about to deploy in step 3.
- **Package translations can overwrite org translations.** "When you retrieve
  or deploy translations from a package, the translations from the package
  might override existing translations. The overridden translations appear in
  the Rename Tabs and Labels UI until you click Reset to restore the
  translations installed by the latest package" (`api_meta.txt:45976-45979`).
  Sequence a package install before, never after, a translation deploy.

---

## Verification

**1. Confirm the language is actually enabled and active.** The `Translation`
object "represents the languages enabled for translation in your Salesforce
org" (`object_reference.txt:290167-290168`):

```sql
SELECT Id, Language, IsActive, CanManage
FROM Translation
ORDER BY Language
```

`IsActive` "indicates whether the translated values for this language display
to users" and `CanManage` "indicates whether the language is available for
translation" (`object_reference.txt:290197,290205-290206`). A language that is present
but `IsActive = false` accepts deployed translations and shows none of them.
Reading this object needs the "View Setup and Configuration" permission, and
the org must be Enterprise, Performance, Unlimited or Developer edition
(`object_reference.txt:290176-290185`).

**2. Confirm the translation reached the running user.** `toLabel()` returns
the running user's translation, so run it as the target-language user rather
than as yourself:

```sql
SELECT Id, Name, Account_Tier__c, toLabel(Account_Tier__c) tierLabel
FROM Account
WHERE Account_Tier__c != null
LIMIT 5
```

`Account_Tier__c` returns the API value (unchanged by translation);
`tierLabel` returns `Platin` for a German user and `Platinum` for an English
one. If both columns come back identical for the German user, the translation
did not land — check `Translation.IsActive` first, then the `masterLabel`
spelling in the `objectTranslation` file.

**3. Confirm the test user is genuinely in the target language.**
`User.LanguageLocaleKey` is "Required. The user's language, such as French or
Chinese (Traditional). Label is Language" and is a restricted picklist
(`object_reference.txt:295460-295465`):

```sql
SELECT Id, Username, LanguageLocaleKey, LocaleSidKey
FROM User
WHERE LanguageLocaleKey = 'de'
AND IsActive = true
```

```apex
// Create the test user in a scratch org, then Login As.
User de = new User(
    Alias        = 'detest',
    Email        = 'de.tester@example.invalid',
    LastName     = 'Tester',
    Username     = 'de.tester@example.invalid.' + System.now().getTime(),
    ProfileId    = [SELECT Id FROM Profile WHERE Name = 'Standard User' LIMIT 1].Id,
    LanguageLocaleKey = 'de',   // what labels render in
    LocaleSidKey      = 'de_DE', // what dates and numbers render in
    EmailEncodingKey  = 'UTF-8',
    TimeZoneSidKey    = 'Europe/Berlin'
);
insert de;
```

`LanguageLocaleKey` and `LocaleSidKey` are different settings and the guide
says so: "Setting a default language is different from setting a default
locale" (`api_meta.txt:135354-135355`). A user with `LanguageLocaleKey = 'de'`
and `LocaleSidKey = 'en_US'` sees German labels over American date formats,
which reads as a broken translation to the tester and is in fact a correct
one.

One more describe-level check worth knowing: from API version 47.0, the
`PicklistEntry` `active` flag on `User.LanguageLocaleKey` "indicates whether
the language is in the user's Displayed Languages (`true`) or the user's
Available Languages (`false`)" (`object_reference.txt:295467-295471`). So a
language can be selectable in the API and still not offered in the user's own
language picker.
