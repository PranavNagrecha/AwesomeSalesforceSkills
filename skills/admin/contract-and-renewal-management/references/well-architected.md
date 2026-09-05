# Well-Architected Notes — Contract and Renewal Management

## Relevant Pillars

- **Reliability** — The contract lifecycle is highly stateful. A failed amendment or renewal that leaves the Contract and Subscription records in an inconsistent state is difficult to recover from without data correction. Reliable contract management requires transactional consistency: always use CPQ's built-in amendment and renewal flows rather than direct record edits. For large-scale amendments, use the async API path to prevent governor limit failures that leave the contract in a partial state.

- **Operational Excellence** — Amendment and renewal processes that are well-defined and repeatable reduce manual errors. Configure CPQ Settings (renewal term, co-termination behavior, auto-renewal) deliberately and document the choices. Build monitoring for async amendment jobs so failures surface immediately rather than silently. Include the amendment/renewal flow in end-to-end UAT for any CPQ deployment.

- **Performance** — Synchronous amendment processing has a practical ceiling of ~200 subscription lines before governor limits become a risk. **UNVERIFIED (2026-09-05): that ceiling is a CPQ community rule of thumb, not a published limit — the App Limits Cheat Sheet carries no Contract or Order limits and the CPQ package is outside every platform guide. Treat it as a prompt to measure, not as a number to quote.** Contracts at scale (enterprise accounts with hundreds of subscribed products) require the async `SBQQ.ContractManipulationAPI.amend()` path. Failing to plan for scale results in amendment failures during business-critical renewal events — a high-impact operational outage.

## Architectural Tradeoffs

**Auto-Renewal vs. Manual Renewal:** Auto-renewal (CPQ Setting) reduces process friction but removes the negotiation step. In B2B contexts with custom pricing, manual renewal is preferred because it allows the renewal quote to be reviewed and negotiated before the customer is committed. Auto-renewal is appropriate for consumer or SMB contexts where standard list pricing and fixed terms are the norm.

**Co-Termination: Earliest End Date vs. End of Term:** CPQ's default co-termination mode ("Earliest End Date") simplifies the contract by converging all lines to a single end date. This works well when contracts are expected to renew as a unit. However, for accounts with products on different lifecycle tracks (e.g., a 12-month support subscription and a 36-month platform license), co-termination can force premature renewal of long-term lines. In these cases, consider splitting products across separate contracts rather than co-terming them, or change the CPQ co-termination setting to "End of Term" (which appends lines rather than shortening them).

**Contracted Prices vs. Manual Renewal Negotiation:** Using `SBQQ__ContractedPrice__c` records to lock in renewal pricing is the cleanest architectural solution for accounts with negotiated rates. It is maintainable and auditable. The alternative — manually editing the renewal quote each cycle — is error-prone and does not scale. Establish a process to create contracted price records at the time of initial contract activation, not as a one-off fix at renewal time.

## Anti-Patterns

1. **Directly modifying SBQQ__Subscription__c records** — Editing subscription records outside the amendment flow corrupts the data model that CPQ relies on for renewal generation. The correct path is always an Amendment Quote, even for small corrections. Direct edits save time in the moment but create reconciliation work that is significantly more expensive.

2. **Cloning quotes to create renewals** — A cloned quote lacks the `SBQQ__RenewedContract__c` relationship on the associated Opportunity. This breaks contract history chaining, makes revenue reporting inaccurate, and can cause contracted price inheritance to fail on the next contract cycle. Always use the Renew button or set the lookup programmatically.

3. **Skipping monitoring for async amendments** — Assuming an async amendment succeeded because no immediate error appeared is a production risk. Async batch failures are silent from the user's perspective. Any org running large-scale amendments should have a monitoring process (Apex post-processing notification, scheduled job to check `AsyncApexJob` status, or Flow-based alert) to surface failures proactively.

## Official Sources Used

Platform sources — read as extracted plain text from the Summer '26 / v62 PDFs; every
line reference below is a `sed`/`grep -n` line number in that extraction.

- Salesforce Object Reference, `Contract` object — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (L80851–L81537: `AccountId` required, `ActivatedById`/`ActivatedDate`, `ContractTerm`, `EndDate` read-only and calculated (L81153–L81160), `OwnerExpirationNotice` restricted to 15/30/45/60/90/120 (L81230–L81236), `Pricebook2Id`, `Status` vs `StatusCode` (L81470–L81490), and the Usage paragraph behind the whole activation-lock argument (L81520–L81525))
- Salesforce Object Reference, `ContractStatus` object — same PDF (L82233–L82300: the status-category model, and the claim that `Terminated` and `Expired` "are defined but are not available for use via the API" at L82295–L82296, which is Gotcha 10)
- Salesforce Object Reference, `ContractLineItem` and `ContractContactRole` — same PDF (L81545–L81661: `ContractLineItem` "represents a product covered by a service contract (customer support agreement)" with a required `AssetId`, which is Gotcha 9 and the reason commercial lines belong on `Order`)
- Salesforce Object Reference, `Order` and `OrderItem` — same PDF (L196122–L197120 and L199076–L200184: `ContractId` and `AccountId` updatable only while `StatusCode` is `Draft`, `IsReductionOrder`, `OriginalOrderId`/`OriginalOrderItemId`, `EffectiveDate`, `AvailableQuantity` (L199127–L199135), the Order activation rules and the "Orders Without Price Books" constraints — Gotcha 11 and the `OrderSettings` guidance in `metadata-examples.md` §2)
- Metadata API Developer Guide, `ContractSettings` and `OrderSettings` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (L113209–L113246 and L123644–L123731: the two documented `ContractSettings` elements, the eight `OrderSettings` elements with their `enableOrders` dependencies, both sample definitions and the package.xml sample that `metadata-examples.md` §1, §2 and §7 are built from)
- Metadata API Developer Guide, `StandardValueSet` / `StandardValue` / `CustomValue` — same PDF (L130740–L130829, L47474–L47534, L142098, L142689: the `ContractStatus` and `OrderStatus` value-set names, the field set available on each value, the "must contain at least one picklist value" rule, and the note that omitted values are deactivated on deploy)
- Metadata API Developer Guide, `ValidationRule`, `CustomField`, `FlowStart` / `FlowSchedule` — same PDF (L45363–L45448, L43204–L43690, L71335–L72560: `errorConditionFormula` / `errorMessage` / `errorDisplayField`, the no-compound-fields rule, `formula` and `formulaTreatBlanksAs`, `trackHistory` needing `enableHistory`, and `triggerType: Scheduled` requiring `schedule` — the basis for `metadata-examples.md` §4, §5 and §6)
- Salesforce App Limits Cheat Sheet — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf (**negative result**, recorded deliberately: it publishes no Contract or Order edition or volume limits. Every "contract" hit in it refers to the customer's Salesforce contract, and every "order" hit to SOQL `ORDER BY`. This is why the CPQ line-count thresholds in `SKILL.md` carry an UNVERIFIED marker rather than a citation.)

CPQ sources — Salesforce CPQ is a managed package. `SBQQ__` returns zero hits across the
Object Reference, the Metadata API Developer Guide, the Apex Developer Guide and the Apex
Reference Guide, so nothing in Gotchas 1–5 or the CPQ patterns can be line-cited above.
Those claims rest on the CPQ product documentation:

- Salesforce CPQ Contract Fields Reference — https://help.salesforce.com/s/articleView?id=sf.cpq_contract_fields.htm (CPQ contract and subscription field semantics)
- Amend Your Contracts and Assets (Salesforce CPQ) — https://help.salesforce.com/s/articleView?id=sf.cpq_amend_contracts.htm (amendment quote generation and the locked-line behaviour in Gotcha 1)
- CPQ Amendment Fields and Settings — https://help.salesforce.com/s/articleView?id=sf.cpq_amendment_fields.htm (co-termination modes behind Gotcha 2 and the renewal-pricing contrast in Gotcha 3)
- Salesforce CPQ Large-Scale Amendment and Renewal (KA-000384875) — https://help.salesforce.com/s/articleView?id=000384875&type=1 (the async amendment path and its monitoring, Gotcha 5)
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (the Reliability / Operational Excellence / Performance framing above)
