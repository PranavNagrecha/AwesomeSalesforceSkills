# Well-Architected Notes — Apex Decimal Arithmetic Precision

## Relevant Pillars

- **Reliability** — Money-touching code that drifts by a cent reaches downstream systems (revenue recognition, billing, financial reporting) where the drift compounds. Reliability here is "the same calculation produces the same value across Apex, Flow, formula, and external API consumers."
- **Security** — Tax and audit calculations must be defensible. A misplaced rounding mode is the kind of bug that surfaces in a compliance review years after deployment, when the original author has left.

## Architectural Tradeoffs

- **One rounding policy vs many** — Centralizing rounding in a `MoneyMath` utility class keeps the policy in one place. The cost is one more level of indirection in calls. The benefit is provably consistent behavior. Worth it for any system that touches a Currency or Tax field.
- **Scale at storage vs scale at compute** — Storing intermediates at higher scale (e.g. computed-tax-with-scale-6 in a workspace field) preserves precision but inflates storage and complicates reporting. The standard Salesforce pattern is "compute at high scale, persist at field scale, document the rounding mode at the boundary."
- **Match-platform rounding vs match-business rounding** — When the business rule is HALF_UP but the Currency field's display rounds HALF_EVEN, choose: (a) match the business rule and accept that the displayed value differs from the stored value on halfway cases, or (b) match the platform and document the deviation from the business rule. There is no "correct" choice — only a documented one.

## Anti-Patterns

1. **Inferring rounding mode from local examples** — Different teams use different rounding for valid reasons (HALF_UP retail, HALF_EVEN finance). Copying a snippet without verifying the rounding mode against the business rule is a top source of "off by a cent" tickets.
2. **Storing the cleaned-up value but computing again from raw inputs** — A persisted `Total_With_Tax__c` written by Apex at HALF_EVEN gets re-summed in a roll-up that re-rounds at HALF_UP, drifting by N×0.01. Either persist the rounded value AND prevent recomputation, or always recompute from raw without persistence.

## Official Sources Used

- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm — Decimal type, RoundingMode enum, divide/setScale signatures.
- Apex Reference Guide — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm — `Decimal.divide`, `Decimal.setScale`, `Decimal.valueOf`, `System.RoundingMode`.
- Object Reference (CurrencyType + DatedConversionRate) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm — multi-currency arithmetic and per-record currency.
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html — Reliability and Security pillars framing.
