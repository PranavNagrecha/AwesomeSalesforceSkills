# Metadata Examples — Formula Fields

A formula field is a `CustomField` whose `<type>` is the **return type** (`Text`, `Number`,
`Currency`, `Percent`, `Checkbox`, `Date`, …) plus a `<formula>` element. There is no
`<type>Formula</type>` on a regular object — that value exists only on the deprecated
`ArticleType CustomField` type (Metadata API Developer Guide, *ArticleType CustomField* → `type`,
api_meta.txt:22161–22178). Choosing the return type is the first design decision because it is
also the deploy-time contract: the return type is what the `<type>` element says.

The two elements that make the field a formula (Metadata API Developer Guide, *CustomField* →
Fields, api_meta.txt:43422–43426):

| Element | Type | What the guide says |
|---|---|---|
| `formula` | string | "If specified, represents a formula on the field." |
| `formulaTreatBlanksAs` | `TreatBlanksAs` enum | "Indicates how to treat blanks in a formula. Valid values are: `BlankAsBlank` and `BlankAsZero`." |

## Where the file lives

| Form | Path | Root element |
|---|---|---|
| Metadata API (zip) | `objects/Account.object` — fields are `<fields>` entries inside `<CustomObject>` | `CustomObject` |
| DX source format | `objects/Account/fields/Health_Score__c.field-meta.xml` | `CustomField` |

The guide documents the embedded form: "Custom fields are user-defined fields and are part of the
custom object or standard object definition" (api_meta.txt:43248–43249), and its sample definition
shows `<fields>` inside `<CustomObject>` (api_meta.txt:43934–43946). `sf project retrieve` decomposes
each field into its own `.field-meta.xml` with `<CustomField>` as the root; the element names and
order are identical either way. The examples below use the DX form.

`fullName` is always object-qualified in `package.xml` — "`Account.MyAcctCustomField__c`"
(api_meta.txt:43226) — but inside a decomposed `.field-meta.xml` it is the bare field name, matching
the file name.

## Currency formula with `BlankAsZero`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Open_Pipeline_Net__c</fullName>
    <description>Amount minus Discount_Amount__c. Blanks count as zero so a missing discount does not blank the whole field. Owner: RevOps. Consumed by the Pipeline Health dashboard.</description>
    <formula>Amount - Discount_Amount__c</formula>
    <formulaTreatBlanksAs>BlankAsZero</formulaTreatBlanksAs>
    <inlineHelpText>Net pipeline value. A blank discount is treated as no discount.</inlineHelpText>
    <label>Open Pipeline Net</label>
    <precision>18</precision>
    <required>false</required>
    <scale>2</scale>
    <trackTrending>false</trackTrending>
    <type>Currency</type>
</CustomField>
```

How to read it:

- `formulaTreatBlanksAs` is the whole behaviour of this field. With `BlankAsZero`, a blank
  `Discount_Amount__c` evaluates as `0` and the result is `Amount`. With `BlankAsBlank` the
  arithmetic has a blank operand and the **field returns blank**, not `Amount`. Omit the element and
  you are deploying whichever default the platform applies rather than a decision you made — always
  write it explicitly on a `Number`, `Currency`, or `Percent` formula.
- `precision` is "the number of digits in a number" and `scale` is "the number of digits to the
  right of the decimal point" (api_meta.txt:43563–43565, 43610–43612). For a currency return type
  `scale` of `2` is the money shape; the pair must be present for numeric return types.
- `description` carries the business rule and the owner. Nothing else in the metadata records why
  the field exists, and a formula field has no code comments.

## Cross-object formula (Account lookup traversal from Contact)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Account_Owner_Name__c</fullName>
    <description>Display-only copy of the parent Account owner for list views and report grouping. One hop. Do not extend this chain; add an intermediate formula on Account instead.</description>
    <formula>IF(ISBLANK(Account.Owner.Id), &quot;No Account&quot;, Account.Owner.FirstName &amp; &quot; &quot; &amp; Account.Owner.LastName)</formula>
    <formulaTreatBlanksAs>BlankAsBlank</formulaTreatBlanksAs>
    <label>Account Owner Name</label>
    <required>false</required>
    <trackTrending>false</trackTrending>
    <type>Text</type>
    <unique>false</unique>
</CustomField>
```

How to read it:

- **XML escaping is not optional.** `&` becomes `&amp;` and `"` becomes `&quot;` inside a
  `<formula>` element. The guide's own samples do exactly this:
  `<formula>Name &amp; &quot;Updated&quot;</formula>` (api_meta.txt:140599) and
  `<errorConditionFormula>OR(Name = &apos;Milo&apos;,...)</errorConditionFormula>`
  (api_meta.txt:45439–45440). A `<` comparison must be written `&lt;` or the file is not
  well-formed XML and the deploy fails before any formula is compiled.
- `Account.Owner.Id` is two relationship hops from Contact. The skill's own ceiling —
  10 unique relationships per formula, ~800 compiled characters of overhead per hop — is in
  `references/llm-anti-patterns.md` (anti-pattern 3). Traversal is where compile size disappears.
- `Owner.Name` is one field; splitting it into `FirstName`/`LastName` is a deliberate choice here so
  the blank branch is explicit. Either works.
- `unique` and `externalId` are inert on a formula field: the guide restricts `externalId` to
  "AutoNumber, Email, Number, or Text" data types (api_meta.txt:43401–43404), and a calculated field
  is read-only in the API (Object Reference, *Calculated Field Type*, object_reference.txt:2207–2211),
  so nothing can ever be written into it to be unique.

## Checkbox formula

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Is_At_Risk__c</fullName>
    <description>TRUE when open cases exceed 5 or the account has been silent for 60+ days. Drives the At Risk list view filter. Blanks count as zero, so a never-touched account is not silently at risk.</description>
    <formula>Open_Cases__c &gt; 5 || (NOT(ISBLANK(Last_Activity_Date__c)) &amp;&amp; TODAY() - Last_Activity_Date__c &gt; 60)</formula>
    <formulaTreatBlanksAs>BlankAsZero</formulaTreatBlanksAs>
    <label>Is At Risk</label>
    <trackTrending>false</trackTrending>
    <type>Checkbox</type>
</CustomField>
```

How to read it:

- A checkbox formula carries no `defaultValue`. The guide defines that element as "If specified,
  represents the default value of the field" (api_meta.txt:43346); a calculated field is read-only
  and derives its value on every read (object_reference.txt:2207-2211), so there is no moment at
  which a default would be applied. Copying a regular checkbox's XML and adding `<formula>` leaves a
  `defaultValue` that means nothing.
- `>` is escaped as `&gt;` and `&&` as `&amp;&amp;`. `>` is legal bare XML character data, but
  escaping both comparison operators consistently is what keeps a formula readable in a diff.
- The `NOT(ISBLANK(...))` guard exists because `BlankAsZero` turns a blank **date** into a date
  arithmetic result, not into `false`. Blank handling is per data type, and the enum is a single
  org-wide switch for the whole formula, not a per-reference one.

## Text formula with `IMAGE()`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Health_Icon__c</fullName>
    <description>Decorative traffic light for the record page and list views. The business value lives in Is_At_Risk__c; this field is display only and must not be used in reports, exports, or integrations.</description>
    <formula>IF(Is_At_Risk__c, IMAGE(&quot;/img/samples/light_red.gif&quot;, &quot;At Risk&quot;), IMAGE(&quot;/img/samples/light_green.gif&quot;, &quot;Healthy&quot;))</formula>
    <formulaTreatBlanksAs>BlankAsBlank</formulaTreatBlanksAs>
    <inlineHelpText>Red when Is At Risk is true. Report on Is At Risk, not on this field.</inlineHelpText>
    <label>Health Icon</label>
    <required>false</required>
    <trackTrending>false</trackTrending>
    <type>Text</type>
    <unique>false</unique>
</CustomField>
```

How to read it:

- `IMAGE()` returns markup, so the return type is `Text`. The second argument is the alt text and is
  what a screen reader and a CSV export see.
- The formula references `Is_At_Risk__c`, itself a formula field. A formula referencing a formula is
  legal and is the standard way to stay under compile size (`references/llm-anti-patterns.md`,
  anti-pattern 2), but it also means deleting `Is_At_Risk__c` breaks this field — plan the delete
  order with `admin/analyze-field-impact` inputs, not by trial deploy.
- The platform's own HTML-generating formula functions are named together in the Metadata API — "flow formula functions that generate HTML, such as `BR()`, `IMAGE()`, and
  `HYPERLINK()`" (`FlowSettings.doesFormulaGenerateHtmlOutput`, api_meta.txt:116861–116863) — which
  is the same family of functions, evaluated by a different engine. Do not assume a formula-field
  `IMAGE()` and a Flow formula `IMAGE()` render identically; see `flow/flow-formula-and-expression-patterns`.

## package.xml

`CustomField` members are `Object.Field__c` and the type **does not accept the `*` wildcard**:
"This metadata type doesn't support the wildcard character `*` (asterisk) in the `package.xml`
manifest file" (api_meta.txt:43983–43984). Every formula field has to be listed by name.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Account.Health_Icon__c</members>
        <members>Account.Is_At_Risk__c</members>
        <members>Contact.Account_Owner_Name__c</members>
        <members>Opportunity.Open_Pipeline_Net__c</members>
        <name>CustomField</name>
    </types>
    <version>62.0</version>
</Package>
```

Deploy order inside this manifest matters: `Health_Icon__c` references `Is_At_Risk__c`, and every
formula references its source fields. Ship the referenced fields in the same deploy or earlier, never
later.

## Retrieve, check, deploy

```bash
# Pull the current definition before editing anything — the retrieved file is the
# authority on which optional elements this return type actually carries.
sf project retrieve start --metadata CustomField:Account.Health_Icon__c --target-org my-sandbox

# Or pull every field on one object.
sf project retrieve start --metadata CustomField:Account.* --target-org my-sandbox

# Static review of the edited files before you spend a deploy.
python3 skills/admin/formula-fields/scripts/check_formula_fields.py \
  --manifest-dir force-app/main/default/objects

# Validate-only first: formula compile errors surface here, not at retrieve time.
sf project deploy start --source-dir force-app/main/default/objects \
  --target-org my-sandbox --dry-run

sf project deploy start --source-dir force-app/main/default/objects --target-org my-sandbox
```

Retrieving a field also pulls its field-level security: "Retrieving a component of this metadata type
in a project makes the component appear in any `Profile` and `PermissionSet` components that are
retrieved in the same package" (api_meta.txt:43251–43252). A formula field retrieved next to profiles
therefore turns into a profile diff as well as a field diff.

## Verify after deploy

Calculated fields are filterable in SOQL — "You can filter on these fields in SOQL, but you don't
replicate these fields" (object_reference.txt:2208–2209) — so a query is a real post-deploy check,
not just a read:

```sql
SELECT Id, Name, Is_At_Risk__c, Health_Icon__c FROM Account WHERE Is_At_Risk__c = true LIMIT 5
SELECT Id, Amount, Discount_Amount__c, Open_Pipeline_Net__c
FROM Opportunity WHERE Discount_Amount__c = null LIMIT 5
```

The second query is the `BlankAsZero` proof: pick records where the referenced field is genuinely
null and confirm the formula returned `Amount` rather than blank. A formula that compiles is not a
formula that is correct, and the blank rows are the ones that expose the difference.

Setup check for the same thing: **Setup → Object Manager → Opportunity → Fields & Relationships →
Open Pipeline Net**. The detail page shows the stored `Blank Field Handling` choice, which is the
Setup rendering of `formulaTreatBlanksAs`.
