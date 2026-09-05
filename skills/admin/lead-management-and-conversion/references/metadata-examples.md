# Metadata Examples — Lead Management and Conversion

Deployable shapes for the metadata that carries lead conversion. Element names, enum values, and the
skeletons come from the Metadata API Developer Guide (v62 PDF: `LeadConvertSettings`,
`LeadConfigSettings`, `StandardValueSet`, `BusinessProcess`, `DuplicateRule`, `Settings` sections) and
the Apex Developer / Reference Guides (`Database.LeadConvert`, `Database.convertLead`). The worked
examples extend the guides' own sample definitions to a realistic org. Validate with:

```bash
python3 skills/admin/lead-management-and-conversion/scripts/check_lead_management_and_conversion.py \
  --manifest-dir force-app/main/default
```

## Where the files live

| What | package.xml `<name>` / `<members>` | File in a DX project | API |
|---|---|---|---|
| Conversion field mappings | `Settings` / `LeadConvert` | `settings/LeadConvert.settings-meta.xml` | 39.0+ |
| Lead behaviour switches | `Settings` / `LeadConfig` | `settings/LeadConfig.settings-meta.xml` | 47.0+ |
| Lead Status values (+ converted flag) | `StandardValueSet` / `LeadStatus` | `standardValueSets/LeadStatus.standardValueSet-meta.xml` | 38.0+ |
| Lead Source values | `StandardValueSet` / `LeadSource` | `standardValueSets/LeadSource.standardValueSet-meta.xml` | 38.0+ |
| Lead process (status subset per record type) | `BusinessProcess` / `Lead.<Name>` | inside `objects/Lead/Lead.object-meta.xml` | 17.0+ |
| Custom Lead / target fields | `CustomField` / `Lead.Foo__c` | `objects/Lead/fields/Foo__c.field-meta.xml` | — |
| Lead duplicate rule | `DuplicateRule` / `Lead.<Name>` | `duplicateRules/Lead.<Name>.duplicateRule-meta.xml` | 66.0+ |

How to read the table:

- Settings members use the type name **without** the `Settings` suffix — `LeadConvertSettings`
  becomes `<members>LeadConvert</members>` (api_meta.txt L108366–108369). The `*` wildcard applies
  only when retrieving *all* settings, never an individual one (api_meta.txt L121264–121268).
- The `LeadConvertSettings` section of the guide states the suffix is `LeadConvertSetting` in a
  `LeadConvertSettings` folder (api_meta.txt L121132–121134), while the `Settings` section states
  every settings component is one file in the `settings` directory named `<feature>.settings`
  (api_meta.txt L108377–108380). Source-format retrieves produce the `settings/` form; the checker
  accepts either path.
- `LeadStatus` is the standard value set behind `Lead.Status`; `LeadSource` is shared by
  `Account.AccountSource`, `CampaignMember.LeadSource`, `Contact.LeadSource`, `Lead.LeadSource`,
  and `Opportunity.LeadSource` — one edit hits five fields (api_meta.txt L142575–142581).
- `BusinessProcess.fullName` is object-qualified in package.xml (`Lead.Inbound_SDR_Process`) but bare
  inside the object file (api_meta.txt L42984–42997).

---

## 1. Conversion field mappings — `settings/LeadConvert.settings-meta.xml`

Up to three `objectMapping` blocks, one each for Account, Contact, Opportunity. `inputObject` is
always `Lead` (api_meta.txt L121178–121205).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LeadConvertSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <!-- Show the Record Owner picker in the Convert Lead dialog -->
    <allowOwnerChange>true</allowOwnerChange>

    <objectMapping>
        <inputObject>Lead</inputObject>
        <mappingFields>
            <inputField>Annual_Contract_Value__c</inputField>
            <outputField>Estimated_ACV__c</outputField>
        </mappingFields>
        <mappingFields>
            <inputField>Employee_Band__c</inputField>
            <outputField>Employee_Band__c</outputField>
        </mappingFields>
        <outputObject>Account</outputObject>
    </objectMapping>

    <objectMapping>
        <inputObject>Lead</inputObject>
        <mappingFields>
            <inputField>Demo_Requested__c</inputField>
            <outputField>Demo_Requested__c</outputField>
        </mappingFields>
        <mappingFields>
            <inputField>Lead_Score__c</inputField>
            <outputField>Lead_Score_at_Conversion__c</outputField>
        </mappingFields>
        <mappingFields>
            <inputField>Consent_Marketing__c</inputField>
            <outputField>Consent_Marketing__c</outputField>
        </mappingFields>
        <outputObject>Contact</outputObject>
    </objectMapping>

    <objectMapping>
        <inputObject>Lead</inputObject>
        <mappingFields>
            <inputField>Lead_Score__c</inputField>
            <outputField>Lead_Score_at_Conversion__c</outputField>
        </mappingFields>
        <mappingFields>
            <inputField>Product_Interest__c</inputField>
            <outputField>Primary_Product_Interest__c</outputField>
        </mappingFields>
        <outputObject>Opportunity</outputObject>
    </objectMapping>

    <!-- VisibleOptional (default) | VisibleRequired | NotVisible -->
    <opportunityCreationOptions>VisibleOptional</opportunityCreationOptions>
</LeadConvertSettings>
```

How to read it:

- `mappingFields` carries **custom** fields only. Standard Lead fields are mapped by the platform and
  do not appear here ("The system automatically maps standard lead fields to standard account,
  contact, and opportunity fields", apexdev.txt L8350–8353).
- The same `inputField` may appear once per `objectMapping` — `Lead_Score__c` above feeds both
  Contact and Opportunity.
- `opportunityCreationOptions` values are exactly `VisibleOptional`, `VisibleRequired`, `NotVisible`
  (api_meta.txt L121164–121174). `NotVisible` means no opportunity is ever created from the dialog.
- The file is a full replace. A deploy that omits an `objectMapping` block removes those mappings
  from the org.

---

## 2. Lead behaviour switches — `settings/LeadConfig.settings-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LeadConfigSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <doesEnableLeadConvertDefaultSubjectBlankTaskCreation>false</doesEnableLeadConvertDefaultSubjectBlankTaskCreation>
    <doesHideOpportunityInConvertLeadWindow>false</doesHideOpportunityInConvertLeadWindow>
    <!-- Keep the rep's chosen status instead of the new owner's record-type default -->
    <doesPreserveLeadStatus>true</doesPreserveLeadStatus>
    <doesSelectNoOpportunityOnConvertLead>false</doesSelectNoOpportunityOnConvertLead>
    <doesTrackHistory>true</doesTrackHistory>
    <enableConversionsOnMobile>true</enableConversionsOnMobile>
    <enableOrgWideMergeAndDelete>false</enableOrgWideMergeAndDelete>
    <shouldLeadConvertRequireValidation>true</shouldLeadConvertRequireValidation>
    <shouldSendNotificationEmailWhenLeadOwnerUpdatesViaApexInLEX>false</shouldSendNotificationEmailWhenLeadOwnerUpdatesViaApexInLEX>
</LeadConfigSettings>
```

How to read it (all field semantics from api_meta.txt L121026–121080):

- `shouldLeadConvertRequireValidation` is the metadata behind **Require Validation for Converted
  Leads**. Deploying `true` starts enforcing validation rules on the conversion path — regression-test
  in a sandbox first (`gotchas.md` Gotcha 6).
- `doesPreserveLeadStatus` defaults to `true`. Set it to `false` only if you *want* the status to be
  replaced by the new owner's record-type default during conversion.
- `doesSelectNoOpportunityOnConvertLead` (`true` = never create an opportunity) overlaps with
  `opportunityCreationOptions` = `NotVisible` in §1. Pick one; setting both is redundant and makes the
  next admin guess which one is load-bearing.
- `relateEmailsToContactOnConvert` (default `false`) associates the lead's emails with the resulting
  contact. It is documented in the field table but omitted from the guide's own sample; add it
  explicitly when you want it rather than relying on the default.

---

## 3. Lead Status values — `standardValueSets/LeadStatus.standardValueSet-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<StandardValueSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <sorted>false</sorted>
    <standardValue>
        <fullName>Open - Not Contacted</fullName>
        <default>true</default>
        <label>Open - Not Contacted</label>
        <converted>false</converted>
        <isActive>true</isActive>
    </standardValue>
    <standardValue>
        <fullName>Working - Contacted</fullName>
        <default>false</default>
        <label>Working - Contacted</label>
        <converted>false</converted>
        <isActive>true</isActive>
    </standardValue>
    <standardValue>
        <fullName>Nurture</fullName>
        <default>false</default>
        <label>Nurture</label>
        <converted>false</converted>
        <isActive>true</isActive>
    </standardValue>
    <!-- Converted statuses. More than one value may carry converted=true. -->
    <standardValue>
        <fullName>Closed - Converted</fullName>
        <default>false</default>
        <label>Closed - Converted</label>
        <converted>true</converted>
        <isActive>true</isActive>
    </standardValue>
    <standardValue>
        <fullName>Closed - Converted (Partner Sourced)</fullName>
        <default>false</default>
        <label>Closed - Converted (Partner Sourced)</label>
        <converted>true</converted>
        <isActive>true</isActive>
    </standardValue>
    <standardValue>
        <fullName>Closed - Not Converted</fullName>
        <default>false</default>
        <label>Closed - Not Converted</label>
        <converted>false</converted>
        <isActive>true</isActive>
    </standardValue>
</StandardValueSet>
```

How to read it:

- `converted` is documented as relevant **only** to the standard Lead Status field
  (api_meta.txt L47547–47555). `LeadStatus.IsConverted` in the Object Reference is explicit that
  "Multiple lead status values can represent a converted lead" (object_reference.txt L166081–166087),
  so two converted statuses is a supported design, not a misconfiguration.
- **Omission deactivates.** "If picklist values are missing from a component definition, they get
  deactivated when deployed. Deactivation occurs for picklist values of both standard and custom
  fields" (api_meta.txt L47481–47484). Always retrieve, edit, redeploy — never author this file from
  scratch.
- A deployed `StandardValueSet` must contain at least one value or the deploy errors
  (api_meta.txt L130771–130774).
- Values loaded through the Metadata API are **not** added to record types automatically: "go to the
  Record Types list for the object containing the picklist field, click Edit, and add the new value to
  the Selected Fields list" (api_meta.txt L130776–130781). See §4.

---

## 4. Lead process — `objects/Lead/Lead.object-meta.xml`

A lead process is a `BusinessProcess` on the Lead object; the record type points at it. Shape from the
guide's own lead-process sample (api_meta.txt L43015–43050).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <businessProcesses>
        <fullName>Inbound_SDR_Process</fullName>
        <description>Status subset worked by the inbound SDR team</description>
        <isActive>true</isActive>
        <values>
            <fullName>Open - Not Contacted</fullName>
            <default>true</default>
        </values>
        <values>
            <fullName>Working - Contacted</fullName>
            <default>false</default>
        </values>
        <values>
            <fullName>Nurture</fullName>
            <default>false</default>
        </values>
        <!-- Without a converted value in the subset, this record type cannot finish a conversion -->
        <values>
            <fullName>Closed - Converted</fullName>
            <default>false</default>
        </values>
        <values>
            <fullName>Closed - Not Converted</fullName>
            <default>false</default>
        </values>
    </businessProcesses>
</CustomObject>
```

How to read it:

- The subset must include at least one value whose `converted` flag is `true` in §3, or users on that
  record type have no status to finish the conversion with.
- Business processes are **not** an access-control mechanism: "a user assigned to a profile that isn't
  enabled for a particular business process can't create or edit it, but they can read the business
  process record… Don't store sensitive information in the business process description, name, or
  picklist values" (api_meta.txt L42961–42966).

---

## 5. Excluding the Web-to-Lead user from a Block duplicate rule

`DuplicateRuleFilter` is the supported way to say "only apply this rule when…". The guide's own sample
filters on `<table>User</table>` / `<field>Username</field>`
(api_meta.txt L56090–56100), which is how a system-context insert is exempted.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<DuplicateRule xmlns="http://soap.sforce.com/2006/04/metadata"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <actionOnInsert>Allow</actionOnInsert>
    <actionOnUpdate>Allow</actionOnUpdate>
    <alertText>A matching lead or contact already exists. Review before saving.</alertText>
    <description>Block reps from creating obvious lead duplicates; let Web-to-Lead through.</description>
    <duplicateRuleFilter>
        <booleanFilter xsi:nil="true"/>
        <duplicateRuleFilterItems>
            <field>Username</field>
            <operation>notEqual</operation>
            <value>webtolead@example.com</value>
            <sortOrder>1</sortOrder>
            <table>User</table>
        </duplicateRuleFilterItems>
    </duplicateRuleFilter>
    <duplicateRuleMatchRules>
        <matchRuleSObjectType>Lead</matchRuleSObjectType>
        <matchingRule>Standard_Lead_Match_Rule</matchingRule>
        <objectMapping>
            <inputObject>Lead</inputObject>
            <mappingFields>
                <inputField>Email</inputField>
                <outputField>Email</outputField>
            </mappingFields>
            <outputObject>Lead</outputObject>
        </objectMapping>
    </duplicateRuleMatchRules>
    <isActive>true</isActive>
    <masterLabel>Lead_Dupe_Rep_Entry_Only</masterLabel>
    <operationsOnInsert>alert</operationsOnInsert>
    <operationsOnInsert>report</operationsOnInsert>
    <operationsOnUpdate>alert</operationsOnUpdate>
    <operationsOnUpdate>report</operationsOnUpdate>
    <securityOption>EnforceSharingRules</securityOption>
    <sortOrder>1</sortOrder>
</DuplicateRule>
```

How to read it:

- "Salesforce only applies the DuplicateRule if the record matches the criteria"
  (api_meta.txt L55978–55979) — a `User`-table filter item is a rule *scope*, not a permission.
- `securityOption` is **not** a user exemption. It decides whether sharing on the *matched existing
  record* is honoured: `EnforceSharingRules` lets the insert proceed silently when the running user
  can't see the match; `BypassSharingRules` ignores sharing (api_meta.txt L55943–55959).
- `alertText` may only be set when `actionOnInsert` or `actionOnUpdate` is `Allow`; setting it
  alongside `Block` is a validation error on deploy (api_meta.txt L55906–55912).
- Full matching/duplicate rule design belongs to `admin/duplicate-management` — this block is only the
  Web-to-Lead exemption.

---

## 6. Bulk conversion from Apex — `classes/LeadConversionService.cls`

Chunked, partial-success, queue-aware. Built from the `Database.LeadConvert` /
`Database.convertLead(List, allOrNone)` contract (apexrefguide.txt L148861–149467, L205811–205846).

```apex
public with sharing class LeadConversionService {

    // "We recommend passing a maximum of 100 LeadConvert objects to the convertLead method."
    // apexrefguide.txt L205831-205833
    @TestVisible private static final Integer CHUNK_SIZE = 100;

    public class ConversionOutcome {
        public Id leadId;
        public Id accountId;
        public Id contactId;
        public Id opportunityId;
        public Boolean success;
        public String error;
    }

    /**
     * @param leadIds        Leads to convert. Must not already be converted.
     * @param newOwnerId     Required when the lead is owned by a queue — accounts and contacts
     *                       cannot be owned by a queue (apexdev.txt L8332-8334). Pass null to keep
     *                       the lead owner.
     * @param createOpps     false suppresses opportunity creation.
     */
    public static List<ConversionOutcome> convert(Set<Id> leadIds, Id newOwnerId, Boolean createOpps) {
        // Step 5 of the documented flow: query the converted status, never hardcode the label.
        List<LeadStatus> convertedStatuses = [
            SELECT ApiName FROM LeadStatus WHERE IsConverted = true ORDER BY SortOrder ASC LIMIT 1
        ];
        if (convertedStatuses.isEmpty()) {
            throw new ConversionException('No Lead Status value has converted = true.');
        }
        String convertedStatus = convertedStatuses[0].ApiName;

        List<Database.LeadConvert> requests = new List<Database.LeadConvert>();
        for (Id leadId : leadIds) {
            Database.LeadConvert lc = new Database.LeadConvert();
            lc.setLeadId(leadId);
            lc.setConvertedStatus(convertedStatus);
            lc.setDoNotCreateOpportunity(createOpps == false);
            if (newOwnerId != null) {
                lc.setOwnerId(newOwnerId);
            }
            // Left at the default (false) deliberately: sending owner mail from a bulk job
            // floods inboxes. lc.setSendNotificationEmail(true) opts in per run.
            requests.add(lc);
        }

        List<ConversionOutcome> outcomes = new List<ConversionOutcome>();
        for (Integer offset = 0; offset < requests.size(); offset += CHUNK_SIZE) {
            Integer end = Math.min(offset + CHUNK_SIZE, requests.size());
            List<Database.LeadConvert> chunk = new List<Database.LeadConvert>();
            for (Integer i = offset; i < end; i++) {
                chunk.add(requests[i]);
            }

            // Each convertLead call consumes one of the 150 DML statements per transaction
            // (salesforce_app_limits_cheatsheet.txt L64, L140-142).
            // allOrNone = false: one bad lead must not roll back the batch.
            List<Database.LeadConvertResult> results = Database.convertLead(chunk, false);

            for (Integer i = 0; i < results.size(); i++) {
                Database.LeadConvertResult r = results[i];
                ConversionOutcome o = new ConversionOutcome();
                o.leadId = chunk[i].getLeadId();
                o.success = r.isSuccess();
                if (r.isSuccess()) {
                    o.accountId = r.getAccountId();
                    o.contactId = r.getContactId();
                    o.opportunityId = r.getOpportunityId();
                } else {
                    o.error = r.getErrors()[0].getMessage();
                }
                outcomes.add(o);
            }
        }
        return outcomes;
    }

    public class ConversionException extends Exception {}
}
```

How to read it:

- `setConvertedStatus` and `setLeadId` are the only two required setters
  (apexrefguide.txt L148983–148990). Everything else has a documented default.
- `setDoNotCreateOpportunity(true)` **suppresses** the opportunity; the default is `false`, meaning
  opportunities are created (apexrefguide.txt L148985–148987). The double negative is the single most
  common inversion bug in generated conversion code.
- `convertLead` exists only as a `Database` class method, never as a DML statement
  (apexdev.txt L7589).
- `getErrors()` is only populated when `allOrNone` is `false`; with `true` a failure throws instead
  (apexrefguide.txt L205825–205830).
- Person accounts: do **not** call `setContactId` — "if you are converting a lead into a person
  account, do not specify setContactId or an error will result. Specify only setAccountId of the
  person account" (apexrefguide.txt L149263–149264).

### Flow-free invocable wrapper

Shape follows the guide's own `ConvertLeadAction` sample (apexdev.txt L5494–5580), reduced to the
inputs an admin-built Flow actually needs.

```apex
public with sharing class ConvertLeadInvocable {

    public class Request {
        @InvocableVariable(required=true label='Lead ID')
        public Id leadId;
        @InvocableVariable(label='New Owner ID (required for queue-owned leads)')
        public Id ownerId;
        @InvocableVariable(label='Create Opportunity')
        public Boolean createOpportunity;
    }

    public class Result {
        @InvocableVariable public Id accountId;
        @InvocableVariable public Id contactId;
        @InvocableVariable public Id opportunityId;
        @InvocableVariable public Boolean success;
        @InvocableVariable public String errorMessage;
    }

    @InvocableMethod(label='Convert Leads' category='Lead')
    public static List<Result> convertLeads(List<Request> requests) {
        // One convertLead call per chunk, not one per request: the invocable receives the whole
        // Flow batch and must not loop DML.
        Map<Id, Request> byLeadId = new Map<Id, Request>();
        for (Request r : requests) {
            byLeadId.put(r.leadId, r);
        }

        Boolean createOpps = requests.isEmpty() || requests[0].createOpportunity != false;
        Id ownerId = requests.isEmpty() ? null : requests[0].ownerId;

        Map<Id, LeadConversionService.ConversionOutcome> outcomeByLead =
            new Map<Id, LeadConversionService.ConversionOutcome>();
        for (LeadConversionService.ConversionOutcome o
                : LeadConversionService.convert(byLeadId.keySet(), ownerId, createOpps)) {
            outcomeByLead.put(o.leadId, o);
        }

        List<Result> results = new List<Result>();
        for (Request r : requests) {
            LeadConversionService.ConversionOutcome o = outcomeByLead.get(r.leadId);
            Result res = new Result();
            res.success = o != null && o.success;
            if (o != null) {
                res.accountId = o.accountId;
                res.contactId = o.contactId;
                res.opportunityId = o.opportunityId;
                res.errorMessage = o.error;
            }
            results.add(res);
        }
        return results;
    }
}
```

How to read it: an `@InvocableMethod` receives the *whole* Flow batch as a `List`, so the DML must
happen once outside the loop. The guide's sample loops `convertLead` per request
(apexdev.txt L5498–5502), which is fine for a one-record demo and burns one DML statement per lead in
a bulk Flow — 151 leads is a `LimitException`.

---

## 7. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>LeadConvert</members>
        <members>LeadConfig</members>
        <name>Settings</name>
    </types>
    <types>
        <members>LeadStatus</members>
        <members>LeadSource</members>
        <name>StandardValueSet</name>
    </types>
    <types>
        <members>Lead.Inbound_SDR_Process</members>
        <name>BusinessProcess</name>
    </types>
    <types>
        <members>Lead.Inbound_SDR</members>
        <name>RecordType</name>
    </types>
    <types>
        <members>Lead.Lead_Score__c</members>
        <members>Contact.Lead_Score_at_Conversion__c</members>
        <members>Opportunity.Lead_Score_at_Conversion__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Lead</members>
        <name>AssignmentRules</name>
    </types>
    <types>
        <members>Lead</members>
        <name>AutoResponseRules</name>
    </types>
    <version>62.0</version>
</Package>
```

Deploy order matters inside a single manifest: the target `CustomField` entries must exist before
`LeadConvert` settings can reference them, and the `StandardValueSet` value must exist before the
`BusinessProcess` subset lists it. Both are satisfied by deploying this manifest as one unit — split
it and the halves fail in isolation.

---

## 8. Retrieve, deploy, verify

```bash
# Retrieve current state before editing anything — StandardValueSet deploys deactivate omitted values
sf project retrieve start \
  --metadata "Settings:LeadConvert" \
  --metadata "Settings:LeadConfig" \
  --metadata "StandardValueSet:LeadStatus" \
  --metadata "CustomObject:Lead" \
  --target-org sandbox

# Validate only (no changes committed) against the sandbox
sf project deploy validate --manifest manifest/package.xml --target-org sandbox

# Deploy
sf project deploy start --manifest manifest/package.xml --target-org sandbox
```

### Verification step

Run in the target org after deploy. Each query answers one question the deploy could have broken.

```sql
-- 1. At least one converted status exists and is reachable
SELECT ApiName, MasterLabel, IsConverted, IsDefault, SortOrder
FROM LeadStatus
ORDER BY SortOrder

-- 2. Conversions are actually landing (should be non-zero after a test conversion)
SELECT COUNT(Id), Status
FROM Lead
WHERE IsConverted = true AND ConvertedDate = LAST_N_DAYS:7
GROUP BY Status

-- 3. Mapped data survived: every recent conversion should carry the score forward
SELECT Id, Company, Lead_Score__c, ConvertedDate,
       ConvertedContactId, ConvertedContact.Lead_Score_at_Conversion__c,
       ConvertedOpportunityId, ConvertedOpportunity.Lead_Score_at_Conversion__c
FROM Lead
WHERE IsConverted = true
  AND ConvertedDate = LAST_N_DAYS:7
  AND Lead_Score__c != NULL
ORDER BY ConvertedDate DESC
LIMIT 50
```

Query 3 is the real gate: a row where `Lead_Score__c` is populated but
`ConvertedContact.Lead_Score_at_Conversion__c` is null is a mapping that did not take. Setup check for
the same thing without SOQL: **Object Manager > Lead > Fields & Relationships > Map Lead Fields**, and
confirm each custom field lists the target you deployed.

The Lead's converted-state fields — `IsConverted`, `ConvertedAccountId`, `ConvertedContactId`,
`ConvertedOpportunityId`, `ConvertedDate`, `Status` — are all filterable and queryable after
conversion (object_reference.txt L163919–163930), which is why the converted Lead remains the audit
record for anything the mapping dropped.
