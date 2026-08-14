# Well-Architected Notes — Rebate Management Setup

## Relevant Pillars

### Reliability

A rebate program's output is money that leaves the company, so "mostly right" is not a state it can occupy. Reliability here means every payout is reproducible from its source journals: `RebateMemberProductAggregate` "Stores the post calculation summary of journal transactions by member, period, and rebate type," and `RebateMemberAggregateItem` is the junction back to each contributing `TransactionJournal`. Keeping that chain intact — idempotent ingestion, adjustments in adjustment objects rather than edits to calculated fields, unit conversions loaded before the first journal — is what lets a disputed payout be answered with evidence instead of a rebuild.

### Security

Rebate data is competitively sensitive in both directions: a partner must see their own tier progress and must never see another partner's rate. The model puts that boundary on `RebateProgramMember` — "The member of a rebate program. By virtue of being a member, the partner or business account is eligible to get rebate payments" — so partner-facing surfaces have to be scoped by member, not by program. Benefit matrices are the sharpest edge: `ProgramRebateTypeBenefit` holds the negotiated rate, and exposing it on a portal page is how one distributor learns another's terms.

### Operational Excellence

The period close is a recurring operational event, not a one-time setup. Accrual and payout run on independently configured cadences (`RebateProgramAccrualPeriod` and `RebateProgramPayoutPeriod`), so the runbook has to state which numbers are estimates and which are committed, who signs off, and what happens to a late journal that lands after close. Programs that lack this end up reopening closed periods, which is where partner-visible balances start moving without explanation.

## Architectural Tradeoffs

**Accrual frequency vs. compute cost and stability.** Daily accruals give partners a live tier-progress number and recalculate the liability every night; monthly accruals are cheaper and steadier but leave partners guessing between runs. Pick the frequency the partner-facing promise actually requires — a portal that advertises real-time progress commits the org to daily.

**Standard model vs. custom extension.** The shipped objects cover a lot, including benefit-matrix extension through `PgmRebateTypBnftMapping`, which "defines mapping of benefit field to the aggregate object fields" when the benefit table is extended. Extending within the shipped structure keeps the calculation, the accruals, and the partner components working. Bolting a parallel custom model alongside it buys short-term flexibility and permanent reconciliation work.

**Journal granularity vs. storage.** Line-level journals give the finest audit trail and the largest data volume; pre-aggregating upstream cuts storage and destroys the ability to answer "which transactions produced this number". Aggregate upstream only where the source system can be trusted to answer that question instead, and record where the evidence lives.

## Anti-Patterns

1. **Rebuilding the model as custom objects.** `RebateProgram`, `ProgramRebateType`, and `TransactionJournal` are standard and appear on provisioning. A `__c` rebate model cannot feed the shipped calculation, and discovering that after the transactions are loaded turns a configuration task into a migration.

2. **Overwriting calculated payouts to record discretion.** Manual amounts belong in `RebatePayoutAdjustment` and `RebatePgmMbrAcruAdjustment` — the latter carries approval status and comments natively. Editing the calculated field loses the change on the next run and leaves no reason attached to money that moved.

3. **Ingesting mixed units without loading `UnitOfMeasureConversion` first.** Cases, eaches, and pallets summed as bare numbers place partners in the wrong tier with no error raised. The conversion table is reference data with a hard ordering dependency, not an optimisation to add later.

## Official Sources Used

- Channel Revenue Management Developer Guide — Rebate Management Standard Objects — full object list with verbatim descriptions (`RebateProgram`, `ProgramRebateType`, `ProgramRebateTypeBenefit`, `ProgramRebateTypEligibility`, `ProgramRebateTypeFilter`, `TransactionJournal`, `RebateMemberProductAggregate`, `RebateMemberAggregateItem`, `RebateProgramMember`, `RebateProgramMemberPayout`, `RebateProgramPayoutPeriod`, `RebateProgramMemberAccrual`, `RebatePayoutAdjustment`, `RebatePgmMbrAcruAdjustment`, `RebatePayment`, `ReceivedDocument`, `UnitOfMeasureConversion`, `RebateClaim`) and the edition statement "Available in: Enterprise, Unlimited, and Developer Editions" (verified 2026-08-14) — https://developer.salesforce.com/docs/atlas.en-us.rebates_api_devguide.meta/rebates_api_devguide/rebates_api_overview.htm
- Rebate Management Developer Guide — `RebateProgram` — object description and "Available in API version 51.0 and later" (verified 2026-08-14) — https://developer.salesforce.com/docs/atlas.en-us.rebates_api_devguide.meta/rebates_api_devguide/sforce_api_objects_rebateprogram.htm
- Rebate Management Developer Guide — `RebateProgramMember` (verified 2026-08-14) — https://developer.salesforce.com/docs/atlas.en-us.rebates_api_devguide.meta/rebates_api_devguide/sforce_api_objects_rebateprogrammember.htm
- Object Reference for the Salesforce Platform — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
