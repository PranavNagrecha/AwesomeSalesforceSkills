# LLM Anti-Patterns — FHIR Data Mapping

Common mistakes AI coding assistants make when generating or advising on FHIR data mapping in Salesforce Health Cloud. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Writing FHIR Patient Demographics Directly to Account or Contact Fields

**What the LLM generates:**

```apex
Account patientAccount = new Account(
    RecordTypeId = personAccountRtId,
    FirstName = fhirPatient.name[0].given[0],
    LastName = fhirPatient.name[0].family,
    Phone = fhirPatient.telecom[0].value,
    BillingStreet = fhirPatient.address[0].line[0]
);
insert patientAccount;
```

**Why it happens:** LLMs trained on general Salesforce content know that Person Account has FirstName, LastName, and Phone fields and reasonably assume those are the mapping targets. The Health Cloud child-record model (PersonName, ContactPointPhone, ContactPointAddress) is a platform-specific pattern that is underrepresented in general training data.

**Correct pattern:**

```apex
// 1. Insert Person Account (no demographic fields)
Account patientAccount = new Account(RecordTypeId = personAccountRtId);
insert patientAccount;

// 2. Insert child PersonName
PersonName pn = new PersonName(
    ParentId = patientAccount.Id,
    GivenName = fhirGivenName,
    FamilyName = fhirFamilyName,
    NameUse = 'Official'
);
insert pn;

// 3. Insert child ContactPointPhone
ContactPointPhone cpp = new ContactPointPhone(
    ParentId = patientAccount.Id,
    TelephoneNumber = fhirPhone,
    AddressType = 'Home'
);
insert cpp;
```

**Detection hint:** Flag any code that sets `Account.FirstName`, `Account.LastName`, `Account.Phone`, `Account.BillingStreet`, or equivalent Contact demographic fields when the context is a FHIR Patient mapping task.

---

## Anti-Pattern 2: Treating condition.code as Optional When Inserting HealthCondition

**What the LLM generates:**

```apex
HealthCondition hc = new HealthCondition(
    Name = fhirCondition.text.div,
    PatientId = accountId,
    // Code omitted because FHIR spec says 0..1
);
insert hc;
```

**Why it happens:** The LLM reads the FHIR R4 specification, sees `Condition.code` marked as 0..1 (optional), and faithfully reflects that optionality in the generated code. It does not know that Health Cloud imposes a stricter cardinality requirement on HealthCondition.Code than the FHIR spec mandates.

**Correct pattern:**

```
// Pre-load: reject or quarantine Conditions without a code
if (fhirCondition.code == null || fhirCondition.code.coding.isEmpty()) {
    quarantineLog.add(fhirCondition.id);
    return; // Do not insert
}

// Only insert when a code is present
HealthCondition hc = new HealthCondition(
    Name = fhirCondition.text?.div,
    PatientId = accountId,
    Code = resolvedCodeSetBundleId  // Required
);
insert hc;
```

**Detection hint:** Look for HealthCondition insert/upsert statements where `Code` is not set. Any such statement is a likely failure at runtime.

---

## Anti-Pattern 3: Creating a Custom careTeam Object or Field on CarePlan

**What the LLM generates:**

```
// LLM suggests creating a custom junction object
CarePlan__CareTeamMember__c ctm = new CarePlan__CareTeamMember__c(
    CarePlan__c = carePlanId,
    Practitioner__c = userId
);
insert ctm;
```

Or alternatively, the LLM looks for a `CareTeamId` lookup field on CarePlan and suggests querying it.

**Why it happens:** The FHIR CarePlan resource has a `careTeam` array. LLMs assume this maps to a direct relationship on the CarePlan SObject. When they do not find a standard field, they propose a custom object or a hallucinated standard field.

**Correct pattern:**

```apex
// Resolve careTeam members to Case Team members on the parent Case
CaseTeamMember ctm = new CaseTeamMember(
    ParentId = parentCaseId,        // The Case related to the CarePlan
    MemberId = practitionerUserId,  // Salesforce User Id of the practitioner
    TeamRoleId = careTeamRoleId     // Case Team Role record Id
);
insert ctm;
```

**Detection hint:** Flag any custom SObject named with `CareTeam`, any `CareTeamId` field reference on CarePlan, or any junction table created to link CarePlan to team members. The correct target is `CaseTeamMember` on the parent Case.

---

## Anti-Pattern 4: Loading CodeSetBundle Without Enforcing the 15-Coding Limit

**What the LLM generates:**

```python
# LLM iterates all codings and tries to set CodeSet16Id, CodeSet17Id, etc.
for i, coding in enumerate(fhir_codings, start=1):
    codeset_bundle[f"CodeSet{i}Id"] = lookup_codeset(coding)
# Results in KeyError or DML failure when i > 15
```

**Why it happens:** LLMs do not have reliable knowledge of the specific 15-field limit on CodeSetBundle. They see the pattern of indexed fields (CodeSet1Id–CodeSet15Id) and assume the series continues or is dynamically extensible.

**Correct pattern:**

```python
MAX_CODESETS = 15

retained = prioritize_codings(fhir_codings)[:MAX_CODESETS]
discarded = prioritize_codings(fhir_codings)[MAX_CODESETS:]

audit_discard(discarded, resource_id)  # Required for clinical governance

codeset_bundle = {}
for i, coding in enumerate(retained, start=1):
    codeset_bundle[f"CodeSet{i}Id"] = lookup_or_create_codeset(coding)
```

**Detection hint:** Look for any loop that dynamically constructs `CodeSet{n}Id` keys without a hard cap at 15, or any comment/code that implies more than 15 CodeSet references are being written to a single CodeSetBundle.

---

## Anti-Pattern 5: Skipping the FHIR R4 Support Settings Activation Step

**What the LLM generates:**

```
// LLM assumes the org is ready and jumps straight to querying clinical objects
List<HealthCondition> conditions = [SELECT Id, Code FROM HealthCondition];
```

Or the LLM generates a migration plan that starts with data transformation without mentioning the org prerequisite.

**Why it happens:** LLMs default to assuming an org is in a standard, fully-configured state. The FHIR-Aligned Clinical Data Model org preference is a prerequisite that is specific to Health Cloud and not commonly represented in general Salesforce training material. LLMs omit it because they are not aware it exists.

**Correct pattern:**

```
Step 0 (before any data or schema work):
  Navigate to Setup > FHIR R4 Support Settings.
  Enable "FHIR-Aligned Clinical Data Model."
  Confirm HealthCondition, CareObservation, PersonName, ContactPointPhone,
  ContactPointAddress objects are now visible in Schema Builder or Object Manager.

Only then proceed to Step 1: design the field mapping.
```

**Detection hint:** Any FHIR-to-Health-Cloud migration plan, runbook, or integration design that does not include a step to enable or verify the FHIR R4 Support Settings org preference is incomplete. Flag it and add the prerequisite step.
