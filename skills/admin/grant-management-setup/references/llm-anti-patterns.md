# LLM Anti-Patterns — Grant Management Setup

Common mistakes AI coding assistants make when generating or advising on Grant Management Setup.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating NPSP Outbound Funds Module with Nonprofit Cloud for Grantmaking

**What the LLM generates:** Advice that treats `outfunds__Funding_Request__c` (OFM) and `FundingAward` (NC Grantmaking) as equivalent or interchangeable, or that provides OFM-specific setup steps to an org running NC Grantmaking (or vice versa).

**Why it happens:** Training data contains documentation for both platforms, and the LLM pattern-matches "grant management" to whichever platform has more coverage in context. Both are Salesforce nonprofit grant tools, so the LLM conflates them as versions of the same product.

**Correct pattern:**
```
Always determine which platform the org is running BEFORE providing any object-level guidance:
- NPSP org (outfunds namespace installed): use OFM objects — outfunds__Funding_Request__c, outfunds__Disbursement__c
- Nonprofit Cloud org with Grantmaking license: use NC objects — FundingAward, FundingDisbursement, FundingAwardRequirement
Never mix API names from both platforms in a single answer.
```

**Detection hint:** If the response references both `outfunds__` namespace objects AND `FundingAward` / `FundingDisbursement`, the platforms are being conflated. Flag and correct before delivering to the user.

---

## Anti-Pattern 2: Recommending Outbound Funds Module Objects When the Org Uses Nonprofit Cloud for Grantmaking

**What the LLM generates:** SOQL queries, Flow references, or configuration steps that use `outfunds__Funding_Request__c`, `outfunds__Disbursement__c`, or `outfunds__Funding_Program__c` for an org that is on Nonprofit Cloud for Grantmaking.

**Why it happens:** OFM has a longer documented history in Salesforce nonprofit content, so the LLM defaults to OFM vocabulary even when the org context specifies Nonprofit Cloud.

**Correct pattern:**
```
For Nonprofit Cloud for Grantmaking orgs:
- Award record: FundingAward (not outfunds__Funding_Request__c)
- Payment tranche: FundingDisbursement (not outfunds__Disbursement__c)
- Deliverable: FundingAwardRequirement (no OFM equivalent)
- SOQL: SELECT Id, Name, AwardAmount__c FROM FundingAward WHERE Status = 'Active'
  NOT: SELECT Id, Name FROM outfunds__Funding_Request__c
```

**Detection hint:** Any response containing `outfunds__` namespace prefixes for an org confirmed to be on Nonprofit Cloud for Grantmaking is incorrect. Search response for `outfunds__` and flag if present in an NPC context.

---

## Anti-Pattern 3: Treating FundingDisbursement as a Single Total Payment Instead of Tranches

**What the LLM generates:** Instructions to create one FundingDisbursement record per FundingAward to record the total payment, or guidance to create FundingDisbursement records only after payment has been sent rather than at award setup time.

**Why it happens:** The word "disbursement" in financial contexts often means a single payment event. The LLM applies this accounting-system semantics to FundingDisbursement without recognizing it is designed as a scheduled tranche planning object, not a payment ledger.

**Correct pattern:**
```
FundingDisbursement = one record per planned payment tranche, created at award setup:
- One FundingAward can have many FundingDisbursements
- Create all disbursement tranches upfront with Status = Draft or Scheduled
- Update Status to Paid when the payment is sent
- Do NOT create a single FundingDisbursement for the total award amount
```

**Detection hint:** If the response instructs creating exactly one FundingDisbursement per FundingAward, or recommends creating disbursements retroactively after payment, the tranche model is being misapplied.

---

## Anti-Pattern 4: Omitting the Licensing Requirement for Nonprofit Cloud for Grantmaking

**What the LLM generates:** Instructions to configure FundingAward, FundingDisbursement, or FundingAwardRequirement in a Nonprofit Cloud org without mentioning that these objects require the Grantmaking product license — a separately purchased add-on.

**Why it happens:** LLMs typically do not track licensing requirements unless explicitly trained on them. The model generates technically correct configuration steps but omits the prerequisite that the objects will not exist without the license.

**Correct pattern:**
```
Before any NC Grantmaking configuration step, verify:
1. Navigate to Setup → Company Information → Permission Set Licenses
2. Confirm "Nonprofit Cloud for Grantmaking" license is listed and has available allocations
3. If absent: do not proceed with FundingAward configuration — the objects are inaccessible
4. Escalate to Salesforce Account Executive to add the Grantmaking license if needed
```

**Detection hint:** Any response that provides FundingAward configuration steps without a licensing verification step is incomplete. Check whether the response includes license verification before declaring it production-ready.

---

## Anti-Pattern 5: Assuming Migration from OFM to NC Grantmaking Is a Configuration Change

**What the LLM generates:** A "migration plan" that treats moving from NPSP Outbound Funds Module to Nonprofit Cloud for Grantmaking as a straightforward data export/import or configuration toggle, without accounting for the architectural incompatibility between the two data models.

**Why it happens:** Migrations between Salesforce features are sometimes handled by package upgrades or configuration changes. The LLM pattern-matches "migration" to this lighter-weight mental model and underestimates the transformation required.

**Correct pattern:**
```
OFM → NC Grantmaking migration requires a full data transformation project:
1. Map outfunds__Funding_Request__c → FundingAward (field-by-field)
2. Map outfunds__Disbursement__c → FundingDisbursement (field-by-field)
3. Build net-new FundingAwardRequirement records (no OFM source — these must be created)
4. Rebuild all Flows, reports, list views, and validation rules using NC API names
5. Re-train grants staff on the new data model and UI
6. Decommission OFM package only after full validation

There is no "upgrade" toggle. This is a data migration and re-implementation project.
```

**Detection hint:** If the response uses phrases like "simply export and import," "upgrade the package," or "map the fields over" without acknowledging full automation rebuilds, it is understating the migration complexity. Flag any migration guidance that omits the need to rebuild Flows and automation.
