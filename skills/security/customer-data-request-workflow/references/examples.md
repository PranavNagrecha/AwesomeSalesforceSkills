# Examples — Customer Data Subject Request (DSR) Workflow

A data subject request is a regulatory workflow with a deadline, a scope that spans
more objects than anyone expects, and an evidentiary requirement: you must be able to
show a regulator *what* you did, *when*, and *to which records*.

Salesforce gives you three building blocks, and which you use changes the whole
design:

| Building block | What it is |
|---|---|
| **Individual** | "Represents a customer's data privacy and protection preferences. Data privacy records based on the Individual object store your customers' …" — available when Data Protection and Privacy is enabled |
| **Privacy Center** | A managed capability whose policies "anonymize or transfer personal data from your org at your customer's request" — surfaced as `DsarPolicy` and `DsarPolicyLog` |
| **Custom workflow** | Policy-as-metadata plus batch Apex, for orgs without Privacy Center |

---

## Example 1: Record the preference before you act on it

**Context:** A customer emails asking to be forgotten. The request arrives in a
shared inbox.

**Problem:** The first thing most teams do is start deleting. The first thing they
should do is *record the request against the individual*, because everything
downstream — the SLA clock, the audit trail, the ability to answer "did we honour
it" — hangs off that record.

**Solution:** the `Individual` object carries the standing preferences. Both fields
are on **`Individual`**, not on `Contact`:

| Field (on `Individual`) | Meaning (Object Reference) |
|---|---|
| `ShouldForget` | "Preference to delete records and personal data related to this customer." |
| `SendIndividualData` | "Preference to export personal data for delivery to the customer." |

The Contact side of the link is `Contact.IndividualId` — "ID of the data privacy
record associated with this contact. This field is available if Data Protection and
Privacy is enabled." Its **Relationship Name is `Individual`**, it is a Lookup, and it
Refers To `Individual`. It is a standard relationship, so it takes **no `__r`
suffix** — `Contact.Individual__r` does not compile.

```apex
// Record the request first. This is the anchor for the SLA clock, the audit
// trail, and every downstream job.
//
// Traverse the lookup in the SELECT list: the preference fields live on
// Individual, so Contact.Individual.ShouldForget is the path. There is no
// Contact.ShouldForget and no Contact.Individual__r.
Contact subject = [
    SELECT Id, IndividualId,
           Individual.ShouldForget, Individual.SendIndividualData
    FROM Contact
    WHERE Id = :contactId
    LIMIT 1
];

// IndividualId is Nillable. A Contact with no data-privacy record yields null
// here, which is the ordinary state in an org that has just enabled the
// feature — so this is a branch, not an assertion.
Individual ind = subject.Individual;
if (ind == null) {
    // No preference record exists yet. Create one and link it, rather than
    // treating the absent record as "no request was made."
}
```

Two constraints that shape the design:

- "This object is available if Data Protection and Privacy is enabled." It is not on
  by default.
- "The Individual object isn't available to Customer Community, Partner Community,
  and Customer Portal users." A self-service portal cannot expose it directly, so a
  portal-submitted request needs a staging object and an internal process.

The object also carries history and change events —`IndividualHistory`,
`IndividualChangeEvent` (API 47.0 and later), and `IndividualShare` — so preference
changes are themselves auditable.

**Why it works:** `ShouldForget` is a *preference*, not an action. Setting it deletes
nothing. That separation is exactly right: the flag records that the request was made
and when, and a separate, auditable job acts on it. A design that jumps straight to
deletion has no record that the request existed.

---

## Example 2: Privacy Center — policies, and the log that is your evidence

**Context:** The org has Privacy Center.

**The two objects you actually work with:**

`DsarPolicy` — "Represents a Data Subject Access Request (DSAR) policy created in the
Privacy Center managed package. DSAR policies anonymize or transfer personal data
from your org at your customer's request." Available in API 50.0 and later.

- `IsActive` — "Indicates whether this policy can be used (`true`) or not (`false`)
  for data subject (customer) requests. **The default value is `false`.**" A policy
  that exists is not a policy that runs.
- Access: "This object is for Privacy Center customers with the `ReadAllData` or
  `PrivacyDataAccess` permissions."
- `Description` is limited to 255 characters — enough for a pointer to the real
  policy document, not for the policy itself.

`DsarPolicyLog` — "Represents the history of Data Subject Access Request (DSAR)
policy execution requests. This log records the status and results of executed …"
This is your evidence, and its field list tells you what a regulator can be shown:

| Field | What it gives you |
|---|---|
| The requesting data subject's 15–18 character ID (API 51.0 and later) | Who |
| The date and time the subject requested access (API 51.0+) | When they asked |
| The date and time the request was completed | When you finished — the SLA proof |
| The date and time the generated file is deleted | The retention boundary on the export |
| The most recent date and time the subject downloaded the file | Whether they collected it |
| An error field for failures generating the file | What went wrong |
| The ID of the org employee or admin making the request on behalf of the subject | Who acted, when it was staff-initiated |

**Query it as your compliance report:**

```sql
SELECT Id, Status__c, CreatedDate
FROM DsarPolicyLog
WHERE CreatedDate = LAST_N_DAYS:90
ORDER BY CreatedDate DESC
```

> The exact API names of `DsarPolicyLog`'s fields are managed-package-namespaced and
> vary by Privacy Center version. Describe the object in your org before writing the
> query into a runbook — the *semantics* above are documented, the literal field names
> are not portable.

**Why it works:** the log is generated as a side effect of executing the policy, so
the evidence cannot drift from what was actually done. A hand-built audit object can.

**The two things to check before relying on it:**

1. **`IsActive` defaults to `false`.** A policy authored and deployed but never
   activated silently does nothing. Verify activation as a distinct step.
2. **Policies are object-scoped.** Right to Be Forgotten policies "are created at the
   object level to ensure all customer data is removed," which means the completeness
   of your erasure equals the completeness of your object inventory. Example 3.

---

## Example 3: The object inventory is the hard part

**Context:** Any erasure request, with or without Privacy Center.

**Problem:** Teams scope the request to Contact and Lead. The subject's data is in a
dozen places, and the ones people miss are systematically the ones that matter.

**Build the inventory from the schema, not from memory:**

```apex
// Every object with a lookup or master-detail to Contact - the starting point
// for an erasure scope. Run this per anchor object (Contact, Lead, Account,
// Individual, User) rather than assuming.
Schema.DescribeSObjectResult contactDescribe = Contact.SObjectType.getDescribe();

for (Schema.ChildRelationship cr : contactDescribe.getChildRelationships()) {
    if (cr.getChildSObject() == null) {
        continue;
    }
    Schema.DescribeSObjectResult child = cr.getChildSObject().getDescribe();
    if (child.isQueryable() && child.isAccessible()) {
        System.debug(child.getName() + '.' + cr.getField().getDescribe().getName());
    }
}
```

Then walk this checklist, because several of these have no relationship to traverse:

```text
DIRECT
  Contact, Lead, Account (incl. Person Accounts), Individual
  Case, Opportunity Contact Role, CampaignMember, Task, Event
  Custom objects with a lookup to any of the above

IDENTITY
  User records for portal / Experience Cloud logins
  PersonAccount, which is Account AND Contact simultaneously

CONSENT
  ContactPointEmail / ContactPointPhone / ContactPointAddress
  ContactPointConsent, ContactPointTypeConsent
  AuthorizationFormConsent, CommunicationSubscriptionConsent, PartyConsent
  (all of which support Field Audit Trail retention policies, so they have
   ARCHIVED copies too)

FREE TEXT - the ones with no relationship to follow
  Case Comments, Chatter posts and comments, Email Messages,
  Notes, Attachments, ContentDocument / ContentVersion (file bodies),
  long-text description fields on any object

HISTORY AND ARCHIVE
  <Object>History records
  FieldHistoryArchive  <- see the warning below
  Setup Audit Trail

OFF-PLATFORM
  Backups, sandboxes seeded from production, data warehouse extracts,
  CRM Analytics datasets, marketing platform copies
```

**The archive warning, which is the single most-missed step:**

> "If you delete a record in your production data, the delete cascades to the related
> history tracking records, but Salesforce doesn't delete the history copied into the
> `FieldHistoryArchive` big object."
> — Salesforce Security Guide, *Field Audit Trail*

So in a Shield org, deleting the record leaves the field history — including old
values of the very fields being erased — in a separate store. Salesforce documents a
distinct procedure for deleting data in `FieldHistoryArchive`, and it must be an
explicit step in the runbook.

**Sandboxes are the second most-missed.** A sandbox refreshed from production before
the erasure holds a full copy. Either the erasure is repeated per sandbox, or sandbox
data masking runs on refresh and that is documented as the control.

**Why the inventory approach works:** describe-driven discovery finds the custom
objects nobody remembers. The checklist covers what describe cannot reach — free text,
archives, and off-platform copies.

---

## Example 4: The Apex path for orgs without Privacy Center

**Context:** No Privacy Center licence. Twelve objects in scope. The process must be
repeatable and evidenced.

**Solution — policy as metadata, execution as Apex, evidence as data.**

> ⚠ **This class performs irreversible DML in system mode.** Two properties are
> load-bearing and neither is optional:
>
> 1. **The Custom Metadata values are untrusted input.** Anyone with *Customize
>    Application* can edit a `DSR_Policy__mdt` row. Every value that reaches the
>    SOQL string is therefore resolved against the live schema first and only the
>    canonical name from `getDescribe().getName()` is concatenated. The subject id
>    is **bound**, never concatenated. Without this, a `Relationship_Path__c` of
>    `Id != null OR Id = null` mass-deletes the object — in system mode, bypassing
>    sharing.
> 2. **A policy row that does not resolve against the schema is a hard failure.**
>    It throws; it does not warn, skip, or continue. A DSAR executor that silently
>    skips a misconfigured object reports success while leaving the subject's data
>    in place, which is the exact failure a regulator asks about.
>
> Rehearse it against a synthetic subject in a full sandbox (Example 5) before it
> ever sees a real request.

```apex
/**
 * DSR_Policy__mdt — one row per object in scope.
 *   Object_API_Name__c   Text        sObject to act on
 *   Field_API_Name__c    Text        field to redact/null; blank only when
 *                                    Action__c = DELETE
 *   Action__c            Picklist    NULL | REDACT | DELETE
 *   Subject_Field__c     Text        the LOOKUP FIELD on this sObject that
 *                                    holds the subject's Individual id
 *   Justification__c     Text        why this object is in scope
 *
 * Subject_Field__c is a single field name, deliberately NOT a multi-hop SOQL
 * path. A path like 'Contact.Individual.Id' cannot be allowlisted with one
 * describe, and an un-allowlisted fragment concatenated into a system-mode
 * query that ends in DELETE is the whole vulnerability. Objects reachable only
 * through a parent get their own policy row anchored on their own lookup.
 *
 * ONE policy per transaction, chained. Two reasons, both load-bearing:
 *   - Limits. N policies inside one execute() means N SOQL and 2N DML. At 100
 *     policies that is SOQL 101; at 76 it is DML 151. Chaining makes the
 *     per-transaction cost constant — 1 SOQL and at most 2 DML — whatever N is.
 *   - Evidence. Each policy's audit rows commit in the same transaction as that
 *     policy's erasure, so a failure on policy 7 cannot roll back the evidence
 *     for policies 1-6. The single-transaction version could not make that
 *     promise, which is why it needed a caveat instead of a design.
 */
public with sharing class DsrExecutor implements Queueable {

    /** A policy row that does not resolve against the live schema. */
    public class PolicyConfigException extends Exception {}

    private final Id individualId;
    private final Id requestId;
    private final List<String> queue;   // DSR_Policy__mdt DeveloperNames, in order

    public DsrExecutor(Id individualId, Id requestId, List<String> policyNames) {
        this.individualId = individualId;
        this.requestId    = requestId;
        this.queue        = policyNames;
    }

    public void execute(QueueableContext ctx) {
        if (queue.isEmpty()) {
            return;
        }

        String policyName = queue.remove(0);
        DSR_Policy__mdt policy = DSR_Policy__mdt.getAll().get(policyName);
        if (policy == null) {
            throw new PolicyConfigException(
                'DSR run references a policy that no longer exists: ' + policyName);
        }

        runPolicy(policy);

        // Test context allows only one chained job, so the harness drives the
        // queue itself rather than relying on the chain.
        if (!queue.isEmpty() && !Test.isRunningTest()) {
            System.enqueueJob(new DsrExecutor(individualId, requestId, queue));
        }
    }

    private void runPolicy(DSR_Policy__mdt policy) {
        Schema.DescribeSObjectResult objDescribe =
            describeObject(policy.Object_API_Name__c);

        // Canonical names from the describe — never the raw metadata strings.
        String objectName   = objDescribe.getName();
        String subjectField = canonicalField(objDescribe, policy.Subject_Field__c);

        Boolean isDelete = ('DELETE' == policy.Action__c);
        Boolean isRedact = ('REDACT' == policy.Action__c);
        Boolean isNull   = ('NULL'   == policy.Action__c);
        if (!isDelete && !isRedact && !isNull) {
            // An unrecognised action must not fall through to "null the field".
            throw new PolicyConfigException(
                'DSR policy ' + objectName + ' has an unrecognised Action__c: ' +
                policy.Action__c);
        }

        String targetField =
            isDelete ? null : canonicalField(objDescribe, policy.Field_API_Name__c);

        // Only allowlisted identifiers are concatenated. The one value in the
        // query — the subject id — travels in the bind map, so it never reaches
        // the SOQL parser. SYSTEM_MODE is stated at the call site rather than
        // inherited silently from the class.
        String soql =
            'SELECT Id' + (targetField == null ? '' : ', ' + targetField) +
            ' FROM '  + objectName +
            ' WHERE ' + subjectField + ' = :subjectId';

        List<SObject> targets = Database.queryWithBinds(
            soql,
            new Map<String, Object>{ 'subjectId' => individualId },
            AccessLevel.SYSTEM_MODE);

        if (targets.isEmpty()) {
            return;
        }

        List<DSR_Action__c> auditRows = new List<DSR_Action__c>();
        for (SObject row : targets) {
            // Log the HASH of the original value, never the value itself. The
            // audit trail must prove what was erased without becoming a second
            // copy of the data you just erased.
            //
            // Read the raw value and null-check it before String.valueOf, so an
            // already-empty field records "nothing was there" rather than a
            // digest of the literal text "null" — which would read, to an
            // auditor, as evidence that a value was erased.
            Object rawValue = (targetField == null) ? null : row.get(targetField);
            String original = (rawValue == null) ? null : String.valueOf(rawValue);

            auditRows.add(new DSR_Action__c(
                Request__c     = requestId,
                Object_Name__c = objectName,
                Record_Id__c   = row.Id,
                Field_Name__c  = targetField,
                Action__c      = policy.Action__c,
                Value_Hash__c  = original == null ? null : EncodingUtil.convertToHex(
                    Crypto.generateDigest('SHA-256', Blob.valueOf(original))),
                Executed_At__c = System.now()
            ));
        }

        // Audit BEFORE the erasure, so an audit failure destroys nothing — and
        // because both commit together, the evidence for THIS policy survives a
        // failure on any later one.
        insert as system auditRows;

        if (isDelete) {
            delete as system targets;
        } else {
            for (SObject row : targets) {
                row.put(targetField, isRedact ? '[REDACTED]' : null);
            }
            update as system targets;
        }
    }

    /**
     * Allowlist the sObject name against the live schema and return the
     * canonical name. The raw metadata value is used only as a lookup key; it
     * is never what gets concatenated.
     */
    private static Schema.DescribeSObjectResult describeObject(String apiName) {
        if (String.isBlank(apiName)) {
            throw new PolicyConfigException('DSR policy has a blank Object_API_Name__c');
        }
        // The key casing of the global describe map is not documented, so try
        // the value as written and then lowercased. This is a lookup convenience
        // only — it does not widen the allowlist, because the name that reaches
        // the query still comes from getDescribe().getName() below.
        Map<String, Schema.SObjectType> gd = Schema.getGlobalDescribe();
        Schema.SObjectType sot = gd.get(apiName);
        if (sot == null) {
            sot = gd.get(apiName.toLowerCase());
        }
        if (sot == null) {
            throw new PolicyConfigException(
                'DSR policy names an sObject that does not exist in this org: ' + apiName);
        }
        return sot.getDescribe();
    }

    /**
     * Allowlist a field against that sObject's describe and return the canonical
     * name. Unresolvable is a HARD FAILURE — a DSAR run that skips a
     * misconfigured object reports success and leaves the data in place.
     */
    private static String canonicalField(Schema.DescribeSObjectResult d, String apiName) {
        if (String.isBlank(apiName)) {
            throw new PolicyConfigException(
                'DSR policy on ' + d.getName() + ' requires a field name for this action');
        }
        Map<String, Schema.SObjectField> fmap = d.fields.getMap();
        Schema.SObjectField f = fmap.get(apiName.toLowerCase());
        if (f == null) {
            f = fmap.get(apiName);
        }
        if (f == null) {
            throw new PolicyConfigException(
                'DSR policy names a field that does not exist on ' + d.getName() +
                ': ' + apiName);
        }
        return f.getDescribe().getName();
    }
}
```

**Why it works:**

- **Nothing user-controlled reaches the SOQL parser.** `Object_API_Name__c`,
  `Subject_Field__c`, and `Field_API_Name__c` are each used as a *lookup key* into
  a describe, and only the canonical name the describe returns is concatenated.
  The subject id is bound through `Database.queryWithBinds`. A metadata value of
  `Id != null OR Id = null` no longer produces a query at all — it produces a
  `PolicyConfigException`, because it is not the name of a field. The canonical
  treatment of this pattern is
  [`apex/apex-dynamic-soql-binding-safety`](../../../apex/apex-dynamic-soql-binding-safety/SKILL.md);
  this example is deliberately consistent with it.
- **`AccessLevel.SYSTEM_MODE` is explicit at the call site.** The executor must
  reach records the running user cannot see, so system mode is the right choice —
  but it is now stated in the argument list where a reviewer reads it, rather than
  implied. It is also why this class needs a tight permission set and an approval
  gate.
- **It fails closed.** Every unresolvable name, blank name, and unrecognised action
  throws before any DML runs. The previous shape would `continue` past a
  misconfigured policy and finish reporting success.
- **The limits are structural, not hopeful.** One policy per transaction is 1 SOQL
  and at most 2 DML regardless of how many objects compliance adds. The scope of a
  DSAR grows by exactly the mechanism — new `DSR_Policy__mdt` rows — that used to
  push it past the governor ceiling.
- **Audit before DML, in the same transaction as its own erasure.** Evidence for a
  completed policy survives a failure on a later one. If the evidence must also
  survive a failure *within* a policy, publish it as a platform event with
  `PUBLISH_IMMEDIATELY`, which survives rollback.
- **Hashing, not storing, the original value** keeps the audit table from becoming a
  second copy of the data you just erased. Note the limit of that claim: an
  unsalted SHA-256 of a low-entropy value — an email address, a phone number — is
  recoverable by dictionary attack. If the audit table's threat model includes an
  attacker who reads it, salt the digest with a per-request secret and store the
  salt separately.

**What this design still owes you:** a hard-delete step (records in the Recycle Bin
are not erased), the `FieldHistoryArchive` deletion, and the off-platform copies. None
of those are reachable from Apex over standard objects, and all three belong in the
runbook.

---

## Example 5: Rehearse in a sandbox with a synthetic subject

**Context:** The workflow is built. It has never been run.

**Problem:** The first execution against a real subject is irreversible and is being
performed under a regulatory deadline.

**Solution:**

```text
1. In a full sandbox, create a synthetic subject with data in EVERY object on the
   inventory - including the awkward ones: a Chatter post, an email message, a
   file, a portal User, a consent record, and a field with history tracking on.
2. Run the workflow end to end.
3. For each object on the inventory, query for residual data as an ADMIN.
   Anything that comes back is a gap.
4. Query FieldHistoryArchive for the subject's old values. In a Shield org this
   WILL return rows unless the archive deletion step ran.
5. Check the Recycle Bin. A soft delete is not an erasure.
6. Record the elapsed time per object and the total.
```

Step 3 is the whole exercise: search as an unrestricted admin for anything that
identifies the subject, in every object you listed and in global search. Step 6 tells
you whether the process fits inside the regulatory window at the volume you expect —
the deadline is not per request, it is per request under load.

**Why it works:** the gaps are found where they are cheap. A missed object discovered
in a sandbox is a backlog item; discovered in production it is a residual copy of data
you told a regulator you had erased.
