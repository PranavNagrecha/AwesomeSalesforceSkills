# LLM Anti-Patterns — NPSP Custom Rollups (CRLP)

Common mistakes AI coding assistants make when generating or advising on NPSP Customizable Rollups.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Suggesting CRLP Can Be Disabled After Enabling

**What the LLM generates:** Instructions like "if you want to revert to legacy NPSP rollups, disable CRLP under NPSP Settings" or "you can always turn off CRLP if it doesn't work out."

**Why it happens:** LLMs pattern-match on generic toggle/feature semantics and assume any feature that can be enabled can be disabled. The irreversibility of the CRLP migration is a domain-specific constraint not well represented in general training data.

**Correct pattern:**

```
Enabling CRLP is a one-way migration. Once enabled, legacy user-defined rollup
configurations are permanently removed. There is no revert path. Always audit
dependencies before enabling and treat the migration as irreversible.
```

**Detection hint:** Look for phrases like "disable CRLP," "revert to legacy rollups," "turn off customizable rollups," or "undo the migration." All of these are incorrect — CRLP cannot be disabled after enabling.

---

## Anti-Pattern 2: Treating CRLP Rollup Fields as Real-Time

**What the LLM generates:** Advice like "after saving the opportunity, the Contact's Total Giving field will reflect the new amount" or a flow design that reads a CRLP rollup field immediately after an Opportunity insert and branches on its value.

**Why it happens:** Salesforce roll-up summary fields on master-detail relationships are real-time. LLMs conflate standard roll-up summary behavior with CRLP, which is batch-driven. The asynchronous nature of CRLP is a managed package behavior not obvious from general Salesforce documentation.

**Correct pattern:**

```
CRLP rollup fields are updated asynchronously by a batch job, not in real-time.
After an Opportunity is saved, the related Contact or Account rollup field will
reflect the new value only after the next Incremental or Full recalculation batch
completes. Do not design flows, triggers, or reports that assume immediate rollup
field currency after a DML operation.
```

**Detection hint:** Any flow, trigger, or Apex that reads an NPSP rollup field (e.g., `npo02__TotalOppAmount__c`, `npo02__LastCloseDate__c`) immediately after an Opportunity save, without scheduling a recalculation or using a SOQL aggregate query instead.

---

## Anti-Pattern 3: Ignoring the 40-Character Filter Group Name Limit

**What the LLM generates:** Filter group names like "Current Fiscal Year Major Donor Unrestricted Gifts" (52 characters) or "Membership Renewal Eligible Donors This Year" (44 characters), presented as valid configuration steps.

**Why it happens:** LLMs optimize for descriptive naming conventions. The 40-character limit is a platform-specific constraint that does not appear in general naming guidance and is not surfaced as a prominent error in the NPSP UI.

**Correct pattern:**

```
Filter group names must be 40 characters or fewer. Use abbreviations:
  - "FY" for fiscal year
  - "CY" for calendar year
  - "MG" for major gifts
  - "Q1"/"Q2" etc. for quarters

Examples of valid names (under 40 chars):
  - "FY25 Major Gifts — Unrestricted"   (31 chars)
  - "CY Donors > $500"                  (16 chars)
  - "Membership Renewals FY25"           (23 chars)
```

**Detection hint:** Count the characters in any proposed filter group name. Flag any name longer than 40 characters before proceeding.

---

## Anti-Pattern 4: Recommending Manual Recreation of CRLP Definitions Per Environment

**What the LLM generates:** A deployment guide that says "log into the sandbox, recreate the rollup definitions in NPSP Settings, then log into production and do the same steps manually."

**Why it happens:** LLMs trained on admin-focused NPSP documentation present the NPSP Settings UI as the primary (and sometimes only) path to configure CRLP. The Metadata API deployment path is less prominent in general documentation and often omitted.

**Correct pattern:**

```
CRLP Rollup Definitions and Filter Groups are custom metadata records
(CustomMetadata type). They should be:
1. Built and validated in sandbox.
2. Retrieved using Metadata API: sfdx force:source:retrieve --metadata "CustomMetadata:Customizable_Rollup__mdt"
3. Committed to version control.
4. Deployed to production via change set or SFDX.

Manual recreation in each environment is error-prone and creates version drift.
```

**Detection hint:** Any recommendation to "log into production and recreate" CRLP definitions step by step in the UI, rather than deploying via Metadata API.

---

## Anti-Pattern 5: Omitting Full Recalculation After CRLP Definition Changes

**What the LLM generates:** A configuration guide that creates or modifies Rollup Definitions but does not include a step to run a Full recalculation batch. Or a guide that only mentions running the Incremental batch after a configuration change.

**Why it happens:** LLMs trained on general Salesforce batch job patterns assume that any change takes effect immediately or that the existing scheduled job will pick it up. The requirement for an explicit Full recalculation after definition changes is specific to CRLP's dirty-flag architecture.

**Correct pattern:**

```
After any Rollup Definition change (new definition, modified filter group,
changed aggregate operation, changed store field):

1. Save the definition.
2. Navigate to NPSP Settings > Batch Processing.
3. Run Recalculate Rollups > Full.
4. Wait for the batch to complete before validating rollup values.

The Incremental batch WILL NOT catch definition changes — it only processes
records with the dirty flag set by Opportunity DML. A Full recalculation is
required to update all existing summary records.
```

**Detection hint:** Any CRLP configuration guide that creates or modifies rollup definitions without an explicit "Run Full Recalculation" step afterward. Also flag guides that say "the scheduled batch will pick this up" after a definition change.

---

## Anti-Pattern 6: Suggesting CRLP for PMM Service Delivery Aggregation

**What the LLM generates:** Instructions to create CRLP Rollup Definitions to aggregate Program Management Module (PMM) Service Delivery records onto Program Engagement or Contact records.

**Why it happens:** CRLP is the NPSP aggregation framework, and LLMs may over-apply it to all nonprofit aggregation needs without distinguishing between NPSP donation data and PMM program data.

**Correct pattern:**

```
CRLP is designed for aggregating Opportunity and Payment records (donation data)
onto Contact and Account records. It does not natively aggregate PMM objects
(ServiceDelivery__c, ProgramEngagement__c).

For PMM aggregation:
- Use standard Salesforce roll-up summary fields where master-detail relationships exist.
- Use SOQL-based Apex or scheduled flows for lookup-relationship aggregation.
- Do not configure CRLP definitions targeting PMM objects — they will not work as expected.
```

**Detection hint:** Any CRLP Rollup Definition that specifies `ServiceDelivery__c`, `ProgramEngagement__c`, or other PMM objects as the Detail Object.
