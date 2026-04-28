# Well-Architected Notes — Apex Trigger Bypass And Killswitch Patterns

## Relevant Pillars

- **Reliability** — A kill switch is a recovery primitive. When a deployed
  trigger is implicated in an outage, ops must be able to disable it in
  seconds without a code deployment. Bypass via Custom Metadata or Custom
  Permission assignment shrinks Mean Time To Recovery from "next deployment
  window" to "minutes".
- **Operational Excellence** — Bypass mechanisms move toggles out of code and
  into configuration, reducing change-management friction for routine
  operations like data loads and integration runs. Combined with
  `Application_Log__c` audit entries, every bypass invocation is observable
  and reviewable.
- **Security** — Adjacent. The Custom Permission gate must be assigned via
  Permission Set (never via a User field), and the bypass capability must be
  scoped to integration / loader users so an admin user cannot self-bypass
  during clicks.

## Architectural Tradeoffs

| Tradeoff | Notes |
|---|---|
| Speed of toggle vs audit depth | Custom Permission assignment is instant but appears only in Setup Audit Trail. CMDT deploy is slower (cache lag) but appears in deployment history. |
| Org-wide vs scoped bypass | CMDT `Is_Active__c = false` disables the handler for everyone. Custom Permission scopes to assigned users. Choose based on whether the disablement is universal or per-actor. |
| Static-state in-transaction bypass vs config bypass | Programmatic `TriggerControl.bypass()` is precise and self-restoring but does not cross transaction boundaries. CMDT and Custom Permission gates persist across transactions. |
| Bypass coverage vs test fidelity | Tests must run with bypass OFF to prove the production path. Over-using `Test.isRunningTest()` short-circuits silently destroys confidence. |

## Anti-Patterns This Skill Helps Avoid

1. **Commenting out trigger code to "temporarily disable".** Leaves no audit
   trail, requires a deployment to enable/disable, and exposes a window
   where production behaviour differs from source.
2. **Bypass checkbox on the User SObject.** Conflates identity with
   capability, lets users self-grant, and bypasses Permission Set Groups.
   Use a Custom Permission instead.
3. **Combining recursion-prevention and bypass in the same flag.** They
   solve different problems; sharing a flag means flipping the kill switch
   accidentally re-enables recursion or vice versa. Keep them separate.

## Official Sources Used

- Apex Developer Guide — Custom Metadata Types in Apex —
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_metadata_custommetadatatypes_using.htm
- Apex Reference Guide — `System.FeatureManagement` Class —
  https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_FeatureManagement.htm
- Salesforce Help — Custom Settings (Hierarchy Custom Settings) —
  https://help.salesforce.com/s/articleView?id=sf.cs_about.htm
- Salesforce Well-Architected — Reliability pillar —
  https://architect.salesforce.com/well-architected/trusted/reliable
- Salesforce Well-Architected — Operational Excellence —
  https://architect.salesforce.com/well-architected/adaptable/resilient
