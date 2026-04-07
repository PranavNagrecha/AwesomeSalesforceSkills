# LLM Anti-Patterns — FSC Referral Management

Common mistakes AI coding assistants make when generating or advising on FSC Referral Management.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Confusing Einstein Referral Scoring (Retiring) with Intelligent Need-Based Referrals (Active)

**What the LLM generates:** Guidance telling the user to enable "Einstein Referral Scoring" in FSC Settings, configure the Einstein scoring model, or rely on Einstein-generated referral scores as a current feature.

**Why it happens:** Training data contains substantial Salesforce Trailhead and blog content published before the Einstein Referral Scoring retirement announcement. The two features have similar names and overlapping functionality, making them easy to conflate. The LLM weights older, more common training references over the retirement notice.

**Correct pattern:**

```
Use Intelligent Need-Based Referrals as the scoring mechanism.
ReferrerScore__c (0-100) on the Lead record reflects the
platform-calculated historical conversion rate under this feature.

Do NOT configure Einstein Referral Scoring — it has been announced
for retirement. Reference: Salesforce Help — Referral Scoring Feature
for Financial Services Retirement Notice.
```

**Detection hint:** Look for phrases like "enable Einstein Referral Scoring", "Einstein scoring model for FSC", or "Einstein referral score threshold". Any of these indicate the retiring feature is being referenced.

---

## Anti-Pattern 2: Omitting ReferralRecordTypeMapping Custom Metadata When Adding a New Referral Type

**What the LLM generates:** Instructions to create a Lead record type and update Lead Assignment Rules, with no mention of creating a `ReferralRecordTypeMapping__mdt` entry. The guidance treats Assignment Rules as the only routing mechanism.

**Why it happens:** LLMs trained on general Salesforce Lead routing knowledge default to the standard Lead routing model (record type + Assignment Rules). The FSC-specific custom metadata gate is not mentioned in standard Salesforce documentation and only appears in FSC-specific sources that may be underrepresented in training data.

**Correct pattern:**

```
To add a new referral type in FSC, all three steps are required:
1. Create the Lead record type
2. Create an active ReferralRecordTypeMapping__mdt record with
   LeadRecordTypeDeveloperName__c matching the record type developer name
3. Create Lead Assignment Rule entries keyed on Expressed Interest values

Skipping step 2 causes routing to silently fail with no error.
```

**Detection hint:** If generated instructions for adding a referral type mention Lead record type and Assignment Rules but do not mention `ReferralRecordTypeMapping`, the metadata step has been omitted.

---

## Anti-Pattern 3: Treating ReferredBy__c as Always a User Lookup

**What the LLM generates:** SOQL queries such as `SELECT Id, ReferredBy__c, ReferredBy__r.Name FROM Lead WHERE ...`, Flow logic that uses `{!Lead.ReferredBy__r.FirstName}` assuming a User, or page layout instructions that link the referrer field to a User record only.

**Why it happens:** In the standard Salesforce data model, most "referred by" or "created by" fields resolve to User records. LLMs trained on standard Salesforce patterns default to this assumption. The FSC Contact-based partner referral credit model is a domain-specific exception that counters the standard assumption.

**Correct pattern:**

```
ReferredBy__c is a polymorphic lookup that resolves to:
- User — for internal referrers (employees, advisors)
- Contact — for external partner referrers

SOQL must handle both:
SELECT Id, ReferredBy__c, ReferredBy__r.Name, ReferredBy__r.Type
FROM Lead
WHERE ReferredBy__c != null

Check ReferredBy__r.Type to determine if the referrer is a
User or Contact before accessing type-specific fields.
```

**Detection hint:** Look for `ReferredBy__r.UserRole`, `ReferredBy__r.Username`, or any query/flow that assumes `ReferredBy__c` resolves only to User without a type check.

---

## Anti-Pattern 4: Assuming Referrer Score Is Editable or Can Be Set via Automation

**What the LLM generates:** Flow or Apex code that attempts to set `ReferrerScore__c` on a Lead record via `lead.ReferrerScore__c = someValue;`, or instructions to create a Flow that updates this field as part of a referral closure process.

**Why it happens:** `ReferrerScore__c` looks like a standard numeric field. LLMs default to treating numeric fields as writable. The platform-managed, read-only nature of this specific field is a FSC-specific constraint not indicated by the field name or type.

**Correct pattern:**

```
ReferrerScore__c is a read-only field calculated and managed by
the FSC platform based on historical referral conversion data.

Do NOT attempt to set this field via Flow, Apex, or data load.
The platform will overwrite any value written to it.

To surface custom scoring, create a separate custom field
(e.g. CustomReferralScore__c) and build scoring logic there.
```

**Detection hint:** Look for `ReferrerScore__c` on the left side of an assignment operator in Apex, or as an "Update Records" field in a Flow. Either indicates an attempted write to a read-only field.

---

## Anti-Pattern 5: Relying on Lead Assignment Log Absence as Proof of Correct Routing

**What the LLM generates:** Validation instructions that say "if no errors appear in the Lead Assignment Log, routing is working correctly." Or test plans that check only for absence of errors rather than confirming a specific queue assignment was made.

**Why it happens:** In standard Salesforce, the Lead Assignment Log surfaces routing failures. LLMs trained on general Lead routing patterns assume that no log entry means routing succeeded. In FSC Referral Management, silent routing failure (due to missing `ReferralRecordTypeMapping__mdt`) does not generate a log entry — it simply skips routing entirely with no trace.

**Correct pattern:**

```
Do not use absence of errors as proof of successful routing.

For each test referral, explicitly verify:
1. The Lead.OwnerId has changed from the creating user to the target queue
2. The Lead Assignment Log shows a routing decision entry (not just no error)
3. The queue's list view contains the test referral record

If the Lead.OwnerId is still the creating user and the Assignment Log
is empty, the ReferralRecordTypeMapping__mdt entry is likely missing.
```

**Detection hint:** Test plans or validation steps that only check for the absence of errors or use phrases like "if no errors appear, the routing is configured correctly" are applying this anti-pattern.
