# Gotchas — Usage-Based Pricing Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: There is no object called `UsageRecord` — raw usage lands in `TransactionJournal`

**What happens:** An integration is specced against a `UsageRecord` or `UsageTransaction` object, the ingestion pipeline is built, and the first deploy fails with `INVALID_TYPE: sObject type 'UsageRecord' is not supported`. The Revenue Management data model names the raw-consumption object `TransactionJournal`, described as the object that "Represents consumption details of a usage resource that are recorded for creating usage summaries."

**When it occurs:** Whenever the integration spec is written from a generic SaaS metering mental model rather than from the object list, and whenever an assistant fills in a plausible-sounding object name.

**How to avoid:** Read the Usage Management standard-object list before writing the ingestion spec, and name the objects exactly. The rating chain, in order, is:

| Stage | Object | Documented purpose |
|---|---|---|
| Raw consumption | `TransactionJournal` | "Represents consumption details of a usage resource that are recorded for creating usage summaries" |
| Aggregation | `UsageSummary` | "Represents the aggregation of the entries in the transaction journal for a usage entitlement for a specified period" |
| Rating input | `UsageRatableSummary` | "Represents the aggregation of the usage summaries that are used to calculate the rate at which the overages are charged" |
| Billable output | `UsageBillingPeriodItem` | "Represents the calculated overages for the usage entitlement and the amount that's charged for these overages" |

Your integration writes to the first row of that table and nothing else. Everything below it is produced by the platform.

---

## Gotcha 2: Overage, rollover, renewal and commitment are separate policy objects, not fields on a schedule

**What happens:** A team models "1M calls included, then $0.002 per call, unused units roll over one period" as tiers on a single pricing record, then discovers the rollover behaviour has nowhere to live. Each of those behaviours is a distinct configuration object:

- `UsageOveragePolicy` — "Represents the set of rules that determine the management of usage resource's units consumed beyond the granted limit"
- `UsageGrantRolloverPolicy` — "Represents a policy about the rollover of a usage grant"
- `UsageGrantRenewalPolicy` — "Represents a policy about the rollover of a usage grant"
- `UsageCommitmentPolicy` — "Represents the set of rules that determines how commitments are applied to a usage resource"
- `UsageResourcePolicy` — "Represents the policies applicable to the usage resource whether it's associated with a sellable product or not"
- `UsageResourceBillingPolicy` — "Represents information about how usage is accumulated before rating a usage resource"
- `RatingFrequencyPolicy` — "Policy defining rating trigger frequency for ratable summary records"

**When it occurs:** Every first implementation, and every migration from a homegrown or Stripe-style metering model where all of this is one price object.

**How to avoid:** Decompose the commercial term into policies before you build anything. Write down which policy object carries each clause of the contract. A term with no policy object is a term the platform will not enforce, and finding that out during UAT is expensive.

---

## Gotcha 3: Two different usage-pricing data models exist, and guidance for one does not apply to the other

**What happens:** An admin follows a tutorial that configures `ConsumptionSchedule` and `ConsumptionRate` records against `Product2`, then cannot find any of the `UsageResource` / `UsageSummary` objects that the current Revenue Management guide describes — or the reverse. Both models are real; they belong to different generations of the product, and they are configured, licensed, and rated differently.

**When it occurs:** Any org that has lived through the CPQ-to-Revenue-Cloud transition, and any search-driven research where the top result is the older model.

**How to avoid:** Establish which model your org is actually licensed for *before* designing anything, by checking which objects exist in Setup → Object Manager. If `UsageResource`, `TransactionJournal` and `UsageSummary` are present, you are on the Revenue Management usage model and the policy objects above are your configuration surface. Do not mix guidance between the two.

---

## Gotcha 4: Units of measure are a two-level model, and mismatches are silent

**What happens:** Telemetry sends bytes; the entitlement is denominated in gigabytes; the rate card is priced per gigabyte. Nothing rejects the mismatch — the numbers are just wrong by a factor of a billion, and it surfaces on the first invoice. The model has two objects specifically to prevent this: `UnitOfMeasure`, which "Defines the units and systems of units used to account for quantities of a usage resource", and `UnitOfMeasureClass`, which "Represents a standard unit of measure dimension."

**When it occurs:** Any ingestion where the emitting system's native unit differs from the contracted unit — which is most of them, because product telemetry emits whatever is cheapest to count.

**How to avoid:** Fix the unit at the `UsageResource` level, define the `UnitOfMeasureClass` for the dimension, and normalise in the ingestion layer rather than at any point downstream. Put a reconciliation assertion in the pipeline that compares total ingested quantity against the source system's own reported total for the same window, in the same unit, and fails loudly on drift.

---

## Gotcha 5: Rating is asynchronous and batched, so "the invoice is wrong" usually means "rating has not run yet"

**What happens:** Someone loads test usage, opens the account, sees no charges, and files a defect against the rate card. Rating is not synchronous with ingestion: `RatingFrequencyPolicy` defines "rating trigger frequency for ratable summary records", `RatingRequest` carries the "common run-time parameters for rating sets of records", and `RatingRequestBatchJob` is the "junction object between rating request and batch job objects" — a batch pipeline with its own schedule and its own job records.

**When it occurs:** Every UAT cycle, and every production incident triage in the first quarter after go-live.

**How to avoid:** Before diagnosing a pricing defect, establish where the data is in the chain — is there a `TransactionJournal` row, did it aggregate into a `UsageSummary`, did a `RatingRequest` run over it, is there a `UsageBillingPeriodItem`? Build that four-step check into a runbook. The Rate Management business API also exposes a **Rating Waterfall** resource that returns "the persisted rating waterfall that stores the process logs" and "provides insights into the internal rating process" — that is the intended diagnostic, and it is far faster than reverse-engineering the arithmetic from the output.
