# LLM Anti-Patterns — Org Cleanup And Technical Debt

Common mistakes AI coding assistants make when generating or advising on Salesforce org cleanup.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Suggesting Direct Production Deletion Without Sandbox Testing

**What the LLM generates:** "Go to Setup > Object Manager > Account > Fields, find the unused field, and click Delete." — with no mention of sandbox testing, reference checking, or the deleted field queue.

**Why it happens:** LLMs optimize for the shortest path to the stated goal. Deleting a field through Setup is technically the correct UI path, but skipping the safety steps before and after deletion is a critical omission.

**Correct pattern:**

```
1. Search all metadata for references to the field (Flows, Apex, validation rules, reports, page layouts).
2. Confirm the field has no populated data (SOQL COUNT query).
3. Delete the field in a sandbox first. Run all Apex tests. Verify critical Flows.
4. Only then delete in production.
5. Purge the deleted fields queue if slot recovery is needed immediately.
```

**Detection hint:** If cleanup advice does not mention "sandbox" or "test" before a deletion step, it is missing the safety gate.

---

## Anti-Pattern 2: Generating Invalid destructiveChanges.xml Syntax

**What the LLM generates:**

```xml
<Package>
    <types>
        <members>Account.Custom_Field__c</members>
        <name>CustomField</name>
    </types>
</Package>
```

Missing the XML declaration, the namespace URI, and the API version element.

**Why it happens:** LLMs frequently omit boilerplate XML elements when generating Metadata API manifests, particularly the `xmlns` namespace and `<version>` tag, which are required for the deploy to succeed.

**Correct pattern:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Account.Custom_Field__c</members>
        <name>CustomField</name>
    </types>
    <version>62.0</version>
</Package>
```

**Detection hint:** Check for missing `xmlns` attribute and missing `<version>` element in any generated Package XML.

---

## Anti-Pattern 3: Conflating Assessment with Execution

**What the LLM generates:** A response that mixes technical debt assessment steps (scanning for dead code, generating a findings report) with cleanup execution steps (deleting fields, deactivating rules) as if they are the same task.

**Why it happens:** "Technical debt" is a broad concept in LLM training data, covering both identification and remediation. In this repo, assessment belongs to `architect/technical-debt-assessment` and execution belongs to this skill. Mixing them produces unfocused, overly long guidance.

**Correct pattern:**

```
If the user asks "what technical debt does my org have?" → route to architect/technical-debt-assessment.
If the user asks "how do I clean up these unused fields?" → use this skill (org-cleanup-and-technical-debt).
If the user has a findings report and asks "now help me fix these" → use this skill.
```

**Detection hint:** If the response includes both "generate a findings report with severity ratings" AND "delete these components," it is conflating two skills.

---

## Anti-Pattern 4: Recommending Deletion of Managed Package Components

**What the LLM generates:** "Delete the unused field `npsp__Donation_Amount__c` from Setup to clean up the data model."

**Why it happens:** LLMs do not distinguish between managed and unmanaged metadata. A field with a namespace prefix (e.g., `npsp__`) belongs to a managed package and cannot be deleted by the subscriber admin.

**Correct pattern:**

```
Fields with a namespace prefix (e.g., npsp__, npe01__, vlocity_cmt__) are managed package
components. They cannot be deleted by the org admin. Options:
- Contact the package publisher to request deprecation in a future release.
- Uninstall the package entirely (warning: deletes all package data).
- Hide the field from page layouts and reports if it is simply clutter.
```

**Detection hint:** Any deletion recommendation for a field or component with a double-underscore namespace prefix (e.g., `prefix__FieldName__c` where prefix is not the org's own namespace) is likely targeting a managed package component.

---

## Anti-Pattern 5: Ignoring the Deleted Fields Queue and Limit Implications

**What the LLM generates:** "Delete 50 unused fields to make room for the new integration fields." — implying that deleting 50 fields immediately frees 50 slots.

**Why it happens:** LLMs do not model Salesforce's 15-day soft-delete queue for custom fields. In most programming contexts, deletion is immediate. Salesforce's recycle behavior is platform-specific and non-obvious.

**Correct pattern:**

```
After deleting fields, they enter a 15-day recycle queue and still count toward the field limit.
To immediately reclaim slots:
1. Go to Setup > Object Manager > [Object] > Fields & Relationships > Deleted Fields.
2. Click "Erase" on each field you want to permanently remove.
3. Erasing is irreversible — the field and its data cannot be recovered.
Only after erasing will the field slot count decrease.
```

**Detection hint:** If cleanup advice claims deleting N fields "frees up N slots" without mentioning the purge/erase step, it is incomplete.

---

## Anti-Pattern 6: Suggesting Apex Code Deletion via Setup Instead of Destructive Deploy

**What the LLM generates:** "Go to Setup > Apex Classes, find the unused class, and delete it."

**Why it happens:** LLMs generalize the Setup deletion path used for declarative metadata (fields, Workflow Rules) to code-based metadata. In production orgs, Apex classes and triggers cannot be deleted through Setup — they can only be removed via a Metadata API destructive deploy.

**Correct pattern:**

```
Apex classes and triggers in production can only be removed via destructive deploy:
1. Create a destructiveChanges.xml listing the ApexClass or ApexTrigger members.
2. Create a minimal package.xml (can be empty of members).
3. Deploy: sf project deploy start --manifest package.xml --post-destructive-changes destructiveChanges.xml --target-org production
Apex CAN be deleted via Setup in sandbox orgs, but not in production.
```

**Detection hint:** Any instruction to delete Apex via Setup in a production org is incorrect. Look for "Setup > Apex Classes > Delete" targeting a production environment.
