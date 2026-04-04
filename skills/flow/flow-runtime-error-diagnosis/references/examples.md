# Examples — Flow Runtime Error Diagnosis

## Example 1: NULL_REFERENCE in Record-Triggered Flow When Account Has No Contact

**Scenario:** A Record-Triggered Flow on Opportunity fires after update. It uses a Get Records element to fetch the primary Contact from the related Account, then populates a custom field from the Contact's email. In accounts with no contacts, the Get Records returns null, and the next Assignment element throws a NULL_REFERENCE error.

**Fault email content (excerpt):**
```
Flow API Name: Opportunity_Post_Update
Version: 5
Error element: Assign_Primary_Contact_Email (Assignment)
Error: NullPointerException: Attempt to de-reference a null object
```

**Root cause:** The variable `{!varPrimaryContact}` set by Get Records is null when no contact exists. The Assignment element references `{!varPrimaryContact.Email}` without checking for null first.

**Fix:**
1. After the Get Records element (`Get_Primary_Contact`), add a Decision element: `Is_Contact_Null` — outcome "Contact Found": `{!varPrimaryContact} is null` = False.
2. Route the null path (no contact) to the end of the flow.
3. Only proceed to the Assignment element on the "Contact Found" path.

**Result:** Flow handles accounts with no contacts gracefully. No fault email, no error shown to user.

---

## Example 2: SOQL Limit Error in Loop Processing Child Records

**Scenario:** A Screen Flow lets users process a list of Opportunities. Inside a Loop element iterating over a collection, there is a Get Records element that fetches related OpportunityLineItems for each opportunity. With 150 opportunities in the list, the flow hits the 101 SOQL limit.

**Fault email content (excerpt):**
```
Flow API Name: Bulk_Opportunity_Processor
Version: 2
Error element: Get_Line_Items_For_Opp (Get Records)
Error: LIMIT_EXCEEDED: Too many SOQL queries: 101
```

**Root cause:** Get Records inside a Loop fires one SOQL query per iteration.

**Fix:**
1. Move `Get_Line_Items_For_Opp` outside the Loop — retrieve all OpportunityLineItems for the entire Opportunity collection in a single Get Records using a filter: `OpportunityId IN {!colOpportunityIds}`.
2. Inside the Loop, use a Collection Filter or Decision to find line items matching the current iteration's Opportunity ID from the already-retrieved collection.

**Result:** One SOQL query instead of one per record. Flow completes within governor limits regardless of collection size (up to the 50,000 record collection limit).

---

## Example 3: INVALID_FIELD After Field Deletion

**Scenario:** A developer deleted a custom field `Account.Legacy_Region__c` that had been deprecated. A Record-Triggered Flow on Account still referenced this field in a Get Records filter. The flow was not updated when the field was deleted.

**Fault email content (excerpt):**
```
Flow API Name: Account_Region_Classifier
Version: 3
Error element: Get_Accounts_By_Region (Get Records)
Error: INVALID_FIELD: No such column 'Legacy_Region__c' on entity 'Account'
```

**Root cause:** The flow metadata still holds a reference to the deleted field. The flow saved without error when the field was deleted (Salesforce does not cascade-validate flow references on field deletion).

**Fix:**
1. Open the flow in Flow Builder (use Ctrl+F to search for `Get_Accounts_By_Region`).
2. Edit the Get Records filter — remove the reference to `Legacy_Region__c`.
3. Replace with the current field or remove the filter condition entirely.
4. Save and activate the updated version.

**Prevention:** When deleting custom fields, search for flow references first using Flow Builder's Field Finder or SOQL on `FlowDefinition` and `FlowVersionView` metadata.
