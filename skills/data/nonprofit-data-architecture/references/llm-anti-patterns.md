# LLM Anti-Patterns — Nonprofit Data Architecture

Common mistakes AI coding assistants make when generating or advising on Nonprofit Data Architecture.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating NPSP Household Account Model with Nonprofit Cloud (NPC)

**What the LLM generates:** Advice or SOQL that references NPC-specific objects (e.g., `Ind_Account__c`, `NPC_Household__c`, or NPC relationship objects) when the org is running NPSP, or vice versa. Or the LLM says "Nonprofit Cloud" when it means NPSP, treating them as different names for the same product.

**Why it happens:** LLMs are trained on nonprofit Salesforce content that frequently uses "Nonprofit Cloud" as a marketing umbrella term covering both NPSP and the newer NPC product. The two products are architecturally incompatible, but training text often conflates them. NPC was released after NPSP had been the dominant nonprofit CRM for a decade, so the volume of NPSP content far exceeds NPC content in training data, creating unpredictable blending.

**Correct pattern:**

```
NPSP (Nonprofit Success Pack):
- Household grouping: Account with RecordType.DeveloperName = 'HH_Account'
- Namespaces: npo02__, npsp__, npe01__, npe03__, npe4__, npe5__
- Giving object: standard Opportunity linked to HH Account

Nonprofit Cloud (NPC) — completely different product:
- Different foundational objects, different namespaces
- Not a newer version of NPSP — a parallel product
- NPSP patterns do not apply to NPC orgs
```

**Detection hint:** If generated content references both `npo02__` namespace fields and NPC-specific objects in the same solution, it has mixed the two models. Also flag any statement that calls NPSP "an older version of Nonprofit Cloud" — they are separate products, not version progression.

---

## Anti-Pattern 2: Querying Opportunity via ContactId for Constituent Gift History

**What the LLM generates:** SOQL like `SELECT Id, Amount FROM Opportunity WHERE ContactId = :contactId` to retrieve a constituent's donation history, following the standard Salesforce contact-activity pattern.

**Why it happens:** In standard Salesforce CRM, contacts are linked to opportunities via the standard `OpportunityContactRole` object or via `ContactId` on Opportunity (for person accounts). LLMs trained on general Salesforce content default to this pattern. The NPSP HH Account model is a deliberate departure from this pattern that requires specific domain knowledge to apply correctly.

**Correct pattern:**

```soql
-- Wrong (returns no results in NPSP HH Account model):
SELECT Id, Amount FROM Opportunity WHERE ContactId = :contactId

-- Correct — query via Household Account:
SELECT Id, Amount FROM Opportunity
WHERE AccountId = :contact.AccountId AND IsWon = true

-- Correct — filter to primary contact if needed:
SELECT Id, Amount FROM Opportunity
WHERE AccountId = :contact.AccountId
  AND npsp__Primary_Contact__c = :contactId
  AND IsWon = true
```

**Detection hint:** Flag any SOQL on Opportunity that uses `ContactId` as a filter when the context is NPSP gift history. `ContactId` on Opportunity is not populated by NPSP's gift creation flow.

---

## Anti-Pattern 3: Treating PMM as Part of NPSP Core

**What the LLM generates:** Solutions that reference `pmdm__ServiceDelivery__c`, `pmdm__ProgramEngagement__c`, or `pmdm__Program__c` without first checking whether the PMM package is installed. Often presented as "use the NPSP program object to track..." implying these objects are always available in NPSP orgs.

**Why it happens:** The Program Management Module is frequently discussed alongside NPSP in Salesforce nonprofit documentation and Trailhead content. LLMs learn the association without learning the package boundary. PMM is a separate installation decision and many NPSP orgs do not have it.

**Correct pattern:**

```python
# Always guard PMM-dependent code with an installation check
# In Apex: use Schema.getGlobalDescribe() to detect pmdm__ objects
# In Python/scripts: check installed packages before referencing pmdm__ fields

# Guard example (Apex):
if (Schema.getGlobalDescribe().containsKey('pmdm__ServiceDelivery__c')) {
    // PMM-dependent logic here
} else {
    // Fallback or error: PMM not installed
}
```

**Detection hint:** Flag any generated solution that uses `pmdm__` objects without an explicit PMM installation check or prerequisite note. The namespace prefix `pmdm__` is the signal.

---

## Anti-Pattern 4: Applying CRLP Configuration Patterns to Orgs Running Legacy Rollup Mode

**What the LLM generates:** Instructions to create `Rollup__mdt` custom metadata records or navigate to the CRLP UI to add a custom rollup field, without first confirming that CRLP is enabled in the org.

**Why it happens:** CRLP is the current recommended rollup approach and is prominently documented in NPSP guides. LLMs default to CRLP guidance because it is the modern pattern. However, many orgs still run legacy rollup mode, especially those on older NPSP versions or those that disabled CRLP after experiencing issues during migration.

**Correct pattern:**

```
Before advising on any rollup configuration:
1. Confirm CRLP is enabled: check NPSP Settings > Rollup Settings
2. If CRLP is enabled: use Rollup__mdt and Filter_Group__mdt via CRLP UI
3. If CRLP is disabled (legacy mode): use the npo02__Household_Settings__c
   settings object and schedule RLLP_OppRollup_BATCH — do NOT create
   Rollup__mdt records, they will have no effect in legacy mode
4. Never enable CRLP mid-migration without removing the legacy batch job first
```

**Detection hint:** If the generated solution creates `Rollup__mdt` records without first stating "confirm CRLP is enabled," flag it. Also flag any solution that creates Rollup__mdt records AND schedules `RLLP_OppRollup_BATCH` — these two approaches conflict.

---

## Anti-Pattern 5: Conflating NPSP Household Account with FSC Household Group

**What the LLM generates:** Solutions that use `AccountContactRelationship` as the household membership object, or reference an "Account with record type Household" using FSC's relationship model, when the org is running NPSP not FSC.

**Why it happens:** Financial Services Cloud also uses household grouping on the Account object, and both FSC and NPSP are discussed extensively in Salesforce household modeling content. LLMs blend the two because both involve "households" and "Account record types." The architectures are fundamentally different: FSC uses `AccountContactRelationship` (ACR) for household membership; NPSP uses `Contact.AccountId` pointing directly to the HH_Account.

**Correct pattern:**

```
NPSP Household Account membership:
  Contact.AccountId → Account (RecordType.DeveloperName = 'HH_Account')
  One Contact.AccountId per Contact — direct relationship
  Query: SELECT Id FROM Contact WHERE AccountId = :hhAccountId

FSC Household Group membership (completely different):
  AccountContactRelationship WHERE Account.RecordType = 'Household'
  Many-to-many relationship via AccountContactRelationship junction object
  Query: SELECT ContactId FROM AccountContactRelationship
         WHERE AccountId = :householdGroupId

These two patterns CANNOT be interchanged. Applying FSC ACR patterns
to an NPSP org will produce schema errors or incorrect data.
```

**Detection hint:** Flag any solution for an NPSP org that uses `AccountContactRelationship` as the primary mechanism for household membership. In NPSP, `Contact.AccountId` is the household link — ACR is not used for this purpose.

---

## Anti-Pattern 6: Using rollup fields for Financial Audit or Tax Reporting

**What the LLM generates:** Recommendations to use `npo02__TotalOppAmount__c` or `npo02__OppAmountThisYear__c` as the source of truth for tax acknowledgment letters, grant reporting, or financial audits.

**Why it happens:** NPSP rollup fields appear on the Contact and Account records prominently, making them look like authoritative financial data. LLMs associate "total giving" with `npo02__TotalOppAmount__c` because it is explicitly named for that purpose. The latency and correctability risk of calculated rollup fields versus raw transaction records is a nuance not present in most training text.

**Correct pattern:**

```soql
-- For financial reporting: ALWAYS aggregate from raw Opportunity records
SELECT AccountId, SUM(Amount) totalGiving
FROM Opportunity
WHERE AccountId IN :householdAccountIds
  AND IsWon = true
  AND CloseDate >= :fiscalYearStart
  AND CloseDate <= :fiscalYearEnd
GROUP BY AccountId

-- npo02__ rollup fields: use for display, segmentation, and constituent-facing UI only
-- Never use as source of truth for tax letters, grant reports, or audit schedules
```

**Detection hint:** Flag any solution that uses `npo02__OppAmountThisYear__c` or `npo02__TotalOppAmount__c` as input to a tax acknowledgment, gift receipt, grant report, or financial audit workflow. These are display fields, not ledger fields.
