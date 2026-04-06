# Well-Architected Notes — Standard Object Quirks

## Relevant Pillars

- **Reliability** — Standard object quirks are a primary source of silent data loss and broken automation. Lead conversion dropping unmapped fields, Account deletion orphaning Contacts, and CaseComment isolation all cause production incidents when the platform behavior diverges from developer expectations. Building systems that account for these quirks directly improves reliability by eliminating entire categories of runtime surprises.

- **Security** — PersonAccount dual-nature has direct security implications. A Contact trigger that processes PersonAccount-related Contacts may expose or modify data that the trigger author did not intend to touch. Polymorphic lookups that resolve to Lead records may inadvertently expose unconverted Lead data to users who should only see Contact data. Sharing rules applied to the Account side of a PersonAccount do not automatically propagate to the Contact side in the same way as standalone Contacts.

- **Operational Excellence** — Documenting known quirks as inline code comments and maintaining a quirk checklist reduces the operational burden of onboarding new developers. Teams that do not document these behaviors rediscover them through production incidents, which is expensive and avoidable. Automated checks (like the checker script in this skill) enforce quirk awareness as part of the deployment pipeline.

- **Performance** — Polymorphic queries using TYPEOF are more efficient than the alternative of running separate queries per target type and merging results in Apex. CaseComment triggers that touch parent Cases add DML operations, which must be bulkified to avoid governor limit violations in high-volume service orgs.

- **Scalability** — Lead conversion in bulk scenarios (Data Loader, batch Apex) amplifies the unmapped-field problem because the data loss is multiplied across thousands of records. PersonAccount orgs that grow beyond initial expectations frequently discover that their Contact-focused automation breaks at scale because it was never tested with PersonAccount records.

## Architectural Tradeoffs

1. **Explicit handling vs. simplicity**: Accounting for every standard object quirk adds code complexity (TYPEOF clauses, PersonAccount guards, CaseComment triggers). The tradeoff is worth it because the alternative is silent data loss or broken automation discovered only in production.

2. **Trigger-based field preservation vs. declarative mapping**: Lead field mapping is simpler to maintain but requires manual updates for every new field. Trigger-based preservation is self-maintaining but adds Apex complexity and test coverage requirements.

3. **CaseComment trigger coupling**: Adding a CaseComment trigger that updates the parent Case creates coupling between two objects. This is an acceptable tradeoff because the platform does not provide a declarative way to propagate CaseComment changes to Case.

## Anti-Patterns

1. **Treating standard objects like custom objects** — Assuming that standard object relationships follow the same cascade-delete, trigger-firing, and field-access rules as custom objects. Standard objects have hard-coded behaviors that override general platform rules. Always verify standard object behavior against the Object Reference before building automation.

2. **Ignoring polymorphic lookup resolution** — Writing SOQL queries that use dot-notation on polymorphic fields (WhoId, WhatId) without TYPEOF, then handling the resulting errors by removing the offending fields instead of using the correct pattern. This leads to automation that lacks critical data.

3. **Building PersonAccount logic as an afterthought** — Enabling PersonAccounts in an org that already has Contact-focused automation without retrofitting every Contact trigger, Flow, and report. The dual-nature of PersonAccounts means every piece of Contact logic is affected, and partial retrofitting creates inconsistent behavior.

## Official Sources Used

- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Person Accounts — https://help.salesforce.com/s/articleView?id=sf.account_person.htm
- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
