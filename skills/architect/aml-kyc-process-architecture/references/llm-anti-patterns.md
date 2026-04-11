# LLM Anti-Patterns — AML/KYC Process Architecture

Common mistakes AI coding assistants make when generating or advising on AML/KYC process architecture on Salesforce. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending FSC Identity Verification as the AML Screening Mechanism

**What the LLM generates:** Guidance that says to "enable FSC Identity Verification" in Setup and configure it as the KYC check during onboarding. The LLM may describe the verification flow in detail and present it as satisfying KYC requirements.

**Why it happens:** "Identity Verification" sounds like KYC identity verification. Training data conflates these terms because both involve confirming a person's identity. FSC Identity Verification is a prominent FSC feature, so it appears frequently in FSC documentation and examples.

**Correct pattern:**

```
FSC Identity Verification = contact-center caller authentication only
  - Confirms caller identity against data already in Salesforce (security questions, DOB, SSN last 4)
  - No connection to OFAC, UN, EU, or any other sanctions list
  - No PEP screening
  - Does NOT satisfy AML program screening requirements

AML/KYC screening requires:
  - Integration to a dedicated third-party screening vendor
    (Refinitiv World-Check, LexisNexis Bridger, Accuity/Fircosoft, etc.)
  - Vendor maintains current sanctions lists and PEP databases
  - Salesforce orchestrates the call; it does not perform the screening
```

**Detection hint:** Any response that mentions "Identity Verification" as part of an AML screening architecture without also specifying a third-party screening vendor is likely wrong.

---

## Anti-Pattern 2: Placing a Synchronous Vendor Callout Inside a Record-Triggered Flow

**What the LLM generates:** A record-triggered Flow design where the flow calls an Apex action or Integration Procedure that makes an HTTP callout to the screening vendor on every Account creation or update.

**Why it happens:** Record-triggered flows are the most common Salesforce automation pattern. LLMs default to them for "trigger something when a record is saved" requirements. The callout-in-bulk-context restriction is a non-obvious platform behavior not prominently documented in introductory content.

**Correct pattern:**

```
Wrong:
  Record-Triggered Flow (Account: After Save)
    └─ Action: Call ScreeningVendorAction (makes HTTP callout) ← fails in bulk context

Correct option A — deferred via Platform Event:
  Record-Triggered Flow (Account: After Save)
    └─ Action: Publish Platform Event: ScreeningRequest__e
  Platform Event Trigger
    └─ Action: Call ScreeningVendorAction (Queueable Apex with callout)

Correct option B — user-initiated via OmniScript:
  OmniScript step: "Screening"
    └─ Integration Procedure: calls vendor REST API (not record-save-triggered)
```

**Detection hint:** Look for a record-triggered Flow with a direct callout action (HTTP callout, external service invocation, Integration Procedure that makes a callout) in the same transaction path as the record save.

---

## Anti-Pattern 3: Recommending the Industries Scoring Framework as the AML Risk Engine

**What the LLM generates:** Architecture guidance that recommends using the "FSC Scoring Framework" or "Industries Scoring Framework" to produce AML customer risk ratings, describing it as the Salesforce-native risk scoring solution for financial services.

**Why it happens:** The Industries Scoring Framework is a real FSC feature and is documented as producing risk scores for financial services use cases. LLMs trained on marketing and product documentation may not distinguish between "propensity score for sales prioritization" and "regulatory risk rating for AML compliance."

**Correct pattern:**

```
Industries Scoring Framework / FSC Scoring Framework:
  - Purpose: propensity scoring for sales/marketing (likelihood to buy, churn risk)
  - Engine: CRM Analytics models
  - Licensing: requires CRM Analytics Plus license
  - Regulatory explainability: NOT designed for regulatory audit
  - Correct use: customer segmentation, next-best-action, sales prioritization

AML risk scoring:
  - Purpose: regulatory customer risk rating (Low/Medium/High/Prohibited)
  - Correct implementation: custom rule-based Apex class writing to PartyProfileRisk
  - Inputs: screening result + geography + customer type + product type
  - Output: RiskCategory picklist value + RiskScore + RiskReason (audit field)
  - Regulatory explainability: rule-based logic is auditable and explainable
```

**Detection hint:** Any response recommending CRM Analytics or the "Scoring Framework" as the primary AML risk rating mechanism without noting the regulatory explainability gap is likely wrong.

---

## Anti-Pattern 4: Using Per-User Named Credentials for Batch Screening

**What the LLM generates:** A Named Credential configuration with "Per-User" (OAuth user-agent) authentication for the screening vendor, then using this Named Credential in a scheduled batch job or `@future` method.

**Why it happens:** Per-User Named Credentials are commonly recommended for integrations where each API call should be made on behalf of the logged-in user. LLMs apply this pattern broadly without accounting for the session-requirement behavior in async contexts.

**Correct pattern:**

```
Per-User Named Credential:
  - Requires active user session to resolve OAuth token
  - Works for: interactive user actions (OmniScript, LWC, Flow triggered by user)
  - FAILS for: Schedulable Apex, Database.Batchable, @future, Platform Event triggers,
               Queueable Apex spawned from non-interactive context

Named Principal Named Credential (correct for batch AML screening):
  - Authenticates as a service account / integration identity
  - Works for: all async and scheduled Apex contexts
  - Configuration: External Credential with Named Principal policy,
                   client credentials OAuth flow or API key header
  - Required for: any AML screening that runs in scheduled or batch context
```

**Detection hint:** Any batch or scheduled Apex design using a Named Credential — check whether the Named Credential policy is Per-User. If it is, flag it as a runtime failure waiting to happen.

---

## Anti-Pattern 5: Omitting Audit Trail and Override Logging from the Architecture

**What the LLM generates:** An AML/KYC architecture design that covers the screening integration and risk rating update but does not specify how screening decisions, risk category changes, and manual compliance overrides are logged. The design assumes that the `LastModifiedDate` on `PartyProfileRisk` is sufficient for audit purposes.

**Why it happens:** Audit trail requirements are non-functional requirements not typically present in a user story. LLMs focus on the functional flow (screen → rate → route) and omit audit logging because it is not part of the happy-path description.

**Correct pattern:**

```
Audit trail requirements for AML/KYC:
  1. Screening request log
     - Timestamp of request
     - Customer identifier
     - Vendor case reference number
     - Data sent to vendor (name, DOB, ID — hashed or encrypted at rest)

  2. Screening result log
     - Timestamp of result
     - Match status returned by vendor
     - Risk score returned by vendor
     - Resulting RiskCategory assigned

  3. Risk category change log (custom AuditLog__c or Shield Field Audit Trail)
     - Previous RiskCategory (before value)
     - New RiskCategory (after value)
     - Changed by (user or system)
     - Change reason

  4. Manual override log
     - Override by (user ID)
     - Override timestamp
     - Justification text (required field — compliance officer must document reason)
     - Approver (if dual-control required by policy)

Standard PartyProfileRisk field history (18-month platform limit) is NOT sufficient
for regulators who may examine records going back 5–7 years. Assess whether
Shield Field Audit Trail is required to extend retention.
```

**Detection hint:** Any AML architecture design that does not specify a custom audit log object or Shield Field Audit Trail for `PartyProfileRisk` changes is likely incomplete for regulatory purposes.

---

## Anti-Pattern 6: Assuming the Vendor Managed Package Object Model Is the Same as FSC's

**What the LLM generates:** Architecture guidance that mixes the screening vendor's managed package objects (e.g., `wchk__Case__c`, `lnbi__Screening__c`) with FSC's standard objects (`PartyProfileRisk`, `Individual`) as if they are natively connected or interchangeable.

**Why it happens:** LLMs may have been trained on vendor-specific integration documentation alongside FSC documentation and conflate the two object models. The vendor package objects store screening-vendor-specific data; the FSC objects store the Salesforce-side risk rating. These are distinct layers.

**Correct pattern:**

```
Layer 1 — Vendor Package Objects (if vendor provides a managed package):
  - wchk__Case__c (Refinitiv) or vendor equivalent
  - Stores: raw screening result, vendor match details, vendor case status
  - Owned by: vendor package; do not add custom fields here

Layer 2 — FSC Objects (Salesforce standard):
  - PartyProfileRisk: stores the institution's regulatory risk rating
  - Individual: person record owning the PartyProfileRisk
  - These are populated by a mapping step AFTER the vendor result is received

The architecture must explicitly design the mapping layer between Layer 1 and Layer 2.
This is typically an Apex class or DataRaptor Transform that reads the vendor result
and writes the derived risk rating to PartyProfileRisk.

Never reference vendor package objects from FSC standard flows or standard page layouts
without going through the mapping layer — this creates a tight coupling that breaks
when the vendor package is upgraded.
```

**Detection hint:** Any architecture diagram or description that shows a direct relationship between vendor package objects and `PartyProfileRisk` without an explicit mapping step is likely incorrect.
