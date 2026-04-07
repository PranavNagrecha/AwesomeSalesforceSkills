# Examples — Marketing Cloud Data Sync

## Example 1: Joining Contact SDE to Sendable DE for Personalized Email Send

**Context:** A B2B marketing team wants to send a campaign email to all active Salesforce Contacts in the "Enterprise" account segment. The email body needs to reference Account Name and the Contact's most recent Case Status — both fields that live in the CRM, not in Marketing Cloud's native subscriber store.

**Problem:** The team has MC Connect configured and the Contact SDE is syncing. A junior admin attempts to use the Contact SDE directly as the send audience in Email Studio, but the send fails with no audience found. A second attempt uses AMPscript to look up fields directly from the SDE without a Contact Builder relationship — personalization strings return empty.

**Solution:**

Step 1 — In Contact Builder > Data Designer, confirm the Contact SDE exists under Synchronized Data Sources. Note the field used as the linking key (in this case `ContactID`, which maps to the `Contact Key` attribute in the attribute group).

Step 2 — Create (or identify) a sendable Data Extension in the main DE folder with at minimum these fields:

```
Field Name       | Type    | Notes
-----------------|---------|------------------------------------
ContactKey       | Text    | Send relationship to Subscriber Key
EmailAddress     | Email   | Required for email send
AccountName      | Text    | Populated via Query Activity from Account SDE
CaseStatus       | Text    | Populated via Query Activity from Case SDE join
```

Step 3 — Populate the sendable DE using a Query Activity that joins the Contact SDE, Account SDE, and Case SDE:

```sql
SELECT
    c.ContactID        AS ContactKey,
    c.Email            AS EmailAddress,
    a.Name             AS AccountName,
    cs.Status          AS CaseStatus
FROM
    [Contact_Salesforce]     c    -- Contact SDE name in MC
    JOIN [Account_Salesforce] a   ON c.AccountId = a.Id
    LEFT JOIN [Case_Salesforce] cs ON cs.ContactId = c.Id
WHERE
    c.HasOptedOutOfEmail = false
    AND a.Type = 'Enterprise Customer'
```

Step 4 — In Contact Builder > Data Designer, link the sendable DE to the Contact attribute group via `ContactKey = Contact Key`.

Step 5 — In Email Studio, use the sendable DE as the send audience. AMPscript personalization strings now resolve via the Contact Builder relationship.

**Why it works:** SDEs are read-only lookup tables in the Contact model. They cannot be send targets, but once linked via Contact Builder, their data is traversable during personalization resolution. The Query Activity pre-populates the sendable DE so the send audience is defined and writeable, while CRM field data flows through the relationship for real-time AMPscript lookups.

---

## Example 2: Diagnosing Missing Fields After Initial Sync (250-Field Cap)

**Context:** A marketing ops team configures a Contact sync to pull 310 Contact fields from Salesforce CRM. The sync completes without error, and the Contact SDE shows records. Three weeks into usage, a campaign team reports that the `Loyalty_Tier__c` field — selected for personalization — is blank in every send preview.

**Problem:** The field is present in Salesforce CRM with valid data. No error appeared during sync setup. The team suspects a sync failure, triggers a full sync, and waits — the field is still blank after the full sync completes.

**Solution:**

Step 1 — In Contact Builder > Synchronized Data Sources, open the Contact object configuration and review the selected field list. Count the number of selected fields.

If the count exceeds 250, the field ordering in the selection UI determines which 250 are synced. Fields beyond position 250 in the selection order are silently dropped.

Step 2 — Inspect the Contact SDE's actual column list (viewable in Data Extensions or via a SSJS script):

```javascript
// SSJS — list SDE columns to compare against intended field selection
var de = DataExtension.Init("Contact_Salesforce");
var cols = de.Fields.Retrieve();
Write(Stringify(cols));
```

Compare the returned column list to the intended field selection. `Loyalty_Tier__c` will be absent from the column list if it was excluded by the cap.

Step 3 — Reduce the selected field count to 250 or fewer. Prioritize fields required for active campaigns. Deselect fields used only for reporting that can be sourced via Salesforce reports instead. Re-save the sync configuration. Trigger an incremental sync (not a full sync unless record counts are mismatched).

Step 4 — After the next sync cycle, confirm `Loyalty_Tier__c` appears in the SDE column list and contains populated values.

**Why it works:** The 250-field hard cap is enforced silently by the sync engine. No error surfaces because from the platform's perspective the sync succeeded — it just excluded the out-of-range fields. The only reliable audit is a post-sync column count comparison. Triggering a full sync without reducing the field count reproduces the same exclusion.

---

## Anti-Pattern: Attempting to Write to an SDE via Query Activity

**What practitioners do:** When needing to enrich SDE data with Marketing Cloud engagement data (e.g., appending email open counts to the Contact SDE), some practitioners configure a Query Activity with the Contact SDE as the target DE, reasoning that since the SDE appears in the Data Extension list it can be used as a query target.

**What goes wrong:** The Query Activity fails with a permissions or write-protection error at runtime. Even if the activity is configured to "Append" or "Overwrite," the write is rejected because SDEs are system-managed, read-only objects. Depending on the journey or automation configuration, this failure may silently skip the step rather than surfacing an error to the admin.

**Correct approach:** Never use an SDE as a Query Activity target. Instead:
1. Create a standard (non-synchronized) Data Extension to hold the enriched data.
2. Query from the SDE into this new DE (SDE as source, custom DE as target).
3. Use the custom DE for any write operations, further enrichment, or as the send audience.

The SDE remains the authoritative read-only source; all writeable derived data lives in purpose-built DEs.
