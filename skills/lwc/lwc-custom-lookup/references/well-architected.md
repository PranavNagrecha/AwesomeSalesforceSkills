# Well-Architected Notes — LWC Custom Lookup

## Relevant Pillars

- **Performance** — A lookup is the most-fired Apex callout in a
  typical record-edit experience. Debouncing keystroke-triggered
  searches by 280ms typically reduces callouts 5-10x; using
  `cacheable=true` deduplicates repeated terms; capping result
  rows at 10-15 keeps the response payload small. Without these
  three measures, a lookup component can single-handedly exhaust
  per-org Apex CPU during a busy support shift.
- **Security** — `WITH SECURITY_ENFORCED` is the floor.
  `with sharing` on the controller class enforces record-level
  visibility. The combination guarantees the lookup can never
  surface records or fields the user is not entitled to see —
  even if the JS controller mis-routes the data later.

## Architectural Tradeoffs

The main tradeoff is **`lightning-record-picker` (declarative)
vs custom lookup**. The standalone `lightning-record-picker`
(Spring '24+) supports cross-object search, configurable display
info, and filters; it is the preferred choice. Reach for a
custom lookup only when the picker cannot model the requirement
(per-row dynamic filter, custom result rendering, search across
non-Salesforce systems via Apex).

Specifically:

- **Standard "pick a record" UX**: `lightning-record-picker`.
- **Per-row dynamic filter**: custom lookup with a parameterized
  Apex search.
- **Cross-system search**: custom lookup whose Apex method calls a
  Named Credential.
- **Multi-select**: custom lookup with a pill list.

## Anti-Patterns

1. **Un-debounced search.** Every keystroke is a callout;
   exhausts Apex CPU and produces visible lag.
2. **`onclick` on result rows.** Closes the listbox before the
   click registers.
3. **Forgetting FLS enforcement.** Without `WITH SECURITY_ENFORCED`,
   the lookup leaks fields the user can't normally see.

## Official Sources Used

- lightning-record-picker (LWC Component Reference) — https://developer.salesforce.com/docs/component-library/bundle/lightning-record-picker/documentation
- SOSL Reference (Apex Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_sosl.htm
- WITH SECURITY_ENFORCED in SOQL — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_with_security_enforced.htm
- @AuraEnabled cacheable=true — https://developer.salesforce.com/docs/platform/lwc/guide/data-wire-service-about.html
- ARIA combobox role — https://www.w3.org/WAI/ARIA/apg/patterns/combobox/
- Salesforce Well-Architected: Performant — https://architect.salesforce.com/well-architected/performant/efficient
