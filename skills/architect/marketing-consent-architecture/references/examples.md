# Examples — Marketing Consent Architecture

## Example 1: Discovering the MC-to-CRM Writeback Gap During a GDPR Audit

**Context:** A B2C retail company has used Marketing Cloud for three years connected to their Salesforce CRM. They have never had a formal consent architecture review. An internal GDPR audit finds that the CRM Contact records show `HasOptedOutOfEmail = false` for contacts who clearly unsubscribed from MC emails over the past year.

**Problem:** The company assumed that because MC is connected to CRM via Marketing Cloud Connect, unsubscribes would automatically sync to the CRM. They did not know that MC All Subscribers `HasOptedOutOfEmail` is a separate field from `Individual.HasOptedOutOfEmail` and that no writeback is configured. The CRM is legally inaccurate: it implies consent exists when the subscriber has exercised their right to opt out. Any non-MC channel (direct mail, CS email, partner sends) using the CRM opt-out field would be sending to opted-out individuals.

**Solution:**

The architect designs a remediation plan in three phases:

**Phase 1 — Immediate suppression:** Export all MC All Subscribers records with `HasOptedOutOfEmail = true`. Bulk-load these into CRM as ContactPointTypeConsent records with `PrivacyConsentStatus = OptOut`, `ContactPointType = Email`, and a `DataUsePurpose` record created for "Email Marketing". Set `CaptureSource = MCUnsubscribe` and `CaptureDate` from the MC unsubscribe date.

**Phase 2 — Enable writeback:** In the MC connector configuration, enable Consent Management and configure the writeback so future MC unsubscribes create or update ContactPointTypeConsent records in CRM within the integration's sync window (typically near-real-time via outbound messaging or hourly batch).

**Phase 3 — Validate:** Run a reconciliation query weekly for one month comparing MC All Subscribers opted-out count to CRM ContactPointTypeConsent OptOut count for the Email Marketing purpose. Alert if they diverge by more than a threshold.

```sql
-- SOQL: Find Contacts with no matching OptOut consent record
-- Run after bulk load to validate coverage
SELECT c.Id, c.Email, c.Individual.HasOptedOutOfEmail
FROM Contact c
WHERE c.Individual.HasOptedOutOfEmail = true
  AND c.Id NOT IN (
    SELECT cptc.IndividualId
    FROM ContactPointTypeConsent cptc
    WHERE cptc.ContactPointType = 'Email'
      AND cptc.PrivacyConsentStatus = 'OptOut'
  )
LIMIT 200
```

**Why it works:** The SOQL query surfaces the gap between the Individual boolean (a coarse flag) and the platform consent objects (the auditable record). Fixing the writeback ensures future divergence is caught at the integration layer, not during an audit.

---

## Example 2: Per-Purpose Consent Architecture for a Financial Services Org

**Context:** A financial services company sends two types of email: transactional (account statements, fraud alerts — lawful basis: contract performance) and marketing (product offers — lawful basis: consent). Under GDPR Article 6, withdrawing marketing consent does not affect transactional sends that are lawful under a different basis. The current architecture uses a single `HasOptedOutOfEmail` boolean, which means a marketing opt-out suppresses transactional sends too — a compliance and customer experience failure.

**Problem:** The org cannot distinguish between a subscriber who withdrew marketing consent (should still receive account statements) and one who has exercised a broader right to erasure or restriction. Both end up fully suppressed, causing legitimate transactional emails to bounce and creating customer escalations.

**Solution:**

The architect designs a two-purpose consent model:

1. Create two Data Use Purpose records in CRM:
   - "Email Marketing" — LegalBasis = Consent, LegalBasisSource = "Web preference center opt-in"
   - "Email Transactional" — LegalBasis = ContractPerformance, LegalBasisSource = "Customer Agreement Terms"

2. For each Individual, create two ContactPointTypeConsent records (one per purpose):
   - Individual → ContactPointTypeConsent (Email + Email Marketing + OptIn/OptOut)
   - Individual → ContactPointTypeConsent (Email + Email Transactional + OptIn)

3. In Marketing Cloud, configure two Send Classifications:
   - Marketing sends → mapped to "Email Marketing" Data Use Purpose
   - Transactional sends → mapped to "Email Transactional" Data Use Purpose

4. When a subscriber opts out of marketing email, only the Email Marketing ContactPointTypeConsent record is updated to OptOut. The Email Transactional record remains OptIn. MC reads the correct record at send time based on the journey's mapped purpose.

```
Data Use Purpose: Email Marketing
  LegalBasis: Consent
  ContactPointTypeConsent.PrivacyConsentStatus: OptOut (after unsubscribe)

Data Use Purpose: Email Transactional
  LegalBasis: ContractPerformance
  ContactPointTypeConsent.PrivacyConsentStatus: OptIn (unchanged)
```

**Why it works:** The ContactPointTypeConsent model supports multiple records per Individual per channel, each scoped to a distinct purpose. MC's Consent Management integration reads the record matching the send's configured Data Use Purpose, so transactional sends are evaluated against the transactional consent record only. This is a correct implementation of GDPR's per-purpose lawful basis requirement.

---

## Anti-Pattern: Using MC All Subscribers as the Consent System of Record

**What practitioners do:** They treat MC All Subscribers `HasOptedOutOfEmail` as the authoritative consent record and do not create or maintain CRM consent objects. They may sync this field to a custom checkbox on Contact (`MC_Opted_Out__c`) but do not use Individual, ContactPointTypeConsent, or ContactPointConsent.

**What goes wrong:**
- No per-purpose tracking: a marketing opt-out suppresses all emails including legally-required transactional sends.
- No audit trail: MC subscriber data does not carry CaptureDate, CaptureSource, or DataUsePurpose in a queryable CRM form. Responding to a GDPR Article 15 access request requires manual MC exports.
- No integration with CRM-driven sends: if another team sends emails directly from CRM (via Apex, Flow, or OmniChannel), the MC opt-out is invisible to those sends.
- Custom checkbox drift: the custom field on Contact quickly drifts from the MC subscriber record because there is no bidirectional sync enforcing consistency.

**Correct approach:** Use CRM consent objects (Individual, ContactPointTypeConsent) as the system of record. Enable MC Consent Management integration so MC reads CRM at send time. Build a writeback so MC unsubscribes update CRM records. Retire custom consent checkboxes in favor of the platform model.
