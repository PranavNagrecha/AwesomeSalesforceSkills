# Examples — Lead Conversion Customization

## Example 1: Invocable Apex for Flow-Triggered Bulk Lead Conversion

**Context:** A marketing team uses a Flow to batch-convert leads that reach a qualifying score. The Flow calls an Invocable Apex method, which must handle the conversion cleanly, suppress Opportunity creation, and transfer a custom `Lead_Score__c` field to the resulting Contact.

**Problem:** Using `Database.convertLead()` naively inside an invocable method with no chunking blows through the 100-record limit when the Flow processes a large batch. Additionally, the custom `Lead_Score__c` field is not mapped in Setup, so it drops silently.

**Solution:**

```apex
public class LeadConversionInvocable {

    @InvocableMethod(label='Convert Qualified Leads' description='Converts leads and maps custom fields')
    public static void convertQualifiedLeads(List<List<Id>> leadIdGroups) {
        // Flatten the grouped input (Flow passes lists of lists for bulk invocable)
        List<Id> allLeadIds = new List<Id>();
        for (List<Id> group : leadIdGroups) {
            allLeadIds.addAll(group);
        }
        LeadConversionService.convertAndMapFields(allLeadIds);
    }
}
```

```apex
public with sharing class LeadConversionService {

    public static void convertAndMapFields(List<Id> leadIds) {
        // Fetch converted status dynamically — never hardcode the label
        String convertedStatus = [
            SELECT MasterLabel FROM LeadStatus
            WHERE IsConverted = true
            LIMIT 1
        ].MasterLabel;

        // Query custom fields before conversion (capture values while record is unconverted)
        Map<Id, Lead> leadMap = new Map<Id, Lead>([
            SELECT Id, Lead_Score__c
            FROM Lead
            WHERE Id IN :leadIds AND IsConverted = false
        ]);

        // Build LeadConvert objects
        List<Database.LeadConvert> conversions = new List<Database.LeadConvert>();
        for (Id lid : leadMap.keySet()) {
            Database.LeadConvert lc = new Database.LeadConvert();
            lc.setLeadId(lid);
            lc.setConvertedStatus(convertedStatus);
            lc.setDoNotCreateOpportunity(true);
            lc.setSendNotificationEmail(false);
            conversions.add(lc);
        }

        // Chunk to 100 per convertLead() call
        List<Database.LeadConvertResult> allResults = new List<Database.LeadConvertResult>();
        for (Integer i = 0; i < conversions.size(); i += 100) {
            List<Database.LeadConvert> chunk = conversions.subList(i,
                Math.min(i + 100, conversions.size()));
            allResults.addAll(Database.convertLead(chunk, false)); // allOrNone = false
        }

        // Post-conversion: transfer unmapped custom fields to Contact
        List<Contact> contactsToUpdate = new List<Contact>();
        for (Database.LeadConvertResult r : allResults) {
            if (r.isSuccess() && r.getContactId() != null) {
                Lead sourceLead = leadMap.get(r.getLeadId());
                contactsToUpdate.add(new Contact(
                    Id = r.getContactId(),
                    Lead_Score__c = sourceLead.Lead_Score__c
                ));
            }
        }

        if (!contactsToUpdate.isEmpty()) {
            update contactsToUpdate;
        }
    }
}
```

**Why it works:** Pre-querying custom fields before `convertLead()` ensures the values are captured before the lead status changes. Post-conversion DML transfers those values using the `getContactId()` from the result. The chunking loop prevents the 100-record `LimitException`.

---

## Example 2: After-Update Trigger Detecting Conversion for UI and API Paths

**Context:** Leads can be converted from the UI by reps, via API by an external CRM sync, and via Apex by a scheduled job. A custom `Demo_Requested__c` checkbox on Lead must be copied to the resulting Contact in all cases. A service-layer approach covers only programmatic conversions.

**Problem:** If the field transfer is coded only inside a conversion service, UI conversions and external API conversions silently miss the field copy. An `after update` trigger on Lead is the only mechanism that covers all conversion paths.

**Solution:**

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
        handleConversion(newLeads, oldMap);
    }

    private void handleConversion(List<Lead> newLeads, Map<Id, Lead> oldMap) {
        // Detect the IsConverted flip — this is the conversion event
        List<Id> convertedLeadIds = new List<Id>();
        for (Lead l : newLeads) {
            if (l.IsConverted && !oldMap.get(l.Id).IsConverted) {
                convertedLeadIds.add(l.Id);
            }
        }
        if (convertedLeadIds.isEmpty()) return;

        // Re-query: Trigger.new does not include ConvertedContactId or custom fields
        Map<Id, Lead> freshLeads = new Map<Id, Lead>([
            SELECT Id, ConvertedContactId, Demo_Requested__c, Lead_Score__c
            FROM Lead
            WHERE Id IN :convertedLeadIds
        ]);

        List<Contact> updates = new List<Contact>();
        for (Lead l : freshLeads.values()) {
            if (l.ConvertedContactId != null) {
                updates.add(new Contact(
                    Id = l.ConvertedContactId,
                    Demo_Requested__c = l.Demo_Requested__c,
                    Lead_Score__c    = l.Lead_Score__c
                ));
            }
        }

        if (!updates.isEmpty()) {
            update updates;
        }
    }
}
```

**Why it works:** The `IsConverted` flip detection (`l.IsConverted && !oldMap.get(l.Id).IsConverted`) is the canonical path-agnostic way to react to conversion. A re-query inside `after update` is necessary because `Trigger.new` does not expose `ConvertedContactId` — that field is populated by the conversion engine before the `after update` fires but is not included in the trigger payload by default.

---

## Anti-Pattern: Calling convertLead() Inside a Loop Without Chunking

**What practitioners do:** Iterate over a list of lead Ids and call `Database.convertLead()` with a single-element list for each one to "keep it simple."

**What goes wrong:** While this avoids the 100-record limit per call (each call has one record), it generates one DML statement per lead, fires full trigger chains per iteration, and quickly exhausts DML statement and SOQL governor limits. A batch of 50 leads creates at least 150 DML operations (Lead, Contact, Account each).

**Correct approach:** Build a `List<Database.LeadConvert>`, add all records, chunk at 100, and call `convertLead()` once per chunk. Query the converted status once outside the loop.
