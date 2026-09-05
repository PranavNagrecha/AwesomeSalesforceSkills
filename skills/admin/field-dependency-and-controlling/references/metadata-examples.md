# Metadata Examples — Field Dependency and Controlling

Deployable XML for a dependency matrix. Element names, types and the checkbox value literals come from the
Metadata API Developer Guide (Summer '26 / v62 PDF): `ValueSet` and `ValueSettings`
(api_meta.txt:45838–45877), the `Picklist (Including Dependent Picklist)` sample definition
(api_meta.txt:44745–44852), `PicklistValue.controllingFieldValues` (api_meta.txt:79250–79258),
`RecordType` / `RecordTypePicklistValue` (api_meta.txt:45041–45053) and `GlobalValueSet`
(api_meta.txt:79344–79370). The worked example below extends the guide's two-field car sample to a
realistic three-field chain plus a checkbox controller.

Validate before deploying:

```bash
python3 skills/admin/field-dependency-and-controlling/scripts/check_field_dependency_and_controlling.py \
    --manifest-dir force-app/main/default
```

---

## 1. Where the matrix lives

| Thing | Metadata type | Element | Guide |
|---|---|---|---|
| "This field is dependent, and on what" | `CustomField` → `ValueSet` | `<controllingField>` | api_meta.txt:45843–45845 |
| The enabled (controlling value, dependent value) pairs | `CustomField` → `ValueSet` | `<valueSettings>` | api_meta.txt:45855–45858 |
| One controlling value in a pair | `ValueSettings` | `<controllingFieldValue>` (string array — repeat the element) | api_meta.txt:45873–45875 |
| The dependent value in a pair | `ValueSettings` | `<valueName>` | api_meta.txt:45877 |
| Which values a record type may use at all | `RecordType` | `<picklistValues><picklist>` + `<values><fullName>` | api_meta.txt:45041–45053 |

The dependency is **not** a separate metadata type. There is no `FieldDependency` component — the matrix is
part of the *dependent* field's own file, and the controlling field's file knows nothing about it. That
asymmetry drives the deploy order in §6.

`<controllingField>` accepts a picklist **or** a checkbox: "A controlling field can be a checkbox or picklist
field, but in this case it's a picklist" (api_meta.txt:45843–45845).

> The `<picklist>` element with `<picklistValues><controllingFieldValues>` that you will find in older
> examples is the **deprecated** shape: "Use this type in API version 37.0 and earlier only… In API version
> 38.0 and later, `Picklist` is replaced by `ValueSet` on the `CustomField` type" (api_meta.txt:44676–44679).
> Write `<valueSet>`. Retrieve at v38.0+ and you will get `<valueSet>` back regardless.

---

## 2. Picklist-controlled dependent picklist (the base case)

Two fields on `Warranty_Claim__c`. `Product_Family__c` (controlling, three values) filters
`Product_Line__c` (dependent, five values). `Accessories` is legal under two families, so it carries two
`<controllingFieldValue>` elements in a single `<valueSettings>` block.

`force-app/main/default/objects/Warranty_Claim__c/fields/Product_Family__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Product_Family__c</fullName>
    <label>Product Family</label>
    <type>Picklist</type>
    <required>false</required>
    <trackTrending>false</trackTrending>
    <valueSet>
        <restricted>true</restricted>
        <valueSetDefinition>
            <sorted>false</sorted>
            <value>
                <fullName>Computers</fullName>
                <label>Computers</label>
                <default>false</default>
            </value>
            <value>
                <fullName>Mobile</fullName>
                <label>Mobile</label>
                <default>false</default>
            </value>
            <value>
                <fullName>Peripherals</fullName>
                <label>Peripherals</label>
                <default>false</default>
            </value>
        </valueSetDefinition>
    </valueSet>
</CustomField>
```

`force-app/main/default/objects/Warranty_Claim__c/fields/Product_Line__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Product_Line__c</fullName>
    <label>Product Line</label>
    <type>Picklist</type>
    <required>false</required>
    <trackTrending>false</trackTrending>
    <valueSet>
        <controllingField>Product_Family__c</controllingField>
        <restricted>true</restricted>
        <valueSetDefinition>
            <sorted>false</sorted>
            <value>
                <fullName>Laptops</fullName>
                <label>Laptops</label>
                <default>false</default>
            </value>
            <value>
                <fullName>Desktops</fullName>
                <label>Desktops</label>
                <default>false</default>
            </value>
            <value>
                <fullName>Handsets</fullName>
                <label>Handsets</label>
                <default>false</default>
            </value>
            <value>
                <fullName>Tablets</fullName>
                <label>Tablets</label>
                <default>false</default>
            </value>
            <value>
                <fullName>Accessories</fullName>
                <label>Accessories</label>
                <default>false</default>
            </value>
        </valueSetDefinition>
        <valueSettings>
            <controllingFieldValue>Computers</controllingFieldValue>
            <valueName>Laptops</valueName>
        </valueSettings>
        <valueSettings>
            <controllingFieldValue>Computers</controllingFieldValue>
            <valueName>Desktops</valueName>
        </valueSettings>
        <valueSettings>
            <controllingFieldValue>Mobile</controllingFieldValue>
            <valueName>Handsets</valueName>
        </valueSettings>
        <valueSettings>
            <controllingFieldValue>Mobile</controllingFieldValue>
            <valueName>Tablets</valueName>
        </valueSettings>
        <valueSettings>
            <controllingFieldValue>Computers</controllingFieldValue>
            <controllingFieldValue>Mobile</controllingFieldValue>
            <controllingFieldValue>Peripherals</controllingFieldValue>
            <valueName>Accessories</valueName>
        </valueSettings>
    </valueSet>
</CustomField>
```

**How to read it**

- `<controllingField>` names the controlling field by API name **relative to the object** — no
  `Warranty_Claim__c.` prefix. `fullName` is the qualified one (api_meta.txt:43219–43224); `controllingField`
  is not.
- One `<valueSettings>` block per **dependent** value, not per pair. Because `controllingFieldValue` is a
  string array (api_meta.txt:45873), `Accessories` lists three of them inside one block. Five dependent
  values means at most five blocks, no matter how large the matrix.
- `Peripherals` enables only `Accessories`. A controlling value that enables nothing is legal and renders an
  empty dependent picklist — check it is deliberate, not an omission.
- `restricted` on either field is a **membership** control, not a pairing control
  (api_meta.txt:45847–45848). It does not make the matrix enforceable on API writes. See §7.
- `<valueSetDefinition>` and `<valueSetName>` are mutually exclusive on one `ValueSet`. A field that
  inherits from a global value set uses `valueSetName`; this one owns its values.

---

## 3. Checkbox-controlled dependent picklist

A checkbox controlling field has exactly two values, and they are **not** `true`/`false`. The guide is
explicit: `controllingFieldValues` "values in the list depend on the field type: • **Checkbox: `checked` or
`unchecked`.** • Picklist: the fullname of the picklist value in the controlling field"
(api_meta.txt:79250–79258). The guide's own dependent-picklist sample writes
`<controllingFieldValues>checked</controllingFieldValues>` against an `isAmerican__c` checkbox
(api_meta.txt:44762–44790).

`force-app/main/default/objects/Warranty_Claim__c/fields/Expedite_Reason__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Expedite_Reason__c</fullName>
    <label>Expedite Reason</label>
    <type>Picklist</type>
    <required>false</required>
    <trackTrending>false</trackTrending>
    <valueSet>
        <!-- Expedited__c is <type>Checkbox</type> with <defaultValue>false</defaultValue> -->
        <controllingField>Expedited__c</controllingField>
        <restricted>true</restricted>
        <valueSetDefinition>
            <sorted>false</sorted>
            <value>
                <fullName>Safety_Recall</fullName>
                <label>Safety Recall</label>
                <default>false</default>
            </value>
            <value>
                <fullName>Executive_Escalation</fullName>
                <label>Executive Escalation</label>
                <default>false</default>
            </value>
            <value>
                <fullName>Standard_Queue</fullName>
                <label>Standard Queue</label>
                <default>false</default>
            </value>
        </valueSetDefinition>
        <valueSettings>
            <controllingFieldValue>checked</controllingFieldValue>
            <valueName>Safety_Recall</valueName>
        </valueSettings>
        <valueSettings>
            <controllingFieldValue>checked</controllingFieldValue>
            <valueName>Executive_Escalation</valueName>
        </valueSettings>
        <valueSettings>
            <controllingFieldValue>unchecked</controllingFieldValue>
            <valueName>Standard_Queue</valueName>
        </valueSettings>
    </valueSet>
</CustomField>
```

**How to read it**

- `checked` / `unchecked` are literals of the *matrix*, not of the checkbox field. The checkbox itself still
  deploys `<defaultValue>false</defaultValue>` and still reads `true`/`false` in Apex and SOQL. Writing
  `true` into `controllingFieldValue` is the single most common deploy failure on a checkbox-controlled
  matrix.
- A checkbox controller means the matrix has two columns and every dependent value must appear under one of
  them or it is unreachable in the UI. `Standard_Queue` under `unchecked` is what keeps the field usable on
  the default (unchecked) state.
- A checkbox cannot itself be dependent. Only a picklist has a `ValueSet`, and `controllingField` is a
  `ValueSet` element.

---

## 4. Chained dependency — a field that is both dependent and controlling

The guide's own sample does exactly this: "The `isAmerican__c` checkbox controls the list of manufacturers
shown in the `manufacturer__c` picklist. The `manufacturer__c` … in turn controls the list of models shown in
the `model__c` picklist" (api_meta.txt:44746–44749). So one field may carry `controllingField` (making it
dependent) *and* be named by another field's `controllingField` (making it controlling). Nothing in the
`ValueSet` definition caps the chain depth.

`force-app/main/default/objects/Warranty_Claim__c/fields/Component__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Component__c</fullName>
    <label>Component</label>
    <type>Picklist</type>
    <required>false</required>
    <trackTrending>false</trackTrending>
    <valueSet>
        <!-- Level 3: Product_Family__c -> Product_Line__c -> Component__c -->
        <controllingField>Product_Line__c</controllingField>
        <restricted>true</restricted>
        <valueSetDefinition>
            <sorted>false</sorted>
            <value>
                <fullName>Battery</fullName>
                <label>Battery</label>
                <default>false</default>
            </value>
            <value>
                <fullName>Display</fullName>
                <label>Display</label>
                <default>false</default>
            </value>
            <value>
                <fullName>Keyboard</fullName>
                <label>Keyboard</label>
                <default>false</default>
            </value>
        </valueSetDefinition>
        <valueSettings>
            <controllingFieldValue>Laptops</controllingFieldValue>
            <controllingFieldValue>Handsets</controllingFieldValue>
            <controllingFieldValue>Tablets</controllingFieldValue>
            <valueName>Battery</valueName>
        </valueSettings>
        <valueSettings>
            <controllingFieldValue>Laptops</controllingFieldValue>
            <controllingFieldValue>Desktops</controllingFieldValue>
            <controllingFieldValue>Handsets</controllingFieldValue>
            <controllingFieldValue>Tablets</controllingFieldValue>
            <valueName>Display</valueName>
        </valueSettings>
        <valueSettings>
            <controllingFieldValue>Laptops</controllingFieldValue>
            <controllingFieldValue>Desktops</controllingFieldValue>
            <valueName>Keyboard</valueName>
        </valueSettings>
    </valueSet>
</CustomField>
```

**How to read it**

- `Component__c`'s controlling values are `Product_Line__c` **values**, never `Product_Family__c` values. Each
  link in the chain sees only its immediate parent. A `<controllingFieldValue>Computers</controllingFieldValue>`
  here is a silent no-op pair, not an error.
- Nothing in the chain clears a stale grandchild. Choosing a different `Product_Family__c` filters
  `Product_Line__c` in the UI but leaves an already-stored `Component__c` in place. See
  `references/gotchas.md` Gotcha 2 and the cascade anti-pattern in `references/examples.md`.
- Setting `restricted` on every level is what stops a load from repairing itself into new values; it still
  does not stop a load writing `Handsets` + `Keyboard`.

---

## 5. Global value sets and the dependency

`GlobalValueSet` "isn't a field itself" (api_meta.txt:79344–79347) and carries no `controllingField` element
— its fields are `customValue`, `description`, `masterLabel`, `sorted` (api_meta.txt:79361–79374). The
dependency therefore always lives on the consuming field's own `ValueSet`. Two fields sharing one GVS need
two independently maintained matrices.

A GVS-backed field as the **controlling** side is unambiguous — the controlling field is referenced only by
name:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Support_Tier__c</fullName>
    <label>Support Tier</label>
    <type>Picklist</type>
    <valueSet>
        <!-- Controller: a local picklist. Its own values are irrelevant to the GVS below. -->
        <controllingField>Region__c</controllingField>
        <restricted>true</restricted>
        <valueSetName>Support_Tier_Values__gvs</valueSetName>
        <valueSettings>
            <controllingFieldValue>EMEA</controllingFieldValue>
            <controllingFieldValue>APAC</controllingFieldValue>
            <valueName>Follow_The_Sun</valueName>
        </valueSettings>
    </valueSet>
</CustomField>
```

UNVERIFIED (2026-09-05): whether a **GVS-backed field may be the dependent side** — the block above. The
Metadata API guide neither authorises nor forbids it. `ValueSet` lists `controllingField`, `valueSetName` and
`valueSettings` as peer elements (api_meta.txt:45843–45858), and the `valueSettings` description says the
picklist "can have its own unique value set, or inherit the values from a global value set"
(api_meta.txt:45855–45857) — which reads as permission. But the neighbouring skill
`admin/picklist-and-value-sets` (Gotcha 6) records the opposite from field experience: Setup does not offer a
GVS-backed field in the dependent-field list, and GVS-backed fields can only be the controlling side. Until
that is settled against Salesforce Help, model the **dependent** side as a local `valueSetDefinition` (§2) and
use the GVS only for the controlling field or for fields outside the matrix.

Note the `__gvs` suffix in `valueSetName`: "Any global value set created in API version 57.0 or later
automatically has the `__gvs` suffix appended to the developer name. When you make any CRUD-based call with
the `GlobalValueSet` type, you must append the suffix to the `fullName` field" (api_meta.txt:79418–79420).
See `admin/picklist-and-value-sets` for global value set authoring.

---

## 6. Record types layered on top

`RecordType.picklistValues` is a second, independent filter: `RecordTypePicklistValue` holds a `picklist`
(the field name) and `values` — "one or more of the picklist values in the picklist. Each value defined is
available in the record type that contains this component" (api_meta.txt:45045–45053). A value the record
type does not list is unavailable on records of that type whatever the dependency matrix says.

`force-app/main/default/objects/Warranty_Claim__c/recordTypes/Hardware.recordType-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<RecordType xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Hardware</fullName>
    <active>true</active>
    <label>Hardware Claim</label>
    <description>Warranty claims for physical goods.</description>
    <picklistValues>
        <picklist>Product_Family__c</picklist>
        <values>
            <fullName>Computers</fullName>
            <default>true</default>
        </values>
        <values>
            <fullName>Mobile</fullName>
            <default>false</default>
        </values>
    </picklistValues>
    <picklistValues>
        <picklist>Product_Line__c</picklist>
        <!-- Every dependent value reachable from Computers or Mobile must appear here,
             or the matrix will filter down to an empty list on this record type. -->
        <values>
            <fullName>Laptops</fullName>
            <default>false</default>
        </values>
        <values>
            <fullName>Desktops</fullName>
            <default>false</default>
        </values>
        <values>
            <fullName>Handsets</fullName>
            <default>false</default>
        </values>
        <values>
            <fullName>Tablets</fullName>
            <default>false</default>
        </values>
        <values>
            <fullName>Accessories</fullName>
            <default>false</default>
        </values>
    </picklistValues>
</RecordType>
```

**How to read it**

- `Peripherals` is deliberately absent from the `Product_Family__c` list, so the `Peripherals → Accessories`
  pair in §2 is dead on this record type. That is the intended interaction, and it is the check the script
  in `scripts/` performs.
- Record types and the dependency matrix compose by intersection: a value must be listed on the record type
  **and** enabled for the selected controlling value.
- The guide warns twice that retrieval is lossy here: "Metadata API doesn't retrieve specific picklist fields
  that are associated with a record type", and for person accounts "Metadata API retrieves standard picklist
  values only" (api_meta.txt:44985–44988). A round-trip retrieve is not proof the org matches source.

---

## 7. Enforcing the matrix on non-UI writes

Nothing in the matrix is enforced off the browser. The Apex Developer Guide's order of execution states it
before step 1: "Before Salesforce executes these events on the server, the browser runs JavaScript validation
if the record contains any dependent picklist fields. The validation limits each dependent picklist field to
its available values. **No other validation occurs on the client side.**" (apexdev.txt:15404–15406). The
server sequence that follows never mentions the dependency. Data Loader, Bulk API, REST, and Apex DML all
skip it.

`force-app/main/default/objects/Warranty_Claim__c/validationRules/Product_Line_Matches_Family.validationRule-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ValidationRule xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Product_Line_Matches_Family</fullName>
    <active>true</active>
    <description>Mirrors the Product_Family__c -> Product_Line__c dependency matrix for API and Data Loader writes.</description>
    <errorConditionFormula>AND(
  NOT(ISBLANK(TEXT(Product_Family__c))),
  NOT(ISBLANK(TEXT(Product_Line__c))),
  NOT(
    OR(
      AND(ISPICKVAL(Product_Family__c, &quot;Computers&quot;),
          OR(ISPICKVAL(Product_Line__c, &quot;Laptops&quot;),
             ISPICKVAL(Product_Line__c, &quot;Desktops&quot;),
             ISPICKVAL(Product_Line__c, &quot;Accessories&quot;))),
      AND(ISPICKVAL(Product_Family__c, &quot;Mobile&quot;),
          OR(ISPICKVAL(Product_Line__c, &quot;Handsets&quot;),
             ISPICKVAL(Product_Line__c, &quot;Tablets&quot;),
             ISPICKVAL(Product_Line__c, &quot;Accessories&quot;))),
      AND(ISPICKVAL(Product_Family__c, &quot;Peripherals&quot;),
          ISPICKVAL(Product_Line__c, &quot;Accessories&quot;))
    )
  )
)</errorConditionFormula>
    <errorDisplayField>Product_Line__c</errorDisplayField>
    <errorMessage>Product Line is not valid for the selected Product Family.</errorMessage>
</ValidationRule>
```

**How to read it**

- The rule restates the matrix. It is duplication, and it is the only way the matrix reaches a Bulk API job.
  Keep the two in one commit — the checker in `scripts/` fails a dependent field with no rule naming both
  fields.
- `<` `>` `&` inside `errorConditionFormula` must be XML-escaped (`&quot;` for the string quotes here).
- The blank guards matter: without them the rule fires on every partial load that sets the family before the
  line.
- Validation rules "can't have compound fields. Examples of compound fields include addresses, first and last
  names, dependent picklists, and dependent lookups" (api_meta.txt:45370–45371) — that constrains referencing
  a dependent picklist *as a compound unit*; `ISPICKVAL` on the individual field, as above, is the supported
  form.

---

## 8. package.xml and deploy order

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Warranty_Claim__c.Product_Family__c</members>
        <members>Warranty_Claim__c.Expedited__c</members>
        <members>Warranty_Claim__c.Product_Line__c</members>
        <members>Warranty_Claim__c.Expedite_Reason__c</members>
        <members>Warranty_Claim__c.Component__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Warranty_Claim__c.Hardware</members>
        <name>RecordType</name>
    </types>
    <types>
        <members>Warranty_Claim__c.Product_Line_Matches_Family</members>
        <name>ValidationRule</name>
    </types>
    <version>62.0</version>
</Package>
```

Deploy order inside one deployment (Salesforce resolves it, but author the manifest in this order so a
partial retry stays legal):

1. **Controlling fields first** — `Product_Family__c`, `Expedited__c`. A `<controllingField>` that names a
   field not yet in the org fails the dependent field's deploy.
2. **Dependent fields** — `Product_Line__c`, `Expedite_Reason__c`, then `Component__c` last, because
   `Component__c` names `Product_Line__c` as its controller.
3. **Record types** — they reference picklist values, so the values must exist.
4. **Validation rules** — they reference both fields by API name.

```bash
# Pull the current matrix before editing anything
sf project retrieve start \
    --metadata "CustomField:Warranty_Claim__c.Product_Line__c" \
    --metadata "CustomField:Warranty_Claim__c.Product_Family__c" \
    --metadata "RecordType:Warranty_Claim__c.Hardware" \
    --target-org myorg

# Validate-only against production before the real deploy
sf project deploy validate --manifest manifest/package.xml --target-org prod

sf project deploy start --manifest manifest/package.xml --target-org myorg
```

`CustomField` and `RecordType` are per-member types here on purpose. The deprecated `Picklist` type "doesn't
support the wildcard character `*` … in the package.xml manifest file" (api_meta.txt:44894–44896); listing
members explicitly also keeps the diff reviewable.

**Removal is not a deploy.** "You can add field dependency values via the Metadata API but not remove them"
(api_meta.txt:45855–45858, repeated at 45873–45875). Dropping a `<valueSettings>` block from source and
deploying leaves the pair enabled in the org. Un-mapping is a Setup action: Object Manager → the object →
Fields & Relationships → the dependent field → **Field Dependencies** → Edit. Re-retrieve afterwards so
source matches the org.

---

## 9. Verifying it landed

**Apex describe — proves the dependency exists and names the controller.** `DescribeFieldResult` exposes
`isDependentPicklist()` "Returns true if the picklist is a dependent picklist" (apexrefguide.txt:191169–191178)
and `getController()` "Returns the token of the controlling field" (apexrefguide.txt:190710–190720).

```apex
Schema.DescribeFieldResult dep = Warranty_Claim__c.Product_Line__c.getDescribe();
System.debug('dependent? ' + dep.isDependentPicklist());          // expect true
System.debug('controller: ' + dep.getController());               // expect Product_Family__c
System.debug('restricted? ' + dep.isRestrictedPicklist());        // expect true
for (Schema.PicklistEntry pe : dep.getPicklistValues()) {
    System.debug(pe.getValue() + ' active=' + pe.isActive());
}
```

Describe confirms *that* a dependency exists; it does not return the matrix. `Schema.PicklistEntry` exposes
only `getLabel()`, `getValue()`, `isActive()` and `isDefaultValue()` (apexrefguide.txt:193673–193685) — there
is no `getValidFor()` on it. To read pair-by-pair, use the UI API `getPicklistValues` payload
(`controllerValues` + `validFor`) or Setup.

**SOQL — find rows the matrix would now reject.** Run this before and after, on real data; a non-zero count
after deploy is the backlog the validation rule will start blocking.

```sql
SELECT Product_Family__c, Product_Line__c, COUNT(Id)
FROM Warranty_Claim__c
WHERE (Product_Family__c = 'Computers' AND Product_Line__c NOT IN ('Laptops','Desktops','Accessories'))
   OR (Product_Family__c = 'Mobile'    AND Product_Line__c NOT IN ('Handsets','Tablets','Accessories'))
   OR (Product_Family__c = 'Peripherals' AND Product_Line__c != 'Accessories')
GROUP BY Product_Family__c, Product_Line__c
```

**Setup check — the matrix itself.** Object Manager → `Warranty_Claim__c` → Fields & Relationships →
`Product_Line__c` → **Field Dependencies**. The grid is the only first-party view of the enabled pairs, and
the only place to disable one. Count the shaded cells and compare against the `<valueSettings>` pair count in
source — the checker prints that count for you.

---

## Related reading

- `references/gotchas.md` — the platform behaviours these files trip over
- `references/examples.md` — the LWC side and the cascade anti-pattern
- `admin/picklist-and-value-sets` — authoring the value sets themselves, global value sets, `__gvs`
- `admin/record-types-and-page-layouts` — the record-type filter in its own right
- `admin/custom-field-creation` — the rest of the `CustomField` element surface
