# Metadata Examples — Matching Rules and Duplicate Rules

Deployable shapes for the two metadata types behind Duplicate Management. Element names, enum values, and the skeletons come from the Metadata API Developer Guide (`MatchingRule` and `DuplicateRule` sections of the v66 PDF); the worked examples extend the guide's own sample definitions to a realistic Contact + Lead configuration. Lint the pair before deploying:

```bash
python3 skills/admin/duplicate-management/scripts/check_duplicate_rules.py --manifest-dir force-app/main/default
```

## Where the files live

| Type | package.xml `<name>` | File in a DX project | Granularity |
|---|---|---|---|
| Matching rule | `MatchingRule` for one rule (`<members>Contact.Contact_Identity</members>`); `MatchingRules` with `*` for all | `matchingRules/Contact.matchingRule-meta.xml` | **One file per object** — every matching rule for that object is a `<matchingRules>` element inside the single `<MatchingRules>` root |
| Duplicate rule | `DuplicateRule` (`<members>Contact.Contact_Identity_Guard</members>`) | `duplicateRules/Contact.Contact_Identity_Guard.duplicateRule-meta.xml` | **One file per rule** — the file name is `<Object>.<RuleName>` |

The guide states the file naming directly: matching rule files are named for "the standard or custom object name that is associated with the matching rule", while its duplicate-rule example is `duplicateRules/Account.Standard_Account_Duplicate_Rule.duplicateRule`. Both types accept `*` in package.xml.

The two types are asymmetric in a way that bites during retrieve: editing one matching rule means editing the object's whole matching-rule file, so two people tuning two different rules on Contact collide on one file.

## Contact matching rule: exact email, or fuzzy first + last name

```xml
<?xml version="1.0" encoding="UTF-8"?>
<MatchingRules xmlns="http://soap.sforce.com/2006/04/metadata">
    <matchingRules>
        <fullName>Contact_Identity</fullName>
        <label>Contact identity: email, or first plus last name</label>
        <description>Exact business email, or fuzzy first name combined with fuzzy last name. A blank email never matches another blank email.</description>
        <booleanFilter>1 OR (2 AND 3)</booleanFilter>
        <matchingRuleItems>
            <blankValueBehavior>NullNotAllowed</blankValueBehavior>
            <fieldName>Email</fieldName>
            <matchingMethod>Exact</matchingMethod>
        </matchingRuleItems>
        <matchingRuleItems>
            <blankValueBehavior>NullNotAllowed</blankValueBehavior>
            <fieldName>FirstName</fieldName>
            <matchingMethod>FirstName</matchingMethod>
        </matchingRuleItems>
        <matchingRuleItems>
            <blankValueBehavior>NullNotAllowed</blankValueBehavior>
            <fieldName>LastName</fieldName>
            <matchingMethod>LastName</matchingMethod>
        </matchingRuleItems>
        <ruleStatus>Active</ruleStatus>
    </matchingRules>
    <!-- Second rule on the SAME object lives in the SAME file. -->
    <matchingRules>
        <fullName>Contact_Phone_Fallback</fullName>
        <label>Contact identity: phone plus last name</label>
        <description>Catches records created without an email address by the call centre.</description>
        <matchingRuleItems>
            <blankValueBehavior>NullNotAllowed</blankValueBehavior>
            <fieldName>Phone</fieldName>
            <matchingMethod>Phone</matchingMethod>
        </matchingRuleItems>
        <matchingRuleItems>
            <blankValueBehavior>NullNotAllowed</blankValueBehavior>
            <fieldName>LastName</fieldName>
            <matchingMethod>LastName</matchingMethod>
        </matchingRuleItems>
        <ruleStatus>Inactive</ruleStatus>
    </matchingRules>
</MatchingRules>
```

How to read it:

- `matchingMethod` is a closed enum. The guide lists exactly: `Exact`, `FirstName`, `LastName`, `CompanyName`, `Phone`, `City`, `Street`, `Zip`, `Title`. There is no `Email` method and no `State` method — email and every other field you want compared character-for-character use `Exact`.
- `blankValueBehavior` is `MatchBlanks` or `NullNotAllowed`, and **`NullNotAllowed` is the default**. Leaving it off Email is therefore safe; setting `MatchBlanks` is what makes every emailless Contact a duplicate of every other emailless Contact.
- `booleanFilter` numbers the `matchingRuleItems` in document order: item 1 is Email, 2 is FirstName, 3 is LastName. Omit it and the items are ANDed, which turns this rule into "email AND first AND last" and stops catching the case it was written for.
- `ruleStatus` accepts six values on the object (`Inactive`, `Deactivating`, `DeactivationFailed`, `Active`, `Activating`, `ActivationFailed`) but the guide is explicit: "The only valid values you can declare when deploying a package are `Active` and `Inactive`."
- There is no `objectName` element. The object comes from the file name only, which is why a copied file that keeps the old name silently targets the wrong object.

## Lead-to-Contact duplicate rule with `objectMapping`

The matching rule referenced here is defined on **Contact** (the object being searched), while the duplicate rule is defined on **Lead** (the object being saved).

`duplicateRules/Lead.Lead_To_Contact_Identity.duplicateRule-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<DuplicateRule xmlns="http://soap.sforce.com/2006/04/metadata"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <actionOnInsert>Allow</actionOnInsert>
    <actionOnUpdate>Allow</actionOnUpdate>
    <alertText>This person already exists as a Contact. Open the existing Contact instead of creating a Lead.</alertText>
    <description>Flags a new Lead that already exists as a Contact so reps convert rather than duplicate.</description>
    <duplicateRuleFilter>
        <booleanFilter xsi:nil="true"/>
    </duplicateRuleFilter>
    <duplicateRuleMatchRules>
        <matchRuleSObjectType>Contact</matchRuleSObjectType>
        <matchingRule>Contact_Identity</matchingRule>
        <objectMapping>
            <inputObject>Lead</inputObject>
            <mappingFields>
                <inputField>Email</inputField>
                <outputField>Email</outputField>
            </mappingFields>
            <mappingFields>
                <inputField>FirstName</inputField>
                <outputField>FirstName</outputField>
            </mappingFields>
            <mappingFields>
                <inputField>LastName</inputField>
                <outputField>LastName</outputField>
            </mappingFields>
            <outputObject>Contact</outputObject>
        </objectMapping>
    </duplicateRuleMatchRules>
    <isActive>true</isActive>
    <masterLabel>Lead to Contact Identity</masterLabel>
    <operationsOnInsert>Alert</operationsOnInsert>
    <operationsOnInsert>Report</operationsOnInsert>
    <operationsOnUpdate>Alert</operationsOnUpdate>
    <securityOption>EnforceSharingRules</securityOption>
    <sortOrder>1</sortOrder>
</DuplicateRule>
```

How to read it:

- `matchingRule` holds "the value that corresponds to the value of `developerName` in the MatchingRule" — the rule's `fullName`, not its `label`.
- `matchRuleSObjectType` is the **target** object. The guide's own words: "if you define a duplicate rule for Contact records, and you want to match with Lead records, the value of `matchRuleSObjectType` is `Lead`."
- `objectMapping` translates the saving object's fields into the target object's fields. `outputObject` must equal `matchRuleSObjectType`, and the guide adds the consequence that is easy to miss: "Any duplicate rules that this object has are ignored when the DuplicateRule API uses the ObjectMapping." A cross-object rule does not chain into the target object's own rules.
- `operationsOnInsert` / `operationsOnUpdate` are arrays; repeat the element for `Alert` and `Report`. `Report` is what materialises `DuplicateRecordSet` rows for the steward queue.
- The field descriptions spell the values lowercase (`alert`, `report`) while the guide's own sample XML uses `Alert` and `Report`. The sample is the shape to copy.
- The empty `duplicateRuleFilter` with `<booleanFilter xsi:nil="true"/>` is how the guide's sample expresses "no filter" for a field the guide marks Required. Declare the `xsi` namespace on the root or the `nil` attribute is not understood.
- `sortOrder` "determines the order in which duplicate rules are applied" — two rules on one object with the same `sortOrder` have no defined precedence.

## Block on insert, alert on update, scoped by a filter

`duplicateRules/Contact.Contact_Identity_Guard.duplicateRule-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<DuplicateRule xmlns="http://soap.sforce.com/2006/04/metadata">
    <actionOnInsert>Block</actionOnInsert>
    <actionOnUpdate>Allow</actionOnUpdate>
    <alertText>A Contact with this email already exists. Update the existing record instead.</alertText>
    <description>Blocks new duplicate Contacts on the Business record type; warns on edits that create a collision.</description>
    <duplicateRuleFilter>
        <booleanFilter>1</booleanFilter>
        <duplicateRuleFilterItems>
            <field>RecordTypeId</field>
            <operation>equals</operation>
            <value>Business_Contact</value>
            <sortOrder>1</sortOrder>
            <table>Contact</table>
        </duplicateRuleFilterItems>
    </duplicateRuleFilter>
    <duplicateRuleMatchRules>
        <matchRuleSObjectType>Contact</matchRuleSObjectType>
        <matchingRule>Contact_Identity</matchingRule>
        <objectMapping>
            <inputObject>Contact</inputObject>
            <mappingFields>
                <inputField>Email</inputField>
                <outputField>Email</outputField>
            </mappingFields>
            <outputObject>Contact</outputObject>
        </objectMapping>
    </duplicateRuleMatchRules>
    <isActive>true</isActive>
    <masterLabel>Contact Identity Guard</masterLabel>
    <operationsOnUpdate>Alert</operationsOnUpdate>
    <operationsOnUpdate>Report</operationsOnUpdate>
    <securityOption>BypassSharingRules</securityOption>
    <sortOrder>2</sortOrder>
</DuplicateRule>
```

How to read it:

- **`alertText` is legal here only because `actionOnUpdate` is `Allow`.** The guide: "You can set a value for `alertText` only when you have `actionOnInsert` or `actionOnUpdate` (or both) set to `Allow`. Otherwise, you receive a validation error when you add or update this component." A rule that blocks both operations must not carry `alertText` at all, and the checker script flags that combination.
- `operationsOnInsert` is absent because `actionOnInsert` is `Block`; the operations arrays only govern what happens when the matching action is `Allow`.
- `duplicateRuleFilter` scopes which records the rule even considers. `field` is the bare API name and `table` names the object holding it, matching the guide's `<field>Username</field>` / `<table>User</table>` sample. `operation` comes from the shared `FilterOperation` enum (`equals`, `notEqual`, `lessThan`, `greaterThan`, `lessOrEqual`, `greaterOrEqual`, `contains`, `notContain`, `startsWith`, `includes`, `excludes`).
- UNVERIFIED (2026-09-04): the guide's filter sample uses a plain text value (`user@example.com`) and does not show a record-type filter, so whether `RecordTypeId` accepts the record type's **developer name** (as written above) or requires an 18-character Id is not established by the Metadata API guide. Deploy this filter to a sandbox and re-read the retrieved XML before promoting it.
- `securityOption` is `EnforceSharingRules` or `BypassSharingRules`. `BypassSharingRules` is the right choice for a Block rule, because under `EnforceSharingRules` a duplicate the running user cannot see lets the save proceed with "No message is issued."

## package.xml and CLI

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Contact.Contact_Identity</members>
        <members>Contact.Contact_Phone_Fallback</members>
        <name>MatchingRule</name>
    </types>
    <types>
        <members>Contact.Contact_Identity_Guard</members>
        <members>Lead.Lead_To_Contact_Identity</members>
        <name>DuplicateRule</name>
    </types>
    <version>66.0</version>
</Package>
```

To take every matching rule in the org instead, use the plural type with a wildcard, exactly as the guide shows:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>*</members>
        <name>MatchingRules</name>
    </types>
    <version>66.0</version>
</Package>
```

On the API version: the guide's `DuplicateRule` section says "DuplicateRule components are available in API version 66.0 and later" while its own sample package.xml for the same type uses `<version>38.0</version>`, and the `MatchingRule` samples use `66.0`. UNVERIFIED (2026-09-04): which of those two `DuplicateRule` statements is current is not resolvable from the guide text alone. Deploy with your org's API version and confirm the type is retrievable before relying on either number.

```bash
# 1. Pull what the org already has, so you edit rather than overwrite
sf project retrieve start \
  --metadata MatchingRule:Contact.Contact_Identity DuplicateRule:Contact.Contact_Identity_Guard \
  --target-org my-sandbox

# Or the whole object's matching rules in one go (single file comes back)
sf project retrieve start --metadata MatchingRules --target-org my-sandbox

# 2. Lint the pair, then validate without deploying
python3 skills/admin/duplicate-management/scripts/check_duplicate_rules.py --manifest-dir force-app/main/default
sf project deploy validate --source-dir force-app/main/default --target-org my-sandbox

# 3. Deploy matching rules first, then the duplicate rules that reference them
sf project deploy start --source-dir force-app/main/default/matchingRules --target-org my-sandbox
sf project deploy start --source-dir force-app/main/default/duplicateRules --target-org my-sandbox
```

UNVERIFIED (2026-09-04): the two-step deploy order above is defensive, not documented. The Metadata API guide does not state that a `MatchingRule` must already exist and be `Active` before a `DuplicateRule` referencing it will deploy. What *is* documented is the runtime dependency — `Datacloud.FindDuplicates` throws `System.HandledException` with "No active duplicate rules are defined for the {ObjectName} object type" when nothing is active — and that matching-rule activation is asynchronous, since `ruleStatus` has `Activating` and `ActivationFailed` states. Deploying both directories in one transaction may well work; deploying matching rules first cannot fail for ordering reasons.

## Bypassing the rule from Apex

For an `Allow` + `Alert` rule, Apex opts out per DML call. Straight from the Apex Reference Guide's `DMLOptions.DuplicateRuleHeader` example:

```apex
Database.DMLOptions dml = new Database.DMLOptions();
dml.DuplicateRuleHeader.allowSave = true;
dml.DuplicateRuleHeader.runAsCurrentUser = true;

Account duplicateAccount = new Account(Name = 'dupe');
Database.SaveResult sr = Database.insert(duplicateAccount, dml);
if (sr.isSuccess()) {
    System.debug('Duplicate account has been inserted in Salesforce!');
}
```

- `allowSave = true` means "the user should be allowed to save the duplicate". The guide scopes it precisely: "For a duplicate rule, **when the Alert option is enabled**, bypass alerts and save duplicate records." It is not a master switch over a `Block` rule.
- `runAsCurrentUser = true` runs the duplicate rules as the current user "which ensures users can't view duplicate records that aren't available to them", and the guide recommends it specifically "to detect duplicates when converting leads to contacts".
- `DMLOptions` "take effect only for record operations performed using Apex DML and not through the Salesforce user interface" — the same class touched by a Lightning action still sees the rule.

To read what the rule found instead of blindly bypassing it, downcast the error:

```apex
Database.SaveResult sr = Database.insert(newContact, false);
if (!sr.isSuccess()) {
    for (Database.Error err : sr.getErrors()) {
        if (err instanceof Database.DuplicateError) {
            Datacloud.DuplicateResult dr =
                ((Database.DuplicateError) err).getDuplicateResult();
            System.debug('Rule: ' + dr.getDuplicateRule());
            System.debug('Message: ' + dr.getErrorMessage());
            System.debug('Allows save: ' + dr.isAllowSave());
            for (Datacloud.MatchResult mr : dr.getMatchResults()) {
                for (Datacloud.MatchRecord rec : mr.getMatchRecords()) {
                    System.debug('Existing: ' + rec.getRecord().Id);
                }
            }
        }
    }
}
```

`getDuplicateRule()` returns the developer name of the rule that fired, `getErrorMessage()` returns the `alertText` an admin configured, and `isAllowSave()` says whether this rule would let the record through — which is how integration code decides between retrying with `allowSave` and routing to a steward.

## Checking for duplicates before you insert

`Datacloud.FindDuplicates` runs the org's active duplicate rules against in-memory sObjects that have not been saved, so a screen or an integration can offer a choice instead of an error:

```apex
Contact candidate = new Contact(
    FirstName = 'Jane', LastName = 'Roe', Email = 'jane.roe@example.com');

List<Datacloud.FindDuplicatesResult> results =
    Datacloud.FindDuplicates.findDuplicates(new List<Contact>{ candidate });

for (Datacloud.DuplicateResult dupResult : results[0].getDuplicateResults()) {
    for (Datacloud.MatchResult matchResult : dupResult.getMatchResults()) {
        if (matchResult.isSuccess() && !matchResult.getMatchRecords().isEmpty()) {
            System.debug('Matched by rule: ' + matchResult.getRule());
            for (Datacloud.MatchRecord m : matchResult.getMatchRecords()) {
                System.debug('Existing record: ' + m.getRecord());
            }
        }
    }
}
```

Constraints the guide states outright, all of which are easy to hit in a batch:

- Every sObject in the input must be the same type, and "the input array is limited to 50 elements", otherwise: `Configuration error: The number of records to check is greater than the permitted batch size.`
- With no active duplicate rule for the type, it throws `System.HandledException`: "No active duplicate rules are defined for the {ObjectName} object type."
- "This method doesn't return custom fields by default" and "standard matching rules don't include custom fields in their matching criteria" — matching on a custom identity field requires a custom matching rule assigned to a duplicate rule.
- `Datacloud.FindDuplicatesByIds.findDuplicatesByIds(List<Id>)` is the saved-record equivalent, useful for a scheduled sweep over records created while a rule was inactive.

## Verification

After deploying, confirm the configuration from data rather than from Setup screenshots.

```sql
-- 1. Are the rules actually there and active, and on which object?
SELECT Id, DeveloperName, MasterLabel, IsActive, SobjectType, SobjectSubtype
FROM DuplicateRule
ORDER BY SobjectType, DeveloperName
```

```sql
-- 2. Did the matching rules reach Active, or stall in Activating / ActivationFailed?
SELECT Id, DeveloperName, MasterLabel, SobjectType, RuleStatus, MatchEngine
FROM MatchingRule
WHERE SobjectType IN ('Contact', 'Lead')
```

```sql
-- 3. Is the Report action producing anything? Empty means the rule never fired.
SELECT Id, Name, RecordCount, DuplicateRuleId, CreatedDate
FROM DuplicateRecordSet
WHERE CreatedDate = LAST_N_DAYS:7
ORDER BY CreatedDate DESC
```

```sql
-- 4. Which concrete records were grouped, so a steward can work the queue.
SELECT Id, Name, RecordId, DuplicateRecordSetId
FROM DuplicateRecordItem
WHERE DuplicateRecordSetId = '0AF...'
```

- `DuplicateRule` and `MatchingRule` are queryable but not writable: their supported calls are `describeSObjects()`, `describeLayout()`, `query()`, `retrieve()`, `search()`. The Object Reference adds "To create, edit, or delete duplicate rules, use the UI" — the Metadata API types above are the deployment path, the SOQL is verification only.
- Since Summer '20, "only users with the View Setup and Configuration permission can access" `DuplicateRule`, `MatchingRule`, and `MatchingRuleItem`, and `DeveloperName` additionally needs View DeveloperName or View Setup and Configuration. A steward-facing report cannot use these objects without that permission.
- `DuplicateRecordSet` and `DuplicateRecordItem` are different: they support `create()`, `update()`, `delete()` and `undelete()`, are reachable by any Sales Cloud or CRM user the admin grants access to, and exist "to create custom report types for duplicates". `DuplicateRecordItem.RecordId` is polymorphic and refers to Account, Contact, Individual, or Lead.
- Setup check: a matching rule that stalls does so visibly — `RuleStatus` sits on `Activating` or `ActivationFailed` rather than `Active`, and no duplicate rule that references it will detect anything.
