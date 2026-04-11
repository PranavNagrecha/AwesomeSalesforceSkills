# Examples — AML/KYC Process Architecture

## Example 1: Real-Time Sanctions Screening in a Guided FSC Onboarding Flow

**Context:** A regional bank using FSC and OmniStudio onboards retail customers through a guided agent-facing OmniScript. The bank's compliance program requires a sanctions screening check (OFAC, UN, EU lists) to complete before the Account can be activated. The screening vendor (Refinitiv World-Check) exposes a synchronous REST API with a p95 response time under 3 seconds.

**Problem:** The initial implementation triggered an Apex callout from a record-triggered Flow on Account creation. This caused two production issues: (1) bulk data imports failed with a callout-in-bulk-context error, and (2) when the vendor API was slow, the Account record save timed out and the customer lost their partially completed onboarding data. The compliance team also lacked visibility into screening results — there was no record of what was sent to the vendor or what was returned.

**Solution:**

The architecture was redesigned around OmniStudio with an Integration Procedure handling the vendor call:

```text
OmniScript Step 3: "Identity Verification and Screening"
  └─ Invoke Integration Procedure: SFFS_ScreenCustomer_IP
       ├─ HTTP Action: POST /worldcheck/v1/cases
       │    Named Credential: WorldCheck_NC (Org-Wide auth)
       │    Request: { name, dateOfBirth, nationality, idNumber }
       │    Timeout: 8000ms
       ├─ DataRaptor Transform: Map vendor response to staging fields
       │    vendorCaseRef  → ScreeningCaseRef__c (on Account)
       │    matchStatus    → ScreeningStatus__c (Clear / PotentialMatch / ConfirmedMatch)
       │    matchScore     → ScreeningScore__c
       └─ DML Action: Upsert PartyProfileRisk
            RiskCategory    = derived from matchStatus (Clear→Low, PotentialMatch→High)
            RiskScore       = vendor matchScore
            RiskReason      = "Initial sanctions screening via World-Check"
            RiskReviewDate  = TODAY() + 365

OmniScript branching logic:
  If ScreeningStatus__c = "Clear"       → advance to Account Activation step
  If ScreeningStatus__c = "PotentialMatch" → route to Compliance Review Queue
  If ScreeningStatus__c = "ConfirmedMatch" → block; open High-Priority Case; notify compliance officer
```

**Why it works:** Moving the vendor call into an Integration Procedure decouples it from the record-save transaction entirely. The OmniScript controls the timing — the call only happens when a human agent reaches the screening step, not on every Account save. The vendor response is captured in full on `PartyProfileRisk` before the OmniScript advances, creating an audit trail. Named Credentials keep the vendor endpoint and API key out of code or metadata accessible to standard users.

---

## Example 2: Asynchronous Periodic Re-Screening of an Existing Portfolio

**Context:** A wealth management firm using FSC has 80,000 individual clients. Regulatory requirements mandate annual re-screening of the full portfolio plus immediate re-screening when a client's country of residence changes. The screening vendor (LexisNexis Bridger Insight) has a REST API but is rate-limited at 20 requests per second.

**Problem:** An initial attempt to build this in a scheduled Flow failed because Flow does not support direct callouts at the volume required, and the vendor rate limit made a fully synchronous approach unworkable. The compliance team needed a record of each re-screening event including the request timestamp, response, and any change in risk category — a requirement that a simple field update on the Account could not satisfy.

**Solution:**

```text
Architecture: Scheduled Batch Apex + Platform Events + Flow Subscriber

1. Scheduled Batch Apex: SFFS_AMLRescreening_Batch (runs nightly)
   - Query: SELECT Id, Individual__c, Name, ... FROM Account
             WHERE Individual__r.PartyProfileRisk__r.RiskReviewDate <= TODAY()
             AND RecordType.DeveloperName = 'IndividualClient'
   - Implements: Database.Batchable, Database.AllowsCallouts
   - Batch size: 10 (keeps callout volume within per-execute limits)
   - Per record in execute():
       a. Call LexisNexis REST API (Named Credential: LexisNexis_NC, Named Principal auth)
       b. On success: publish ScreeningResult__e Platform Event
            Fields: AccountId__c, VendorCaseRef__c, MatchStatus__c,
                    RiskScore__c, ScreeningTimestamp__c
       c. On HTTP error: publish ScreeningError__e Platform Event for dead-letter handling

2. Platform Event Trigger (Apex): SFFS_ScreeningResult_Trigger
   - Subscribes to ScreeningResult__e
   - For each event:
       a. Query existing PartyProfileRisk for the Account's Individual
       b. Only update if event.ScreeningTimestamp__c > PartyProfileRisk.LastModifiedDate
          (prevents out-of-order event overwrite)
       c. Update PartyProfileRisk: RiskCategory, RiskScore, RiskReason, RiskReviewDate
       d. If RiskCategory changed: create AuditLog__c record (custom) with before/after values
       e. If new RiskCategory = 'High' or 'Prohibited': create Case, assign to Compliance Queue

3. Rate-limit throttling:
   - Batch execute() method checks a Custom Metadata record for the current
     LexisNexis rate limit (default: 20 req/sec)
   - Uses a simple counter in the batch state to stay within limits
```

**Why it works:** Separating the callout (batch) from the DML (Platform Event subscriber) is the only governor-limit-safe pattern at this volume. The timestamp guard on the subscriber prevents the rare but real scenario where two batch runs overlap and the older run's event arrives after the newer run's event. The custom `AuditLog__c` record creates a durable history of every re-screening and every risk category change — essential for regulatory examination.

---

## Anti-Pattern: Using FSC Identity Verification as a Sanctions Check

**What practitioners do:** Configure FSC Identity Verification (Setup > Identity Verification) and present it to the compliance team as the AML/KYC screening mechanism. They route the onboarding Flow through the Identity Verification step and mark "KYC screening complete" when the step passes.

**What goes wrong:** FSC Identity Verification authenticates a caller's identity by comparing answers to questions (security questions, date of birth, last four of SSN) against data already stored in Salesforce. It does not perform any of the following actions that AML regulations require:

- It does not check the customer's name against OFAC, UN, or EU sanctions lists.
- It does not screen for Politically Exposed Person (PEP) status.
- It does not perform adverse media screening.
- It does not assign a regulatory risk category.

A financial institution that relies on FSC Identity Verification as its AML screening mechanism has no sanctions screening program and faces regulatory enforcement risk.

**Correct approach:** Use FSC Identity Verification only for its intended purpose: confirming a caller's identity in a contact-center context. AML/KYC screening requires a separate integration to a dedicated screening vendor (Refinitiv, Accuity, LexisNexis, etc.) that maintains current sanctions lists and PEP databases. Design this integration using the patterns in this skill.
