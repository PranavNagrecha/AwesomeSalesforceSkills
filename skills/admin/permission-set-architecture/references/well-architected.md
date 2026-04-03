# Well-Architected Notes — Permission Set Architecture

## Relevant Pillars

### Security

Permission-set architecture is a Security concern because it is the control plane for feature access. Least privilege depends on capability boundaries, license-aware assignment, and avoiding profile drift that grants more than intended.

### Operational Excellence

Well-run access models reduce admin toil, make audits faster, and allow repeatable onboarding and offboarding. PSG-based bundle design is an operational tool as much as a security one.

### Reliability

Access changes are production changes. An architecture built on reusable bundles is easier to test and less likely to break user workflows when one entitlement changes.

## Architectural Tradeoffs

- **Thin profiles vs short-term convenience:** Keeping profiles minimal takes more design discipline up front, but it prevents long-term access sprawl.
- **Reusable PSGs vs many direct assignments:** Direct assignment is faster in the moment, but PSGs scale better for review, provisioning, and change management.
- **Shared bundles plus muting vs cloned bundles:** Muting preserves reuse, while cloned bundles can be clearer for radically different personas. Use muting sparingly.

## Anti-Patterns

1. **Profile per persona or exception** — this produces brittle access drift and makes every feature change a profile-maintenance task.
2. **Giant permission sets with no capability ownership** — access becomes impossible to review because one metadata object grants unrelated privileges.
3. **Muting-first architecture** — excessive subtractive exceptions hide the fact that the base bundle model is wrong.

## Official Sources Used

- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
