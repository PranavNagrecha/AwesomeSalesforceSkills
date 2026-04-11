# Well-Architected Notes — NPSP Trigger Framework Extension (TDTM)

## Relevant Pillars

- **Reliability** — The DmlWrapper contract is the primary reliability pillar here. Handlers that issue direct DML break the NPSP dispatcher's batching guarantee, causing recursive trigger execution, unpredictable state, and governor limit failures in bulk operations. Following the DmlWrapper pattern ensures the handler participates cleanly in NPSP's managed transaction.
- **Adaptable** — Registering handlers via `npsp__Trigger_Handler__c` records rather than modifying packaged code makes the customization metadata-driven and upgrade-safe. Setting `npsp__Owned_by_Namespace__c` correctly keeps the customization stable across NPSP upgrades — this is the primary adaptability concern in this domain.
- **Security** — Custom TDTM handlers run in the security context of the triggering user or the batch process. Handlers that operate on sensitive fields (e.g., financial, clinical, or PII fields common in nonprofit orgs) must enforce CRUD/FLS where the handler issues queries or builds DML wrapper objects. The managed DmlWrapper is not exempt from sharing rules; consider whether `with sharing` or `without sharing` is appropriate for each handler class.
- **Performance** — Load order and DmlWrapper batching are the main performance levers. Handlers placed before packaged handlers on an object can degrade performance if they issue heavy queries before NPSP's own caching has run. Handlers at order 100+ run after packaged handlers, avoiding this. Bulkification inside `run()` is mandatory — always iterate over `newlist` as a list, never query inside a loop.

## Architectural Tradeoffs

**TDTM handler vs. Flow vs. Platform Event:** TDTM handlers are appropriate when: (a) the logic must run synchronously in the same transaction as NPSP's own trigger logic, (b) the volume is high enough that Flow CPU limits or bulkification issues are a concern, or (c) the logic requires access to data states that only exist mid-transaction (e.g., checking payment records created by NPSP before the transaction commits). For low-volume, declarative-first orgs, a Flow triggered after NPSP handlers may be simpler and more maintainable.

**Managed vs. unmanaged handler registration:** Handler records can be deployed as part of a data deployment (using a post-install script or data files) or as Apex code (inserted in a test or post-install Apex class). For ISVs or managed packages, use a post-install Apex class to create the handler records. For org-specific customizations, deploy via a dataset or use Salesforce Data Deploy tools to manage the `npsp__Trigger_Handler__c` records alongside the Apex class.

**Recursion guard design:** Because TDTM does not provide a public recursion control API for custom handlers, each handler must implement its own static `Set<Id>` guard. This adds boilerplate but provides fine-grained control. For handlers that create records on the same object they are registered on, the guard is mandatory.

## Anti-Patterns

1. **Issuing Direct DML Inside run()** — Breaks the NPSP dispatcher's transaction contract. All DML must go through `DmlWrapper`. Direct DML inside a TDTM handler causes recursive dispatch, doubles governor limit consumption, and can produce duplicate records or corrupt NPSP rollup state.

2. **Omitting npsp__Owned_by_Namespace__c** — Leaving this field blank causes the handler record to be deleted by NPSP package upgrades. The deletion is silent — no error, no warning, no deploy failure. The feature simply stops working after the next upgrade.

3. **Using getTdtmConfig() Before setTdtmConfig() in Tests** — Causes the custom handler to be silently dropped from the test execution context due to a static cache collision. Tests pass vacuously without ever invoking the custom handler. This anti-pattern is particularly dangerous because there is no failure signal.

## Official Sources Used

- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Apex Reference Guide — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Deploy a Custom Apex Class in the TDTM Framework for NPSP — https://help.salesforce.com/s/articleView?id=sfdo.npsp_deploy_apex_tdtm
- Manage Trigger Handlers for NPSP — https://help.salesforce.com/s/articleView?id=sfdo.NPSP_Manage_Trigger_Handlers
