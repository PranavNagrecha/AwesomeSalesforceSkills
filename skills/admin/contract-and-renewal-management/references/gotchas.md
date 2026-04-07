# Gotchas — Contract and Renewal Management

Non-obvious Salesforce CPQ platform behaviors that cause real production problems in the contract and renewal domain.

## Gotcha 1: Amendment Pricing Locks Existing Lines to Original Contracted Price

**What happens:** When an amendment quote is generated from an active contract, all existing subscription lines display the price from the original Quote Line, not the current price book entry. Fields like Unit Price and List Price on these lines are read-only in the CPQ quote editor. Updating the product's price book entry after the contract was activated has no effect on the amendment quote.

**When it occurs:** Every time an amendment quote is created on a contract that contains previously contracted subscription lines. This is the default and non-configurable behavior for existing lines. It catches admins off guard when a price book update was expected to flow through to an amendment.

**How to avoid:** Do not promise customers or internal teams that a mid-contract price book update will affect existing subscription pricing on an amendment. New lines added during the amendment do pick up current price book pricing. If a price correction on an existing line is genuinely required, the only supported path is to use a `SBQQ__ContractedPrice__c` record for the account/product combination before creating the amendment, which CPQ will then use as the override price for that line.

---

## Gotcha 2: Co-Termination Can Silently Shorten Line Terms

**What happens:** When a contract contains subscription lines with different start dates (common when products are added via multiple amendments), CPQ co-termination logic forces all lines on a new amendment to end on the date of the earliest-ending subscription. A line that was supposed to run 24 months may be co-termed to end in 8 months if there is an older line expiring sooner.

**When it occurs:** Any time an amendment is created on a contract with heterogeneous subscription end dates. This is the default CPQ behavior unless the CPQ Setting for co-termination is changed to "End of Term" rather than "Earliest End Date."

**How to avoid:** Before creating an amendment on a contract with mixed-term lines, query the `SBQQ__Subscription__c` records to identify the earliest `SBQQ__EndDate__c`. Communicate to the customer that all lines will be co-termed to that date. If the customer objects, evaluate whether the CPQ co-termination setting should be changed org-wide, or whether some lines should be split into a separate contract. Do not attempt to manually override end dates on the amendment quote — this produces inconsistent subscription state.

---

## Gotcha 3: Renewal Reprices at Current List — Not Contracted Prices

**What happens:** Renewal quotes reprice all lines at the current price book rate, regardless of the price the customer was paying during the original contract. If prices have increased since the original contract was signed, the renewal quote will reflect those higher prices without any warning.

**When it occurs:** Every time a renewal quote is generated. This is opposite to amendment behavior (where existing lines are locked). The intent is that renewals represent a fresh negotiation, but it surprises admins who expect renewal pricing to match the expiring contract.

**How to avoid:** If the customer has a negotiated rate that should carry into renewals, create a `SBQQ__ContractedPrice__c` record for the account/product combination. CPQ will use the contracted price record instead of the price book entry when generating the renewal quote. Without contracted prices, the renewal will always price at list. Build a review step into the renewal process to compare renewal quote prices against the expiring contract before presenting to the customer.

---

## Gotcha 4: SBQQ__RenewedContract__c Must Be Set for Lifecycle Integrity

**What happens:** If a renewal quote is created by cloning the original opportunity and quote (rather than using the Renew button on the contract), the `SBQQ__RenewedContract__c` lookup on the Renewal Opportunity is never set. CPQ uses this field to chain contract history. Contracted price records, revenue rollups, and contract lineage reports will all be broken because the system does not know this opportunity represents a renewal of the expiring contract.

**When it occurs:** When admins take shortcuts by cloning instead of using the Renew button, or when a third-party integration creates renewal opportunities without setting this field.

**How to avoid:** Always use the **Renew** button on the Contract record, or programmatically set `SBQQ__RenewedContract__c` on the Renewal Opportunity when creating renewals via API or automation. Validate this field is populated before closing a renewal opportunity as Won.

---

## Gotcha 5: Async Amendment Does Not Surface Errors Prominently

**What happens:** When using `SBQQ.ContractManipulationAPI.amend()` for large-scale amendments, failures in the async batch job are written to `AsyncApexJob.ExtendedStatus` and the Apex Job log — not to any visible UI element on the Contract record. Admins who trigger an async amendment and then wait for the amendment quote to appear on the Contract will wait indefinitely if the job failed.

**When it occurs:** Any large-scale amendment using the async API path fails (due to data issues, permission errors, or governor limit overruns in the batch context).

**How to avoid:** After triggering an async amendment, build explicit monitoring into the process. Query `AsyncApexJob` where `ApexClass.Name` contains `Amendment` and check `Status` and `ExtendedStatus`. Consider implementing a post-processing notification (email alert or platform event) when the batch job completes or fails. Do not assume silence means success.
