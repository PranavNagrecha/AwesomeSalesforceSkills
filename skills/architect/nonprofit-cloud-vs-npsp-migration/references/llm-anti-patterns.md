# LLM Anti-Patterns — Nonprofit Cloud vs NPSP Migration

Common mistakes AI coding assistants make when choosing between or migrating between NPSP and Nonprofit Cloud.

## Anti-Pattern 1: Recommending NPSP for a greenfield nonprofit

**What the LLM generates:** "Install NPSP — it is the standard for nonprofits on Salesforce."

**Why it happens:** Pretraining is heavy on NPSP; Nonprofit Cloud is newer and less represented.

**Correct pattern:**

```
For greenfield nonprofits, default to Nonprofit Cloud. It is the
forward-looking native product, with native Einstein features and the
Industries data model. NPSP remains supported but new investment goes
to Nonprofit Cloud. Choose NPSP only for a specific AppExchange
dependency or team familiarity reason.
```

**Detection hint:** A new-project proposal installs NPSP without evaluating Nonprofit Cloud.

---

## Anti-Pattern 2: 1:1 object mapping from NPSP to Nonprofit Cloud

**What the LLM generates:** "Map `npsp__Opportunity__c` → `Gift__c` and copy the fields over."

**Why it happens:** The model treats migrations as renames and misses semantic differences (soft credits, recurring donation engine, household rollups).

**Correct pattern:**

```
Build a field-by-field mapping spreadsheet. Some NPSP objects have no
Nonprofit Cloud equivalent; some Nonprofit Cloud features (native
soft credits) require converting NPSP custom relationships into
native relationships. Validate with fundraising users before writing
migration scripts.
```

**Detection hint:** Migration script literal-copies NPSP fields to Nonprofit Cloud fields without a mapping review.

---

## Anti-Pattern 3: Running data loads into NPSP with triggers enabled and no rollup plan

**What the LLM generates:** Bulk loader script inserts 500k gifts into NPSP Opportunity; triggers enabled; no rollup coordination.

**Why it happens:** The model treats NPSP like stock Salesforce and is unaware of NPSP's heavy triggers + rollup engine.

**Correct pattern:**

```
Before bulk loading to NPSP Opportunity: disable NPSP triggers via
npsp__Trigger_Handler__c records, load data, re-enable triggers, and
run NPSP's Rollup batch deliberately. Skipping this produces silently
wrong household rollups.
```

**Detection hint:** Data Loader configuration with no reference to NPSP trigger handlers or rollup scheduling.

---

## Anti-Pattern 4: Keeping NPSP alongside Nonprofit Cloud with no boundary

**What the LLM generates:** "Install Nonprofit Cloud features and also keep NPSP; use whichever for each flow."

**Why it happens:** Model avoids committing to one model and creates ambiguity.

**Correct pattern:**

```
If both exist, draw an explicit boundary: e.g., NPSP owns fundraising
transactions, Nonprofit Cloud owns program management and services.
Two data models without a boundary means dual writes, duplicate
reports, and conflicting household logic.
```

**Detection hint:** An architecture diagram with NPSP and Nonprofit Cloud in the same swimlane with no clear domain split.

---

## Anti-Pattern 5: Ignoring payment processor and recurring donation engine in the migration

**What the LLM generates:** Migration plan covers constituents and gifts but never mentions recurring donations or the payment processor.

**Why it happens:** The model focuses on data objects and forgets that recurring charges run on a payment-processor schedule that must not break.

**Correct pattern:**

```
Migration plan must include: payment processor cutover (Stripe,
Braintree, iATS), recurring donation schedule replay, tokenized card
reassignment, reconciliation of in-flight transactions. Cut over
payment processing in a narrow window with a feature freeze on
recurring donation modifications.
```

**Detection hint:** Migration runbook with no entry for "payment processor" or "recurring donation cutover."

---

## Anti-Pattern 6: Loading NPSP Rollup Values As Data In The Target

**What the LLM generates:** "Copy `npo02__TotalOppAmount__c` and the other rollup fields onto the Account in Nonprofit Cloud so donor totals are preserved."

**Why it happens:** Totals look like data, and copying them makes the first report match.

**Correct pattern:**

```
Rollups are definitions to rebuild, not values to load.
- NPSP: Customizable Rollups (npsp__Rollup__mdt, npsp__Customizable_Rollup_Settings__c)
- Nonprofit Cloud: Record Rollup Definitions (RecordAggregationDefinition, API 59.0+;
  needs the Record Aggregation permission set licence and Record Aggregation Access)
Rebuild each rollup, let it calculate from migrated GiftTransaction rows, and
reconcile a donor sample against the NPSP values.
```

**Detection hint:** A mapping row whose source is a rollup or summary field and whose target is a plain field.

UNVERIFIED (2026-10-03): the field name `npo02__TotalOppAmount__c` is a commonly seen NPSP household rollup used here as an illustration; confirm the installed field names in the source org.

---

## Anti-Pattern 7: Assuming The Migration Or Integration User Can See Fundraising Objects

**What the LLM generates:** A Data Loader or middleware plan that authenticates as the existing integration user and inserts into `GiftTransaction`.

**Why it happens:** Standard objects are assumed to be visible to any user with object permissions.

**Correct pattern:**

```
Fundraising objects are "available only if the Fundraising Access license is
enabled and the Fundraising User system permission is assigned to users"
(NPC Guide, Special Access Rules). Assign both, through a permission set group,
to the migration user and every integration user (payment processor, email,
portal) before the pilot load, and test each one.
```

**Detection hint:** A migration runbook with no step that assigns the Fundraising Access licence or the Fundraising User permission.
