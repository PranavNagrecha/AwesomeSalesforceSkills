# Examples — Clinical Data Quality

## Example 1: Configuring Matching Rules for Person Account Duplicate Detection in Health Cloud

**Context:** A Health Cloud org onboards patients through a digital intake flow. The team wants to prevent duplicate patient (Person Account) records from being created when the same patient registers twice with slightly different name spellings.

**Problem:** Without a Matching Rule scoped to the Account object, duplicate Person Accounts are created silently. A Duplicate Rule on the Contact object has no effect on Person Accounts — Person Account deduplication runs on the Account object exclusively.

**Solution:**

```text
Setup > Duplicate Management > Matching Rules > New

Object: Account
Rule Name: Patient Name and Birthdate Match
Description: Detects duplicate Person Account patient records by name and birth date

Match Criteria:
  Field: FirstName     | Matching Method: Fuzzy - First Name  | Match Blank Fields: No
  Field: LastName      | Matching Method: Fuzzy - Last Name   | Match Blank Fields: No
  Field: PersonBirthdate | Matching Method: Exact             | Match Blank Fields: No

If an optional MedicalRecordNumber__c field exists on Account:
  Field: MedicalRecordNumber__c | Matching Method: Exact | Match Blank Fields: No

Activate the Matching Rule.

Setup > Duplicate Management > Duplicate Rules > New

Object: Account
Rule Name: Duplicate Patients — Alert
Duplicate Rule Condition: Active AND IsPersonAccount = true
Matching Rule: (select the rule created above)
Action on Create: Allow + Alert
Action on Edit:  Allow + Alert

Activate the Duplicate Rule.
```

**Why it works:** Scoping to Account (not Contact) ensures the rule runs against the Person Account record itself. Fuzzy matching on name fields catches common intake typos. Setting the action to Alert (not Block) allows intake staff to proceed while surfacing the potential match for review — a safer initial configuration than Block, which would halt intake if the match quality is imperfect.

---

## Example 2: Pre-Merge Apex Batch to Reassign Clinical Records Before Account Merge

**Context:** A care operations team has identified 50 pairs of duplicate patient (Person Account) records. They are preparing to merge each pair. Without intervention, merging the accounts will orphan all EpisodeOfCare, PatientMedication, and ClinicalEncounter records associated with the losing account.

**Problem:** The platform does NOT automatically reparent Health Cloud clinical objects when Person Accounts are merged. Clinical records on the losing (deleted) account become orphaned — invisible on the winning patient's record — causing silent patient data loss.

**Solution:**

```apex
/**
 * PreMergePatientReassignment
 *
 * Reassigns clinical records from a losing patient Account to a winning patient Account
 * BEFORE the merge DML executes. Must be called and confirmed complete before merging.
 *
 * Usage:
 *   Database.executeBatch(
 *       new PreMergePatientReassignment(losingAccountId, winningAccountId), 200
 *   );
 */
public class PreMergePatientReassignment implements Database.Batchable<SObject>, Database.Stateful {

    private final Id losingId;
    private final Id winningId;

    // Add or remove clinical objects as appropriate for your org.
    private static final List<String> CLINICAL_OBJECTS = new List<String>{
        'EpisodeOfCare',
        'PatientMedication',
        'ClinicalEncounter',
        'CareObservation',
        'CoveredBenefit'
    };

    // Map object API name -> lookup field API name pointing to Account/Patient
    private static final Map<String, String> LOOKUP_FIELDS = new Map<String, String>{
        'EpisodeOfCare'      => 'AccountId',
        'PatientMedication'  => 'PatientId',
        'ClinicalEncounter'  => 'AccountId',
        'CareObservation'    => 'AccountId',
        'CoveredBenefit'     => 'MemberId'
    };

    private Integer objectIndex = 0;
    public List<String> errors = new List<String>();

    public PreMergePatientReassignment(Id losingAccountId, Id winningAccountId) {
        this.losingId  = losingAccountId;
        this.winningId = winningAccountId;
    }

    public Database.QueryLocator start(Database.BatchableContext bc) {
        String objName    = CLINICAL_OBJECTS[objectIndex];
        String lookupFld  = LOOKUP_FIELDS.get(objName);
        String soql = 'SELECT Id, ' + lookupFld
                    + ' FROM ' + objName
                    + ' WHERE ' + lookupFld + ' = :losingId';
        return Database.getQueryLocator(soql);
    }

    public void execute(Database.BatchableContext bc, List<SObject> scope) {
        String objName   = CLINICAL_OBJECTS[objectIndex];
        String lookupFld = LOOKUP_FIELDS.get(objName);
        for (SObject rec : scope) {
            rec.put(lookupFld, winningId);
        }
        List<Database.SaveResult> results = Database.update(scope, false);
        for (Database.SaveResult sr : results) {
            if (!sr.isSuccess()) {
                for (Database.Error e : sr.getErrors()) {
                    errors.add(objName + ' ' + sr.getId() + ': ' + e.getMessage());
                }
            }
        }
    }

    public void finish(Database.BatchableContext bc) {
        objectIndex++;
        if (objectIndex < CLINICAL_OBJECTS.size()) {
            // Chain to next clinical object
            Database.executeBatch(this, 200);
        } else {
            // All clinical objects reassigned — safe to merge
            if (errors.isEmpty()) {
                System.debug('PreMergePatientReassignment complete. Safe to merge.');
                // Trigger merge after confirmation:
                // Account master = [SELECT Id FROM Account WHERE Id = :winningId];
                // Account dup    = [SELECT Id FROM Account WHERE Id = :losingId];
                // merge master dup;
            } else {
                System.debug('Errors during reassignment: ' + errors);
                // Do NOT merge until all errors are resolved.
            }
        }
    }
}
```

**Why it works:** The batch reassigns each clinical object's lookup field from the losing Account ID to the winning Account ID before the merge DML fires. Because the losing Account still exists during reassignment, the lookups update successfully. After the batch completes with no errors, the `merge` DML can be safely executed — the losing Account has no clinical children to orphan.

---

## Anti-Pattern: Merging Person Accounts First, Then Trying to Reassign Clinical Records

**What practitioners do:** Execute the Account merge first, then write a script to find and reassign any orphaned clinical records by querying for records whose lookup field points to the deleted Account ID.

**What goes wrong:** After an Account merge, the losing Account record is deleted (hard-deleted, not in the Recycle Bin for most merge scenarios). Querying clinical objects by `WHERE AccountId = :deletedId` returns zero rows — the deleted ID resolves to nothing. The orphaned records are effectively unqueryable by their patient lookup unless you know their record IDs in advance. Recovering them requires querying audit logs, using the Tooling API or Metadata API, or restoring from a sandbox backup.

**Correct approach:** Always run the pre-merge reassignment batch and confirm zero errors before executing the merge DML. The order is non-negotiable: reassign first, merge second, audit third.
