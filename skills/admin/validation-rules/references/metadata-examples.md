# Metadata Examples: Validation Rules

Deployable XML for the `ValidationRule` metadata type, shaped from the Metadata API Developer Guide's own
sample definition and field table, then extended to a realistic Opportunity example.

---

## The type in one table

`ValidationRule` extends `Metadata` and inherits `fullName`. Available in **API version 12.0 and later**.

| Element | Type | Required | Behaviour (Metadata API Developer Guide, ValidationRule) |
|---|---|---|---|
| `fullName` | string | yes | Internal name. Must start with a letter; may contain letters, characters, or `_`; can't end with `_`; can't contain two consecutive underscores |
| `active` | boolean | yes | `true` = rule enforces, `false` = rule is deployed but silent |
| `description` | string | no | Free text; the only place the business justification survives a sandbox refresh |
| `errorConditionFormula` | string | yes | If the formula returns `true`, the error message is displayed |
| `errorDisplayField` | string | no | Fully specified field name. **If you do not specify a value, or the field isn't visible on the page layout, the value changes automatically to Top of Page** |
| `errorMessage` | string | yes | **Must be 255 characters or less** |

Two version gates from the same section:

- **As of API version 20.0, validation rules can't have compound fields.** Examples of compound fields are addresses, first and last names, dependent picklists, and dependent lookups.
- **As of API version 40.0, you can use validation rules with custom metadata types.**

---

## Where the file lives

The guide documents the **CustomObject-embedded** shape: rules are `<validationRules>` elements inside the
object file, and "the file suffix is `.object` for the custom object or standard object file… stored in the
`objects` folder in the corresponding package directory" (Metadata API Developer Guide, CustomObject →
Declarative Metadata File Suffix and Directory Location). `ValidationRule` is listed under CustomObject's
"Declarative Metadata Additional Components", alongside `CustomField`, `ListView` and `RecordType`.

Salesforce DX **source format** splits each rule into its own file:

```text
force-app/main/default/objects/Opportunity/validationRules/Opportunity_ACV_RequiredAtProposal.validationRule-meta.xml
```

whose root element is `<ValidationRule>` rather than `<CustomObject>`. Both shapes carry the same child
elements. `sf project deploy` converts source format to metadata format on the way to the org, so a rule you
author in either shape deploys identically.

> UNVERIFIED (2026-09-04): the Metadata API Developer Guide documents only the metadata-format `.object`
> layout; the string `validationRule-meta` does not appear anywhere in it, so the DX directory and file
> suffix above are not confirmed by the guide text used for this skill. The **element names and semantics**
> in the table above ARE confirmed and are identical in both shapes.

---

## Example 1 — metadata format, three rules inside the object file

Modelled on the guide's own `CatsRule` sample, extended to a realistic Opportunity object.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <validationRules>
        <fullName>Opportunity_CloseDate_RequiredWhenClosed</fullName>
        <active>true</active>
        <description>Revenue forecasting and the contract-generation integration both read CloseDate. Owner: RevOps. Bypass: Bypass_Validation_Opportunity.</description>
        <errorConditionFormula>AND(
  NOT($Permission.Bypass_Validation_Opportunity),
  OR(
    ISPICKVAL(StageName, "Closed Won"),
    ISPICKVAL(StageName, "Closed Lost")
  ),
  ISBLANK(CloseDate)
)</errorConditionFormula>
        <errorDisplayField>CloseDate</errorDisplayField>
        <errorMessage>Enter a Close Date before setting the Stage to Closed Won or Closed Lost. Forecasting and contract generation both read this date.</errorMessage>
    </validationRules>
    <validationRules>
        <fullName>Opportunity_ACV_RequiredAtProposal</fullName>
        <active>true</active>
        <description>Enterprise deals must carry an ACV from Proposal onward. Scoped to the Enterprise record type only. Owner: RevOps.</description>
        <errorConditionFormula>AND(
  NOT($Permission.Bypass_Validation_Opportunity),
  RecordType.DeveloperName = "Enterprise",
  OR(
    ISPICKVAL(StageName, "Proposal/Quote"),
    ISPICKVAL(StageName, "Negotiation/Review"),
    ISPICKVAL(StageName, "Closed Won")
  ),
  ISBLANK(ACV__c)
)</errorConditionFormula>
        <errorDisplayField>ACV__c</errorDisplayField>
        <errorMessage>Enter the Annual Contract Value. Enterprise opportunities need an ACV from Proposal/Quote onward so the deal desk can price the renewal.</errorMessage>
    </validationRules>
    <validationRules>
        <fullName>Opportunity_Stage_CannotRegressFromClosedWon</fullName>
        <active>false</active>
        <description>Shipped inactive on 2026-09-04. Activate after the 480 open backdated deals are cleaned up; see RevOps ticket. Uses PRIORVALUE, so it is guarded with NOT(ISNEW()).</description>
        <errorConditionFormula>AND(
  NOT($Permission.Bypass_Validation_Opportunity),
  NOT(ISNEW()),
  ISPICKVAL(PRIORVALUE(StageName), "Closed Won"),
  NOT(ISPICKVAL(StageName, "Closed Won"))
)</errorConditionFormula>
        <errorMessage>A Closed Won opportunity cannot be reopened. Create a renewal or an upsell opportunity instead, or ask RevOps to reverse the booking.</errorMessage>
    </validationRules>
</CustomObject>
```

### How to read it

- **`<validationRules>` repeats** — one element per rule, all inside one `<CustomObject>` root. There is no
  wrapper element around the collection.
- **Bypass clause is first inside the `AND`.** `NOT($Permission.Bypass_Validation_Opportunity)` short-circuits
  the whole rule for anyone holding the Custom Permission. The bypass contract — this Custom Permission plus
  the `Integration_Bypass__c` hierarchy Custom Setting, and why an org wants both — is defined once in
  `templates/admin/validation-rule-patterns.md`; do not restate it per rule, reference it.
- **Relevance gate second** — `RecordType.DeveloperName = "Enterprise"` and the stage list. `DeveloperName` is
  a text field, so it is compared with `=`, not `ISPICKVAL`.
- **Business condition last** — `ISBLANK(...)`. The formula describes the **invalid** state; the rule fires and
  blocks the save when it evaluates to `true`.
- **`errorDisplayField` is a field API name, unqualified** — `CloseDate`, not `Opportunity.CloseDate`. Rule 3
  omits it deliberately because the error is about a stage transition, not one field.
- **`active=false` deploys a real, dormant rule.** Rule 3 exists in Setup, is retrievable, is version
  controlled, and enforces nothing. This is how you land a rule ahead of the data cleanup it depends on —
  flip `active` to `true` in a later, one-line deploy instead of authoring the rule under time pressure.
- **Newlines inside `<errorConditionFormula>` are preserved** and are what you see in Setup. Indent the
  formula for the next admin, not for the XML.
- **`<` and `&` must be escaped** in formula text (`&lt;`, `&amp;`). Prefer double-quoted string literals so
  you never need `&apos;`. The guide's own sample uses `&apos;` for single quotes.

> Doc quirk worth knowing: the guide's `CatsRule` sample definition prints `<validationMessage>` where its own
> field table names the element **`errorMessage`**. `errorMessage` is the element name in the field table and
> is the one that deploys.

---

## Example 2 — DX source format, one rule per file

`force-app/main/default/objects/Opportunity/validationRules/Opportunity_CloseDate_RequiredWhenClosed.validationRule-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ValidationRule xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Opportunity_CloseDate_RequiredWhenClosed</fullName>
    <active>true</active>
    <description>Revenue forecasting and the contract-generation integration both read CloseDate. Owner: RevOps. Bypass: Bypass_Validation_Opportunity.</description>
    <errorConditionFormula>AND(
  NOT($Permission.Bypass_Validation_Opportunity),
  OR(
    ISPICKVAL(StageName, "Closed Won"),
    ISPICKVAL(StageName, "Closed Lost")
  ),
  ISBLANK(CloseDate)
)</errorConditionFormula>
    <errorDisplayField>CloseDate</errorDisplayField>
    <errorMessage>Enter a Close Date before setting the Stage to Closed Won or Closed Lost. Forecasting and contract generation both read this date.</errorMessage>
</ValidationRule>
```

In source format the file name carries the rule name, so `<fullName>` is redundant but harmless and is what
`sf project retrieve` writes.

---

## Example 3 — a rule on a custom metadata type

Supported as of API version 40.0. The rule lives inside the `.object` file for the type, exactly as it does
for an sObject:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <validationRules>
        <fullName>Tier_Threshold_MustBeAscending</fullName>
        <active>true</active>
        <description>Discount tiers must not overlap. Custom metadata type rules fire on the metadata record save, not on business-record DML.</description>
        <errorConditionFormula>AND(
  NOT(ISBLANK(Min_Amount__c)),
  NOT(ISBLANK(Max_Amount__c)),
  Max_Amount__c &lt;= Min_Amount__c
)</errorConditionFormula>
        <errorDisplayField>Max_Amount__c</errorDisplayField>
        <errorMessage>Max Amount must be greater than Min Amount. Overlapping discount tiers make the pricing lookup non-deterministic.</errorMessage>
    </validationRules>
</CustomObject>
```

Note `&lt;` — a bare `<` inside `errorConditionFormula` makes the file invalid XML and the deploy fails at
parse time with no rule-level error.

---

## package.xml

`ValidationRule` **doesn't support the wildcard character `*`** in `package.xml` (Metadata API Developer
Guide, ValidationRule → Wildcard Support in the Manifest File). Name each rule, or retrieve the whole object.

**Named rules** — `objectName.ruleName`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Opportunity.Opportunity_CloseDate_RequiredWhenClosed</members>
        <members>Opportunity.Opportunity_ACV_RequiredAtProposal</members>
        <members>Opportunity.Opportunity_Stage_CannotRegressFromClosedWon</members>
        <name>ValidationRule</name>
    </types>
    <types>
        <members>Bypass_Validation_Opportunity</members>
        <name>CustomPermission</name>
    </types>
    <version>62.0</version>
</Package>
```

> UNVERIFIED (2026-09-04): the guide prints the `objectName.componentName` `<members>` syntax explicitly for
> the `CustomField` (`Account.SLA__c`, `MyCustomObject__c.MyCustomField__c`) and `ListView`
> (`Account.AccountTeam`) sub-components of CustomObject, but shows no `ValidationRule` manifest sample.
> `Object.RuleName` follows the documented sub-component pattern; it is not stated for this type in the guide.

**Whole object** — safest when you are unsure of a rule name, and the guide's recommended route for list
views on standard objects for the same reason. Retrieving the object returns every rule on it:

```xml
<types>
    <members>Opportunity</members>
    <name>CustomObject</name>
</types>
```

Retrieving a `CustomObject` also "makes the component appear in any Profile and PermissionSet components that
are retrieved in the same package" — check your diff before committing.

---

## sf CLI commands

```bash
# Retrieve the three named rules plus the bypass Custom Permission
sf project retrieve start \
  --metadata "ValidationRule:Opportunity.Opportunity_CloseDate_RequiredWhenClosed" \
  --metadata "ValidationRule:Opportunity.Opportunity_ACV_RequiredAtProposal" \
  --metadata "CustomPermission:Bypass_Validation_Opportunity" \
  --target-org devhub-sandbox

# Retrieve every rule on the object (also pulls fields, layouts, record types)
sf project retrieve start --metadata "CustomObject:Opportunity" --target-org devhub-sandbox

# Lint before you deploy
python3 skills/admin/validation-rules/scripts/check_validation_rules.py \
  --manifest-dir force-app/main/default/objects

# Validate-only against production: compiles and runs tests, commits nothing
sf project deploy validate \
  --source-dir force-app/main/default/objects/Opportunity \
  --test-level RunSpecifiedTests \
  --tests OpportunityValidationRuleTest \
  --target-org production

# Deploy for real
sf project deploy start \
  --source-dir force-app/main/default/objects/Opportunity \
  --test-level RunSpecifiedTests \
  --tests OpportunityValidationRuleTest \
  --target-org production
```

Run the deploy **against a sandbox with the integration user present** first. A validate-only deploy proves
the XML parses and the formula compiles; it does not prove the integration user still gets its records in.

---

## Verification after deploy

**1. Confirm the rules landed and their active state — Tooling API SOQL:**

```sql
SELECT Id, ValidationName, Active, ErrorDisplayField, ErrorMessage
FROM ValidationRule
WHERE EntityDefinition.QualifiedApiName = 'Opportunity'
ORDER BY ValidationName
```

Run with `sf data query --use-tooling-api --target-org production`. Expect
`Opportunity_Stage_CannotRegressFromClosedWon` to come back with `Active = false` — that is the deploy
working, not failing.

**2. Setup check:** Setup → Object Manager → Opportunity → Validation Rules. The list shows Rule Name, Active,
Error Message and the modified-by stamp. Confirm the error message reads as a full sentence in the list, not
as a truncated fragment — the list is where the next admin meets it.

**3. Prove the rule actually blocks, and that the bypass actually bypasses.** Setup showing "Active" proves
neither. The two Apex tests below do.

---

## Apex tests

Both patterns come from the Apex Developer Guide. The first uses partial-save `Database.insert` so the test
inspects `Database.Error` objects rather than catching an exception; the second is the guide's own
`System.runAs` negative-test shape for a validation rule.

### Test 1 — the rule fires and names the right field

```apex
@IsTest
private class OpportunityValidationRuleTest {

    @IsTest
    static void closeDateRule_blocksClosedWonWithNoCloseDate() {
        Opportunity opp = new Opportunity(
            Name       = 'VR test - closed with no date',
            StageName  = 'Closed Won',
            CloseDate  = null
        );

        Test.startTest();
        // allOrNone = false -> partial save, so the failure comes back as a
        // SaveResult instead of throwing. This is how you assert on one record
        // in a bulk context without aborting the rest of the DML.
        Database.SaveResult sr = Database.insert(opp, false);
        Test.stopTest();

        Assert.isFalse(sr.isSuccess(), 'Validation rule did not fire; the record saved.');

        Boolean sawRule = false;
        for (Database.Error err : sr.getErrors()) {
            // Database.Error exposes getStatusCode(), getMessage() and getFields().
            if (String.valueOf(err.getStatusCode()) == 'FIELD_CUSTOM_VALIDATION_EXCEPTION') {
                sawRule = true;
                Assert.isTrue(
                    err.getMessage().contains('Enter a Close Date'),
                    'Wrong validation rule fired: ' + err.getMessage()
                );
                // getFields() reflects errorDisplayField. Asserting it is what
                // catches a later edit that drops errorDisplayField and silently
                // relocates the error to Top of Page.
                Assert.isTrue(
                    new Set<String>(err.getFields()).contains('CloseDate'),
                    'Error was not attached to CloseDate: ' + err.getFields()
                );
            }
        }
        Assert.isTrue(sawRule, 'No FIELD_CUSTOM_VALIDATION_EXCEPTION in: ' + sr.getErrors());
    }
}
```

The status-code string `FIELD_CUSTOM_VALIDATION_EXCEPTION` is the value the Apex Developer Guide asserts in
its own validation-rule test (`Assert.areEqual('FIELD_CUSTOM_VALIDATION_EXCEPTION', e.getDmlStatusCode(0))`).
`Database.Error.getStatusCode()` returns a `System.StatusCode`; the guide states the full list of status codes
lives in your org's WSDL rather than in the reference, which is why this example compares the string form.

### Test 2 — the bypass permission suppresses the rule

```apex
@IsTest
static void closeDateRule_isBypassedByCustomPermission() {
    // A permission set that grants Bypass_Validation_Opportunity.
    PermissionSet bypassPs = [
        SELECT Id FROM PermissionSet
        WHERE Name = 'Integration_BypassValidation' LIMIT 1
    ];

    Profile p = [SELECT Id FROM Profile WHERE Name = 'Standard User' LIMIT 1];
    User integrationUser = new User(
        Alias             = 'vrbypas',
        Email             = 'vr.bypass@example.invalid',
        LastName          = 'BypassTest',
        Username          = 'vr.bypass.' + DateTime.now().getTime() + '@example.invalid',
        ProfileId         = p.Id,
        EmailEncodingKey  = 'UTF-8',
        LanguageLocaleKey = 'en_US',
        LocaleSidKey      = 'en_US',
        TimeZoneSidKey    = 'America/Los_Angeles'
    );
    insert integrationUser;
    insert new PermissionSetAssignment(
        AssigneeId      = integrationUser.Id,
        PermissionSetId = bypassPs.Id
    );

    Opportunity opp = new Opportunity(
        Name      = 'VR bypass - closed with no date',
        StageName = 'Closed Won',
        CloseDate = null
    );

    Test.startTest();
    System.runAs(integrationUser) {
        Database.SaveResult sr = Database.insert(opp, false);
        Assert.isTrue(
            sr.isSuccess(),
            'Bypass permission did not suppress the rule: ' + sr.getErrors()
        );
    }
    Test.stopTest();
}
```

Two things this test protects that nothing else does:

- Someone edits the rule and drops the `NOT($Permission...)` clause. Test 1 still passes. Test 2 fails.
- Someone renames the Custom Permission. The formula silently evaluates the missing permission as false for
  everyone, the bypass stops working, and only Test 2 notices.

If the rule uses the `VLOOKUP` function, add `@IsTest(SeeAllData=true)`: as of API version 28.0 the `VLOOKUP`
validation rule function no longer reads org data from a running Apex test and sees only data the test
created, so a `VLOOKUP`-based rule can pass in a test and fail in production.
