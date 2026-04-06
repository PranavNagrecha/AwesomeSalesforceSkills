# Gotchas — Lead Conversion Customization

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: LeadConvertResult Cannot Be Instantiated in Test Code

**What happens:** Attempting to construct `new Database.LeadConvertResult()` in a test class causes a compile error: "Constructor not defined." Test authors who try to mock conversion results this way cannot compile their test class at all.

**When it occurs:** Any time a developer tries to unit test a method that accepts or returns `Database.LeadConvertResult` and wants to mock the result without performing a real DML conversion.

**How to avoid:** Two approaches work. The simpler approach is to call `Database.convertLead()` in the test itself with a real test Lead record — the platform returns a legitimate `LeadConvertResult` instance from the invocation. If a mock result is truly needed (for a method that only processes results), deserialize it from a JSON string:

```apex
Database.LeadConvertResult mockResult = (Database.LeadConvertResult)
    JSON.deserialize(
        '{"success":true,"leadId":"' + testLeadId + '",' +
        '"contactId":"' + testContactId + '",' +
        '"accountId":"' + testAccountId + '"}',
        Database.LeadConvertResult.class
    );
```

---

## Gotcha 2: ConvertedContactId Is Null in before update — Only Available in after update

**What happens:** A trigger developer adds lead conversion logic to the `before update` handler to read `ConvertedContactId`. The field is always null at that point, so related record creation or field mapping silently fails with no error.

**When it occurs:** Any `before update` trigger context fires before the conversion engine has finished writing the Contact, Account, and Opportunity records. The `ConvertedContactId`, `ConvertedAccountId`, and `ConvertedOpportunityId` fields are populated on the Lead record only after the conversion DML commits — which is visible in `after update`.

**How to avoid:** Always detect the conversion event (`l.IsConverted && !oldMap.get(l.Id).IsConverted`) and perform the related-record work exclusively in the `after update` context. A re-query inside `after update` is also necessary because `Trigger.new` does not include `ConvertedContactId` even in `after update`.

---

## Gotcha 3: Unmapped Custom Fields Drop Silently With No Warning

**What happens:** A custom Lead field has no mapping configured in Setup (Object Manager > Lead > Map Lead Fields). When conversion runs — from the UI, Apex, API, or Flow — the field value disappears from the converted records. Salesforce does not raise an error or warning. The original Lead record retains the value, but the Contact, Account, and Opportunity do not receive it.

**When it occurs:** Any conversion of a Lead that has populated custom fields without corresponding field mappings. Commonly discovered weeks or months after go-live when sales reps notice blank fields on Contacts that were expected to have values.

**How to avoid:** After calling `Database.convertLead()`, explicitly query the unmapped fields on the source Lead records and perform a follow-up DML update on the resulting Contact or Account. This is also the reason the trigger-based post-conversion pattern re-queries the Lead after the `IsConverted` flip.

---

## Gotcha 4: The 100-Lead Hard Limit Throws a LimitException, Not a Graceful Error

**What happens:** Passing more than 100 `Database.LeadConvert` objects to `Database.convertLead()` throws `System.LimitException: Too many lead conversions: 101` (or the actual count). This is not caught by a standard try/catch on `DmlException` — it is a limit exception that terminates the entire transaction.

**When it occurs:** Any call to `convertLead()` with more than 100 items, including from a Batch Apex `execute()` method if the batch size is not constrained to 100.

**How to avoid:** Always chunk the input list into groups of 100 before calling `convertLead()`. In Batch Apex, set the batch size to 100 or fewer in the `Database.executeBatch()` call. Never rely on the calling code to enforce this — put the chunking logic inside the conversion service so every caller is protected.

---

## Gotcha 5: setConvertedStatus Requires the API Name, Not the Label

**What happens:** `Database.LeadConvert.setConvertedStatus('Converted')` succeeds if the API name happens to match the label, but in many orgs the picklist label and API name differ. When the value does not match an `IsConverted = true` status, the conversion throws `INVALID_CONVERTED_STATUS`.

**When it occurs:** Any time the converted status is hardcoded as a string literal without verifying the exact API name, or when orgs have customized the LeadStatus picklist with non-standard names for their converted statuses.

**How to avoid:** Query the `LeadStatus` object dynamically to retrieve the converted status API name before building `LeadConvert` objects:

```apex
String convertedStatus = [
    SELECT MasterLabel FROM LeadStatus
    WHERE IsConverted = true
    LIMIT 1
].MasterLabel;
```

If multiple converted statuses exist, select the appropriate one for the use case rather than always taking `LIMIT 1`.
