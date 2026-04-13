# LLM Anti-Patterns — Insurance Cloud Architecture

Common mistakes AI coding assistants make when generating or advising on Insurance Cloud Architecture.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating FSC InsurancePolicy with Health Cloud MemberPlan

**What the LLM generates:** SOQL or data model designs that mix InsurancePolicy fields with MemberPlan fields, or architecture documents that reference "insurance coverage" using Health Cloud object names like `MemberPlan`, `CoverageBenefit`, or `EligibilityBenefit` for a P&C or life insurance use case.

**Why it happens:** Both products address "insurance" in training data. LLMs surface Health Cloud payer objects when the word "insurance" appears because Health Cloud has more training data coverage than FSC Insurance Cloud.

**Correct pattern:**

```text
FSC Insurance Cloud (P&C / Life): InsurancePolicy, InsurancePolicyCoverage, InsurancePolicyParticipant
Health Cloud Payer: MemberPlan, CoverageBenefit, EligibilityBenefit, InsurancePolicyBenefit (Health-specific)

These are completely separate licensed products with separate APIs and separate object models.
Always confirm: P&C/Life → FSC Insurance Cloud; Health payer → Health Cloud.
```

**Detection hint:** Flag any output that references both `InsurancePolicy` and `MemberPlan` in the same architecture or SOQL. That combination indicates conflation.

---

## Anti-Pattern 2: Assuming All Insurance Modules Are Included in the Base FSC License

**What the LLM generates:** Architecture designs, data model diagrams, or SOQL referencing `Claim`, `ClaimParticipant`, or `InsuranceUnderwritingRule` without noting that these objects require specific separately licensed modules (Claims Management, Policy Administration) beyond the base FSC Insurance Add-On.

**Why it happens:** LLMs are trained on documentation that describes all Insurance Cloud objects without always clarifying per-module licensing gates. The LLM assumes "FSC Insurance" is a single package that unlocks all objects.

**Correct pattern:**

```text
Module to Object Mapping:
- Brokerage Management: InsurancePolicy, InsurancePolicyCoverage, InsurancePolicyParticipant, Producer
- Claims Management: Claim, ClaimParticipant, ClaimCoverage
- Policy Administration: InsuranceUnderwritingRule, Insurance Product Administration APIs
- Group Benefits: GroupPlan, GroupMemberPlan

Always check which modules are licensed before referencing their objects in design documents.
```

**Detection hint:** Any architecture or code that uses `Claim` or `InsuranceUnderwritingRule` without a preceding note about the required module license is a flag.

---

## Anti-Pattern 3: Modeling InsurancePolicyParticipant with a Contact Lookup

**What the LLM generates:** SOQL like `SELECT Id, ContactId FROM InsurancePolicyParticipant` or data model diagrams showing a Contact → InsurancePolicyParticipant relationship.

**Why it happens:** Standard Salesforce relationship modeling uses Contact for person records. LLMs apply this default without knowing that Insurance Cloud uses Account (via PrimaryParticipantAccountId) for participant roles.

**Correct pattern:**

```soql
-- Correct
SELECT Id, PrimaryParticipantAccountId, RoleInPolicy
FROM InsurancePolicyParticipant
WHERE InsurancePolicyId = :policyId

-- Wrong - ContactId does not exist on this object
-- SELECT Id, ContactId FROM InsurancePolicyParticipant
```

**Detection hint:** Any reference to `ContactId` on `InsurancePolicyParticipant` is wrong. The field is `PrimaryParticipantAccountId`.

---

## Anti-Pattern 4: Placing Underwriting Logic in Flow Decision Elements

**What the LLM generates:** Screen Flows with Decision elements that evaluate applicant credit scores, property ages, or coverage limits using Flow formulas, presented as the recommended underwriting architecture.

**Why it happens:** Flow decision tables are the most commonly trained Salesforce automation pattern. LLMs default to what they know when asked for "decision logic."

**Correct pattern:**

```text
Correct architecture:
1. InsuranceUnderwritingRule records with Active/Draft lifecycle for eligibility criteria
2. Insurance Product Administration APIs for rating and policy issuance
3. Integration Procedure calling Insurance APIs (not Flow decisions)
4. OmniScript for UI layer only — collects inputs, displays API results

Flow decision elements for underwriting logic:
- Cannot be audited via Insurance APIs
- Business analysts cannot update without developer involvement
- External rating engines cannot consume Flow decisions
- Do not enforce the InsuranceUnderwritingRule lifecycle
```

**Detection hint:** Architecture that describes underwriting rules "in Flow" or uses Flow Decision elements for eligibility checks should be flagged for review.

---

## Anti-Pattern 5: Synchronous Apex Callouts for Rating Engine Integration

**What the LLM generates:** Apex trigger or before-save code that makes synchronous callouts to external rating engines when an InsurancePolicy or Quote record is saved.

**Why it happens:** Synchronous callouts in Apex are a common integration pattern. LLMs apply this by default without understanding Insurance Cloud governor limits or the prescribed Integration Procedure pattern.

**Correct pattern:**

```apex
// WRONG: synchronous callout in trigger or before-save
trigger InsurancePolicyTrigger on InsurancePolicy (before insert) {
    HttpRequest req = new HttpRequest();
    req.setEndpoint('callout:RatingEngine/rate');
    // ... This violates governor limits and is not restartable
}

// CORRECT: Use OmniStudio Integration Procedure for rating callouts
// Integration Procedures are:
// - Async-safe (can be called from OmniScript without blocking)
// - Chainable (Queueable Chainable for governor-limit-intensive flows)
// - Auditable (IP execution logs)
// - Configurable by administrators without code changes
```

**Detection hint:** Any Apex that makes HTTP callouts for insurance rating or policy issuance should be flagged. The correct pattern is an Integration Procedure with a DataRaptor HTTP action or a dedicated external service callout.
