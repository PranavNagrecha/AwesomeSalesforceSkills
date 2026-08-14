# Gotchas — Rebate Management Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Every Rebate Object Is Standard — There Is No `__c` Anywhere in the Model

**What happens:** Someone builds `Rebate_Program__c`, `Benefit__c`, and `Transaction__c` because that is what a rebate model "should" look like. Six weeks later the shipped calculation, the shipped accrual roll-ups, and the partner-facing components all turn out to be wired to standard objects the custom build cannot feed. The rebuild is not a rename — it is a re-migration of every transaction.

**When it occurs:** Before provisioning, when the objects are not yet visible in Object Manager and the team assumes they must be built. Also when an AI assistant generates a data model from the phrase "rebate program" without checking what ships.

**How to avoid:** Provision the licence first, then look. The model is standard: `RebateProgram` (API 51.0 and later) is "The rebate program your organization runs with a single account, all accounts, or specific list of accounts," `ProgramRebateType` supplies "the rebate types that are part of this program. For example, volume rebate, revenue rebate, or rebate on every transaction," and `TransactionJournal` holds "The transactions that need to be processed for a rebate program." Edition matters as much as licence: "Rebate Management is available in Lightning Experience. Available in: Enterprise, Unlimited, and Developer Editions" — a Professional-edition org cannot host it at all, and that is a contract conversation, not a configuration one.

---

## Gotcha 2: Several API Names Are Truncated, and the "Corrected" Spelling Does Not Exist

**What happens:** A query, a Flow, or an Apex class references `ProgramRebateTypeEligibility` and fails, because the object is actually `ProgramRebateTypEligibility` — one `e` short. The same trap appears across the model: `ProgramRbtTypeAcruSource`, `ProgramRbtTypeAggrField`, `ProgramRbtTypPayoutSrc`, `PgmRebateTypBnftMapping`, `RebatePgmMbrAcruAdjustment`, `RebatePartnerSpecialPrcTrm`, `RebatePtnrSpclPrcTrmBnft`. These are compressed to fit the API-name length ceiling, and the readable spelling resolves to nothing.

**When it occurs:** Every time a name is typed from memory or auto-completed from a label rather than copied from the object reference. Language models are especially prone to it — the truncated form looks like a typo, so the model "fixes" it.

**How to avoid:** Copy API names from the Rebate Management standard-object list, never retype them. In Apex, reference them through `Schema.getGlobalDescribe()` keys or a compile-time `SObjectType` token so a wrong name fails at deploy rather than at run time. In a Flow or a report, build the reference by picking from the object list rather than typing.

---

## Gotcha 3: Accrual and Payout Are Separate Object Families, and Teams Wire the Wrong One

**What happens:** A partner portal is built against payout objects and shows nothing until the period closes, because the in-period estimate the partner actually wants lives on the accrual side. Or the reverse: finance reports off accruals and treats the numbers as committed liability.

**When it occurs:** Immediately, because the two families read as synonyms. Payout: `RebateProgramPayoutPeriod` is "The period of the payout calculation," `RebateProgramMemberPayout` is "The payout calculated for a member for the period," and `ProgramRebateTypePayout` is "The payout given to a member for a particular rebate type." Accrual: `RebateProgramAccrualPeriod`, `RebateProgramMemberAccrual` "Stores aggregated accrual amounts for a rebate program member for a specific accrual period, including any prior period or rate adjustments," and `ProgramRebateTypeAccrual` holds the same rolled up by rebate type.

**How to avoid:** Decide per surface which number the audience needs — in-period estimate (accrual) or closed-period entitlement (payout) — and label it in the UI. The two periods are configured independently, so an accrual cadence of daily against a payout period of quarterly is normal and expected. Never join them on date alone.

---

## Gotcha 4: Manual Adjustments Are Their Own Objects, Not Edits to a Calculated Payout

**What happens:** An admin edits a calculated payout amount to apply a negotiated top-up. The next calculation run overwrites it, the partner sees the number move, and there is no record of who changed what or why.

**When it occurs:** Whenever the process has a human-discretion step — MDF top-ups, goodwill adjustments, correcting a mis-loaded journal — and the org has not been told where discretion belongs.

**How to avoid:** Route every manual amount through the adjustment objects, which exist precisely for this. `RebatePayoutAdjustment` is the "Rebate amount adjustment that needs to be given manually," and `RebatePgmMbrAcruAdjustment` "Stores manual adjustments made to system-calculated accrual amounts, including the adjustment value, approval status, and related comments" — note that it carries approval status and comments natively, which is the audit trail an edited payout field will never give you. Ship-and-debit claims are a separate shape again: `RebateClaim` and `RebateClaimAdjustment`.

---

## Gotcha 5: Units Do Not Reconcile Unless `UnitOfMeasureConversion` Is Populated First

**What happens:** A volume-tier program pays the wrong tier because journals arrive in mixed units — cases from the distributor feed, eaches from the POS extract, pallets from the warehouse. The aggregate sums the raw numbers and a partner lands two tiers below where the contract says they should be. Nothing errors; the money is simply wrong.

**When it occurs:** Any multi-source ingestion, which is most real deployments. It is invisible in a single-source pilot, so it usually surfaces in the first production quarter — after payouts have gone out.

**How to avoid:** Load `UnitOfMeasureConversion` — "the information used to convert a measurement value from a unit of measure to another" — as reference data before the first `TransactionJournal` lands, not as a fix afterwards. Add a reconciliation check to the period-close runbook that ties `RebateMemberProductAggregate` totals (the "post calculation summary of journal transactions by member, period, and rebate type") back to the source system's own volume report, and treat a variance as a blocker on the payout approval rather than a note.
