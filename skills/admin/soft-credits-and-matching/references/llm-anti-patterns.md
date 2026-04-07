# LLM Anti-Patterns — Soft Credits and Matching Gifts (NPSP)

Common mistakes AI coding assistants make when generating or advising on NPSP soft credits and matching gift configuration. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating Household Auto-Soft-Credits With Explicit Matching Gift Credits

**What the LLM generates:** An explanation that "NPSP automatically creates soft credits for related contacts, including employer matching, based on the household model." The LLM treats matching gift credits as an extension of the same auto-credit mechanism used for household members.

**Why it happens:** Training data conflates NPSP's two different automatic-credit mechanisms — household member auto-credits (which are genuinely automatic and OCR-based) and matching gift credits (which require a separate Matching Gift opportunity and the Find Matched Gifts action). Both appear under "soft credits" in NPSP documentation, encouraging incorrect generalization.

**Correct pattern:**

```
Household auto-soft-credits:
- Triggered automatically by NPSP when a household member who is not the primary donor is on the household Account
- Creates OCRs with role = "Household Member" automatically
- Controlled by NPSP Settings > Household Settings > Automatically Create Soft Credit For...

Matching gift credits:
- Require a separate Matching Gift Opportunity record on the employer Account
- Require manually running Find Matched Gifts (or custom automation replicating it)
- Result in an OCR with role = "Matched Donor" on the MATCHING GIFT opportunity — not the employee's donation
- Use npsp__Partial_Soft_Credit__c for partial match amounts
```

**Detection hint:** If the response says matching gifts are handled "automatically" by NPSP or describes the employer receiving credit via the employee's donation OCR, the anti-pattern is present.

---

## Anti-Pattern 2: Advising That Soft Credit Totals Update in Real Time

**What the LLM generates:** "After you add the OpportunityContactRole, the contact's soft credit this year field will update immediately." Or: "NPSP uses real-time rollups, so the contact totals are always current."

**Why it happens:** NPSP's real-time rollup mode is a documented feature, and LLMs over-apply it. Real-time rollups in NPSP cover primary gift hard credit calculations; soft credit rollup fields are excluded and run through the batch path regardless of rollup mode setting.

**Correct pattern:**

```
Soft credit rollup fields (npsp__Soft_Credit_This_Year__c, etc.) update ONLY:
1. When the nightly NPSP batch job runs (NPSP_Account_Contact_Rollup), OR
2. When an admin manually triggers Recalculate Rollups from NPSP Settings > Batch Processing, OR
3. When the Contact-level Recalculate Rollups button is used (if available in the NPSP version)

After creating OCR or Partial_Soft_Credit__c records, always trigger manual recalculation
before reading or reporting on soft credit totals.
```

**Detection hint:** Any phrase like "updates immediately," "real-time," or "automatically reflects" in the context of soft credit rollup fields is the anti-pattern.

---

## Anti-Pattern 3: Creating OCR With Soft Credit Role on the Employee's Donation to Credit the Employer

**What the LLM generates:** Advice to add an OCR with role "Soft Credit" (or "Matched Donor") to the employee's original donation Opportunity, with the employer contact listed as the recipient, to represent a matching gift credit.

**Why it happens:** This is the intuitively simple approach — add a credit record to the gift in question. LLMs familiar with generic CRM credit-attribution patterns default to this because they lack specific knowledge of NPSP's matching gift data model, where employer credit flows through a separate Matching Gift opportunity.

**Correct pattern:**

```
Correct matching gift data model:
1. Employer Account has a separate Matching Gift Opportunity (not the employee's donation)
2. Find Matched Gifts links the employee's donation to the Matching Gift opportunity
   via npsp__Matching_Gift__c lookup on the employee's Opportunity
3. An OCR with role "Matched Donor" is created on the MATCHING GIFT Opportunity
   for the employer contact
4. npsp__Partial_Soft_Credit__c is created on the Matching Gift Opportunity
   with the matched amount

The employee's donation Opportunity does NOT receive an employer OCR.
```

**Detection hint:** If the response creates an OCR on the employee's donation for the employer contact, or does not mention a separate Matching Gift Opportunity, the anti-pattern is present.

---

## Anti-Pattern 4: Treating Find Matched Gifts as Safe to Re-Run

**What the LLM generates:** "If the matching gift wasn't recorded correctly, just click Find Matched Gifts again to fix it." Or: "You can re-run Find Matched Gifts to refresh the matching gift linkage."

**Why it happens:** LLMs often assume UI actions are idempotent unless explicitly told otherwise. Find Matched Gifts looks like a lookup/sync operation rather than a record-creation operation, which reinforces the assumption that running it again is safe.

**Correct pattern:**

```
Find Matched Gifts is NOT idempotent.

Each execution creates new OCR and npsp__Partial_Soft_Credit__c records
on the Matching Gift Opportunity WITHOUT checking whether they already exist.

Before re-running Find Matched Gifts:
1. Delete the existing OCR (Role = "Matched Donor") for the employer contact
   on the Matching Gift Opportunity
2. Delete the existing npsp__Partial_Soft_Credit__c record linked to that OCR
3. Then run Find Matched Gifts again

Skipping steps 1-2 creates duplicate records and inflates rollup totals.
```

**Detection hint:** Any advice to "re-run," "run again," or "click Find Matched Gifts to update" without mentioning deletion of existing records first is the anti-pattern.

---

## Anti-Pattern 5: Omitting npsp__Contact_Role_ID__c When Creating Partial_Soft_Credit__c Records

**What the LLM generates:** Apex or data loader instructions that create `npsp__Partial_Soft_Credit__c` records with `npsp__Opportunity__c`, `npsp__Contact__c`, and `npsp__Amount__c` populated — but without `npsp__Contact_Role_ID__c`.

**Why it happens:** The three obvious fields (opportunity, contact, amount) match what most credit-attribution objects require. The lookup back to the OCR is a NPSP-specific requirement that is easy to miss, and it is not enforced by a platform validation rule — the record saves without error whether or not `npsp__Contact_Role_ID__c` is populated.

**Correct pattern:**

```apex
// WRONG — saves without error but partial amount is silently ignored by NPSP
npsp__Partial_Soft_Credit__c psc = new npsp__Partial_Soft_Credit__c(
    npsp__Opportunity__c = oppId,
    npsp__Contact__c = contactId,
    npsp__Amount__c = 5000
    // npsp__Contact_Role_ID__c is missing
);

// CORRECT — OCR must be inserted first; its Id is required
npsp__Partial_Soft_Credit__c psc = new npsp__Partial_Soft_Credit__c(
    npsp__Opportunity__c = oppId,
    npsp__Contact__c = contactId,
    npsp__Amount__c = 5000,
    npsp__Contact_Role_ID__c = ocrId  // Id of the corresponding OCR record
);
```

**Detection hint:** Any code or data loader template that creates `npsp__Partial_Soft_Credit__c` records without `npsp__Contact_Role_ID__c` is the anti-pattern. Check all insert statements and data migration field mappings.

---

## Anti-Pattern 6: Assuming NPSP Validates Against Duplicate Soft Credit OCRs

**What the LLM generates:** "NPSP will prevent duplicate contact roles from being created for the same contact on the same opportunity." Or: "The system will warn you if a soft credit already exists for this contact."

**Why it happens:** Salesforce does enforce uniqueness on primary OCRs (only one primary per Opportunity), which LLMs generalize incorrectly to all OCR uniqueness constraints. NPSP adds no additional uniqueness enforcement on soft credit role OCRs.

**Correct pattern:**

```
NPSP does NOT enforce uniqueness on soft credit OCRs.

Multiple OCR records with the same contact, same role, and same opportunity
can coexist without any platform error. Each one independently contributes
to rollup calculations.

Duplicate detection is a manual or programmatic responsibility:
- Before inserting OCRs via data loader or Apex, query for existing records
- After running Find Matched Gifts, query for duplicate Matched Donor OCRs
- Include duplicate-OCR audit queries in post-migration validation scripts
```

**Detection hint:** Any claim that the system "prevents," "blocks," or "warns about" duplicate soft credit OCRs is the anti-pattern.
