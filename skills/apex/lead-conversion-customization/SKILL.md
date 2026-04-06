---
name: lead-conversion-customization
description: "Use when writing Apex to customize lead conversion: controlling which records are created, copying custom field values post-conversion, firing related record logic on convert, or structuring LeadConvert calls. Triggers: 'lead conversion apex', 'Database.LeadConvert', 'custom field mapping conversion', 'convert lead trigger', 'lead convert opportunity', 'LeadConvertResult'. NOT for configuring lead conversion field mapping in Setup UI, managing lead assignment rules, or building web-to-lead forms — use admin/lead-management-and-conversion for those."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
  - Operational Excellence
triggers:
  - "custom fields are not being copied when I convert a lead in Apex"
  - "how do I run Apex code when a lead is converted"
  - "how do I use Database.LeadConvert to skip creating an opportunity"
  - "lead convert trigger not working as expected"
  - "how do I map custom lead fields to contact or account fields during conversion"
  - "LeadConvertResult cannot be used in test class"
tags:
  - lead-conversion
  - Database.LeadConvert
  - LeadConvert
  - apex-triggers
  - custom-field-mapping
  - after-convert
inputs:
  - "Lead record Id(s) to convert"
  - "Target converted status API name from the LeadStatus picklist"
  - "Whether an Opportunity should be created (and its name)"
  - "Existing Account or Contact Id if merging into an existing record"
  - "Custom fields on Lead that need to be transferred to Contact, Account, or Opportunity"
outputs:
  - "Apex class or service method implementing bulkified LeadConvert logic"
  - "After-convert trigger or handler that maps custom fields post-conversion"
  - "Test class with valid LeadConvertResult test patterns"
  - "Decision guidance on when to use triggers vs. invocable Apex vs. process automation"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Lead Conversion Customization

This skill activates when a practitioner needs Apex to control, extend, or react to lead conversion — including custom field transfer, selective record creation, and post-conversion side effects. It covers the `Database.LeadConvert` API and the Apex trigger patterns that fire during and after conversion.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the converted LeadStatus API name. `Database.LeadConvert.setConvertedStatus()` requires the exact API name of a picklist value where `IsConverted = true`. Passing a display label causes a runtime error.
- Verify whether the org already has an `after update` trigger on Lead that fires on conversion. Conversion fires `before update` and `after update` on Lead, `before insert`/`after insert` on Contact, Account, and (optionally) Opportunity. Adding logic in multiple places without coordination causes duplicate processing.
- Know the batch size. `Database.convertLead()` accepts a maximum of 100 `Database.LeadConvert` instances per call. Exceeding this limit throws a `System.LimitException` at runtime.
- Understand which custom fields are mapped in Setup (Object Manager > Lead > Map Lead Fields). Only mapped fields are copied automatically. All others silently drop their values unless handled in Apex post-conversion.

---

## Core Concepts

### Database.LeadConvert and LeadConvertResult

`Database.LeadConvert` is the Apex object used to configure a single lead conversion. You build a list of these, one per lead, set properties on each, and pass the list to `Database.convertLead()`. The method returns a `List<Database.LeadConvertResult>`.

Key setters on `Database.LeadConvert`:

| Method | Purpose |
|---|---|
| `setLeadId(Id)` | Required. Specifies the Lead to convert. |
| `setConvertedStatus(String)` | Required. API name of a converted LeadStatus value. |
| `setDoNotCreateOpportunity(Boolean)` | Pass `true` to skip Opportunity creation. |
| `setOpportunityName(String)` | Sets the Opportunity name. Defaults to company name if omitted. |
| `setAccountId(Id)` | Merge the Lead into an existing Account instead of creating a new one. |
| `setContactId(Id)` | Merge the Lead into an existing Contact instead of creating a new one. |
| `setOwnerId(Id)` | Assign the resulting records to a specific user. |
| `setSendNotificationEmail(Boolean)` | Whether to send the lead owner notification email. |

`Database.LeadConvertResult` exposes `getAccountId()`, `getContactId()`, `getOpportunityId()`, `isSuccess()`, and `getErrors()`. You cannot instantiate this class directly in test code — see the Testing Gotcha below.

### Custom Field Transfer Is Not Automatic

Salesforce automatically copies Lead field values to Contact, Account, and Opportunity only for fields that are explicitly mapped in Setup > Object Manager > Lead > Map Lead Fields. Custom fields that are not mapped are silently dropped at conversion time. The Lead record remains in the database with the original field values, so recovery is possible, but it requires a follow-up query against the converted Lead.

The correct pattern is to perform a post-conversion DML update: after calling `Database.convertLead()`, query the converted Lead for the unmapped custom fields, then update the resulting Contact, Account, or Opportunity records with those values.

### Conversion Fires Triggers on Multiple Objects

A single `Database.convertLead()` call fires triggers on:

- **Lead**: `before update` and `after update` (with `IsConverted` flipping from `false` to `true`)
- **Account**: `before insert` / `after insert` (if a new Account is created) or `before update` / `after update` (if merged into existing)
- **Contact**: `before insert` / `after insert` (if a new Contact is created) or `before update` / `after update` (if merged)
- **Opportunity**: `before insert` / `after insert` (if Opportunity creation is not suppressed)

All of this happens in a single transaction. Governor limits are shared across all trigger fires. SOQL queries and DML operations performed in any one trigger count against the same transaction limits.

### The 100-Lead Batch Limit

`Database.convertLead()` enforces a hard limit of 100 `Database.LeadConvert` objects per invocation. When processing more than 100 leads, split the input list into chunks of 100 and call `convertLead()` multiple times. In a Batch Apex `execute()` method, set batch size to 100 or fewer to stay within this limit without manual chunking.

---

## Common Patterns

### Pattern 1: Controlled Bulk Lead Conversion Service

**When to use:** A user action, Flow, or scheduled job needs to convert leads in bulk with custom configuration — suppressing opportunity creation, targeting specific accounts, or running post-conversion field mapping.

**How it works:**

```apex
public class LeadConversionService {

    public static void convertLeads(List<Id> leadIds) {
        // Fetch the converted status once
        String convertedStatus = [
            SELECT MasterLabel FROM LeadStatus
            WHERE IsConverted = true
            LIMIT 1
        ].MasterLabel;

        List<Database.LeadConvert> conversions = new List<Database.LeadConvert>();
        for (Id leadId : leadIds) {
            Database.LeadConvert lc = new Database.LeadConvert();
            lc.setLeadId(leadId);
            lc.setConvertedStatus(convertedStatus);
            lc.setDoNotCreateOpportunity(true);
            lc.setSendNotificationEmail(false);
            conversions.add(lc);
        }

        // Enforce 100-lead batch limit
        List<Database.LeadConvertResult> results = new List<Database.LeadConvertResult>();
        for (Integer i = 0; i < conversions.size(); i += 100) {
            List<Database.LeadConvert> batch = conversions.subList(i,
                Math.min(i + 100, conversions.size()));
            results.addAll(Database.convertLead(batch));
        }

        // Collect converted record Ids for post-conversion field mapping
        List<Id> contactIds = new List<Id>();
        for (Database.LeadConvertResult r : results) {
            if (r.isSuccess()) {
                contactIds.add(r.getContactId());
            }
        }
        // Continue with custom field transfer...
    }
}
```

**Why not the alternative:** Calling `convertLead()` one record at a time in a loop hits governor limits quickly and cannot be bulkified across a trigger batch. Building a list-based service method keeps the conversion atomic and governor-safe.

### Pattern 2: Post-Conversion Custom Field Transfer via After-Update Trigger on Lead

**When to use:** Unmapped custom fields on Lead must be transferred to Contact, Account, or Opportunity every time a conversion occurs — including conversions triggered from the UI, from Flow, or from Apex.

**How it works:**

Use an `after update` trigger on Lead. When `IsConverted` flips to `true`, query the Lead's custom fields, then update the related Contact.

```apex
trigger LeadTrigger on Lead (before insert, before update, after insert, after update) {
    if (!TriggerControl.isActive('Lead')) return;
    LeadTriggerHandler handler = new LeadTriggerHandler();

    if (Trigger.isBefore && Trigger.isInsert)  handler.onBeforeInsert(Trigger.new);
    if (Trigger.isBefore && Trigger.isUpdate)  handler.onBeforeUpdate(Trigger.new, Trigger.oldMap);
    if (Trigger.isAfter  && Trigger.isInsert)  handler.onAfterInsert(Trigger.new);
    if (Trigger.isAfter  && Trigger.isUpdate)  handler.onAfterUpdate(Trigger.new, Trigger.oldMap);
}
```

```apex
public with sharing class LeadTriggerHandler {

    public void onAfterUpdate(List<Lead> newLeads, Map<Id, Lead> oldMap) {
        List<Id> convertedLeadIds = new List<Id>();
        for (Lead l : newLeads) {
            if (l.IsConverted && !oldMap.get(l.Id).IsConverted) {
                convertedLeadIds.add(l.Id);
            }
        }
        if (convertedLeadIds.isEmpty()) return;

        // Re-query because ConvertedContactId is not in Trigger.new
        Map<Id, Lead> leads = new Map<Id, Lead>([
            SELECT Id, ConvertedContactId, Custom_Score__c, Demo_Requested__c
            FROM Lead
            WHERE Id IN :convertedLeadIds
        ]);

        List<Contact> contactsToUpdate = new List<Contact>();
        for (Lead l : leads.values()) {
            if (l.ConvertedContactId != null) {
                contactsToUpdate.add(new Contact(
                    Id = l.ConvertedContactId,
                    Lead_Score__c = l.Custom_Score__c,
                    Demo_Requested__c = l.Demo_Requested__c
                ));
            }
        }

        if (!contactsToUpdate.isEmpty()) {
            update contactsToUpdate;
        }
    }
}
```

**Why not the alternative:** Doing the update inside the Apex service that calls `convertLead()` works only for programmatic conversions. The trigger-based approach also covers UI conversions, Flow-driven conversions, and API conversions from external systems.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to suppress Opportunity creation | `setDoNotCreateOpportunity(true)` on `Database.LeadConvert` | Only reliable way; UI flows and Flow always create an Opp unless this flag is set programmatically |
| Custom fields must transfer on every conversion (UI + Apex) | `after update` trigger on Lead detecting `IsConverted` flip | Fires for all conversion paths, not just programmatic ones |
| Custom fields must transfer only for programmatic conversion | Post-`convertLead()` DML in the service class | Simpler, avoids trigger complexity, but misses UI-driven conversions |
| Converting >100 leads in a batch job | Batch Apex with batch size 100, or manual chunking | Hard 100-record limit on `convertLead()`; exceeding it throws `LimitException` |
| Need to merge lead into an existing account | `setAccountId(existingAccountId)` | Platform merges data rather than creating a duplicate account |
| Need to test LeadConvertResult | JSON deserialization workaround | Cannot construct `LeadConvertResult` in test code; must deserialize from JSON |
| Assign converted records to a specific user | `setOwnerId(userId)` on `Database.LeadConvert` | Applies to all resulting records (Account, Contact, Opportunity) |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Gather context** — Identify the converted LeadStatus API name, which custom fields need to be transferred, whether Opportunity creation should be suppressed, and whether an existing Account or Contact should be targeted. Confirm the org edition and whether a trigger framework is already in use.
2. **Check for existing Lead triggers** — Query the org for any `after update` triggers on Lead. If one exists, add conversion logic inside the existing handler rather than creating a second trigger. One trigger per object is non-negotiable.
3. **Build or extend the conversion service** — Implement `Database.LeadConvert` list construction with correct setters. Add chunking logic for batches over 100. Use `allOrNone = false` with `Database.convertLead(conversions, false)` only if partial success is acceptable, and handle individual errors from `LeadConvertResult.getErrors()`.
4. **Add post-conversion field mapping** — For unmapped custom fields, either add logic after `convertLead()` in the service (programmatic-only path) or add an `after update` trigger on Lead detecting `IsConverted` flip (covers all paths). Do not mix both without a guard to prevent double-processing.
5. **Write the test class** — Create a Lead, convert it using `Database.convertLead()`, retrieve the resulting `LeadConvertResult` from the return value, and assert on `isSuccess()` and resulting record Ids. Do not attempt to instantiate `LeadConvertResult` directly; use the returned instance.
6. **Run the checker script and validate** — Execute `python3 scripts/skill_sync.py --skill skills/apex/lead-conversion-customization` and then `python3 scripts/validate_repo.py` before marking the work complete.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Converted LeadStatus API name is fetched dynamically or validated — not hardcoded as a display label
- [ ] `Database.convertLead()` calls are chunked to 100 leads per invocation
- [ ] Custom field transfer logic runs post-conversion, not inside the `convertLead()` call itself
- [ ] No second Lead trigger has been created if one already exists — logic added to existing handler
- [ ] Test class verifies `isSuccess()` on `LeadConvertResult` and does not instantiate the result class directly
- [ ] Post-conversion DML uses `with sharing` and respects FLS for the target fields
- [ ] Error handling covers partial failures when `allOrNone = false` is used

---

## Salesforce-Specific Gotchas

1. **`LeadConvertResult` cannot be instantiated in test code** — The class has no public constructor. Attempting `new Database.LeadConvertResult()` fails at compile time. In tests, call `Database.convertLead()` with a real or test Lead and use the returned result instances. If mock results are needed, deserialize from a JSON string using `(Database.LeadConvertResult) JSON.deserialize(...)`.

2. **`IsConverted` flip fires `after update`, not a special event** — There is no dedicated conversion trigger event. The only reliable detection in a trigger is checking `l.IsConverted && !oldMap.get(l.Id).IsConverted` in `after update`. Logic placed in `before update` cannot read `ConvertedContactId` or `ConvertedAccountId` yet — those fields are populated only after the conversion DML completes.

3. **Unmapped custom fields silently drop their values** — Salesforce does not warn or error when a custom Lead field has no mapping. The data disappears at conversion time. The original Lead record retains its values but the Contact, Account, and Opportunity do not receive the data without explicit post-conversion DML.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `LeadConversionService.cls` | Bulkified Apex service that builds `Database.LeadConvert` objects, chunks at 100, and calls `convertLead()` |
| `LeadTriggerHandler.cls` | Handler class with `onAfterUpdate` method detecting the `IsConverted` flip and performing post-conversion field mapping |
| `LeadTrigger.trigger` | Minimal trigger body delegating to the handler with an activation guard |
| `LeadConversionServiceTest.cls` | Test class covering success path, partial failure path, and custom field transfer assertions |

---

## Related Skills

- `admin/lead-management-and-conversion` — Use for configuring lead conversion field mapping in Setup, managing lead status picklist values, and building assignment rules. This Apex skill assumes Setup configuration is already in place.
- `apex/trigger-framework` — Use when deciding how to structure the Lead trigger handler or when a trigger framework is already in the org and must be followed.
- `apex/batch-apex-patterns` — Use when converting more than a few hundred leads — Batch Apex handles the 100-per-call chunking cleanly at scale.
- `apex/mixed-dml-and-setup-objects` — Conversion is a DML-heavy operation; be aware of mixed-DML constraints if post-conversion logic touches Setup objects.
