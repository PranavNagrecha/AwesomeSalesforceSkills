# Examples — FSC Referral Management

## Example 1: Adding a New Referral Type for a New Business Line

**Context:** A financial institution is adding Small Business Lending as a new referral category. Advisors will submit referrals from the FSC app. The team creates a Lead record type `SmallBusinessLending` and a queue but skips the custom metadata step.

**Problem:** After deployment, advisors create referrals using the new record type and select Expressed Interest values. The referrals appear in the system with no errors, but the Small Business Lending queue never receives any assignments. The queue stays empty. No error is surfaced on the Lead record or in setup logs.

**Solution:**

```xml
<!-- ReferralRecordTypeMapping__mdt record (deployed as custom metadata) -->
<!-- File: force-app/main/default/customMetadata/ReferralRecordTypeMapping.SmallBusinessLending.md-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <label>Small Business Lending</label>
    <protected>false</protected>
    <values>
        <field>LeadRecordTypeDeveloperName__c</field>
        <value xsi:type="xsd:string">SmallBusinessLending</value>
    </values>
    <values>
        <field>IsActive__c</field>
        <value xsi:type="xsd:boolean">true</value>
    </values>
</CustomMetadata>
```

After deploying this metadata record, create Lead Assignment Rule entries that filter on `Expressed Interest` picklist values for SBA Loan and Business Line of Credit, routing to the Small Business Lending queue. Test by creating a referral and reviewing the Lead Assignment Log on the record.

**Why it works:** `ReferralRecordTypeMapping__mdt` is the gate the FSC platform checks before initiating any routing logic. Without an active entry for the Lead record type developer name, the platform treats the record as a non-referral Lead and skips all referral routing — silently.

---

## Example 2: Surfacing Referrer Score for External Partners in Experience Cloud

**Context:** A wealth management firm has financial advisors who are external partners submitting referrals through an Experience Cloud community. Advisors want to see their Referrer Score (0–100) to understand how their referral conversion history is performing. After enabling Referral Management, the score is invisible to community users despite the data being populated.

**Problem:** `ReferrerScore__c` is populated on the Lead record, but it does not appear on the Experience Cloud referral detail page for the community profile. The partner advisor logs in and sees no score field at all. Granting access in the profile alone does not fix it.

**Solution:**

Step 1 — Grant field-level security for the community profile:
```
Setup > Object Manager > Lead > Fields & Relationships > ReferrerScore__c
> Set Field-Level Security > [Community Profile] > Read Access = Enabled
```

Step 2 — Add the field to the Experience Builder page:
```
Experience Builder > [Partner Community Site] > Pages > Referral Detail
> Edit page layout > Add field: ReferrerScore__c
> Label: "Your Referrer Score"
> Save and Publish
```

Step 3 — Verify that ReferredBy__c on the referral points to the partner's Contact record (not User). Partner referrals credit Contact records by FSC platform design. If the lookup is empty, the score field will render but show blank.

**Why it works:** FSC credits partner referrals to Contact records rather than User records. `ReferrerScore__c` is a read-only field that is absent from all default Experience Cloud page layouts — it must be placed explicitly. FLS is also required because the field's default FLS for community profiles is often read-restricted.

---

## Anti-Pattern: Treating Lead Assignment Rule Routing as Sufficient Without Metadata Registration

**What practitioners do:** A team sets up Lead Assignment Rules with multiple `Expressed Interest` criteria entries pointing to the appropriate queues. They test the rules using the "Run Rules" button in setup and observe the routing logic is correct. They skip creating `ReferralRecordTypeMapping__mdt` entries under the assumption that the Assignment Rules are all that is needed.

**What goes wrong:** When referrals are submitted through the FSC interface, the `ReferralRecordTypeMapping__mdt` lookup fails to find an active entry for the record type. FSC skips the referral routing pipeline entirely. The Lead Assignment Rules never evaluate. Referrals accumulate unassigned. No system error is generated. The team observes the problem only when business stakeholders report that no referrals are appearing in queues.

**Correct approach:** Always create the `ReferralRecordTypeMapping__mdt` entry first, deploy it, then add the Assignment Rule entries. The metadata entry is the prerequisite gate; the Assignment Rule is the routing logic. Both must be in place for routing to work end-to-end.
