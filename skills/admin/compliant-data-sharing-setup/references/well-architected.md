# Well-Architected Notes — Compliant Data Sharing Setup

## Relevant Pillars

- **Security** — CDS is the primary platform mechanism for enforcing ethical walls and regulatory data separation in FSC orgs. Correct setup directly determines whether confidential client data is isolated between business lines. The role-hierarchy bypass, explicit participant assignment model, and per-object enablement flags are all security controls. Misconfigurations (wrong OWD, missing "Use CDS" permission, surviving sharing rules) undermine the intended data boundary and can result in compliance failures.

- **Reliability** — CDS introduces a new failure mode absent in standard sharing: a participant assignment that appears to succeed but produces no access grant (due to wrong OWD or missing Deal Management prerequisite). The setup checklist and validation steps in this skill ensure the configuration is testable and produces verifiable, reproducible access grants before production rollout.

## Architectural Tradeoffs

**CDS vs. Standard Sharing Rules for Team Isolation:**
Standard sharing rules can grant access across hierarchy boundaries but cannot prevent access granted by the hierarchy. CDS inverts this: it removes the hierarchy grant entirely and requires explicit assignment. The tradeoff is operational burden — every access grant must be explicit and maintained. For orgs with stable team structures, this is manageable. For orgs with high user turnover, `ParticipantGroup` (managed via the `fsc-compliant-sharing-api` skill) reduces the maintenance cost significantly.

**OWD Change Timing:**
Changing OWD in production triggers a sharing recalculation that can take minutes to hours depending on record volume. Changing OWD and enabling CDS simultaneously compounds the recalculation scope. The recommended pattern is: change OWD first, let recalculation complete, then enable CDS. This allows each change to be independently validated and rolled back if needed.

**Role-Hierarchy Inheritance Removal Is Irreversible in Practice:**
Once business users and managers have operated under CDS for even a short period, any rollback to role-hierarchy inheritance requires recreating the full participant assignment model using standard sharing rules instead — a non-trivial migration. Treat CDS enablement as a long-term architectural commitment, not a toggle that can be easily reversed.

## Anti-Patterns

1. **Enabling CDS without auditing existing sharing rules** — CDS replaces role-hierarchy inheritance but leaves sharing rules untouched. An org with existing criteria-based sharing rules that grant cross-team access will have an incomplete ethical wall even after CDS is enabled. Always audit and remove conflicting sharing rules as part of the CDS rollout.

2. **Assuming CDS is a superset of standard sharing** — CDS is a parallel mechanism, not an extension. It does not block access granted via other paths (sharing rules, manual shares, or Apex managed sharing). Architects who design ethical walls assuming CDS covers all access vectors will produce gaps that are difficult to detect without explicit cross-mechanism testing.

3. **Skipping the OWD prerequisite step** — CDS without Private or Public Read-Only OWD produces a configuration that appears deployed but functions as if CDS were not present. This is a silent misconfiguration that fails only at runtime access testing, not at deploy time.

## Official Sources Used

- Compliant Data Sharing for Financial Services Cloud — https://help.salesforce.com/s/articleView?id=sf.fsc_compliant_data_sharing.htm
- Compliant Data Sharing Setup (Trailhead) — https://trailhead.salesforce.com/content/learn/modules/financial-services-cloud-compliant-data-sharing
- Considerations and Limitations for Compliant Data Sharing — https://help.salesforce.com/s/articleView?id=sf.fsc_compliant_data_sharing_considerations.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
