# Well-Architected Notes — Compliant Data Sharing Setup

UNVERIFIED (2026-10-20): every statement in this file that CDS bypasses, removes or replaces role-hierarchy inheritance — the corpus documents the CDS flags, ParticipantRole and participant groups, not the bypass.

## Relevant Pillars

- **Security** — CDS is the primary platform mechanism for enforcing ethical walls and regulatory data separation in FSC orgs. Correct setup directly determines whether confidential client data is isolated between business lines. The role-hierarchy bypass, explicit participant assignment model, and per-object enablement flags are all security controls. Misconfigurations (wrong OWD, missing Use Compliant Data Sharing permission, surviving sharing rules) undermine the intended data boundary and can result in compliance failures.

- **Reliability** — CDS introduces a new failure mode absent in standard sharing: a participant assignment that appears to succeed but produces no access grant (UNVERIFIED (2026-10-20): due to wrong OWD or missing Deal Management — no corpus line). The setup checklist and validation steps in this skill ensure the configuration is testable and produces verifiable, reproducible access grants before production rollout.

## Architectural Tradeoffs

**CDS vs. Standard Sharing Rules for Team Isolation:**
Standard sharing rules can grant access across hierarchy boundaries but cannot prevent access granted by the hierarchy. CDS inverts this: it removes the hierarchy grant entirely and requires explicit assignment. The tradeoff is operational burden — every access grant must be explicit and maintained. For orgs with stable team structures, this is manageable. For orgs with high user turnover, participant groups (Group `Type` Participant, object_reference 264 L155375-155379; managed via `apex/fsc-compliant-sharing-api`) reduce the maintenance cost.

**OWD Change Timing:**
Changing OWD in production runs a sharing recalculation, longer with more data (secguide 262 L2785-2786). Changing OWD and enabling CDS simultaneously compounds the recalculation scope. The recommended pattern is: change OWD first, let recalculation complete, then enable CDS. This allows each change to be independently validated and rolled back if needed.

**Role-Hierarchy Inheritance Removal Is Irreversible in Practice:**
Once business users and managers have operated under CDS for even a short period, any rollback to role-hierarchy inheritance requires recreating the full participant assignment model using standard sharing rules instead — a non-trivial migration. Treat CDS enablement as a long-term architectural commitment, not a toggle that can be easily reversed.

## Anti-Patterns

1. **Enabling CDS without auditing existing sharing rules** — CDS replaces role-hierarchy inheritance but leaves sharing rules untouched. An org with existing criteria-based sharing rules that grant cross-team access will have an incomplete ethical wall even after CDS is enabled. Always audit and remove conflicting sharing rules as part of the CDS rollout.

2. **Assuming CDS is a superset of standard sharing** — CDS is a parallel mechanism, not an extension. It does not block access granted via other paths (sharing rules, manual shares, or Apex managed sharing). Architects who design ethical walls assuming CDS covers all access vectors will produce gaps that are difficult to detect without explicit cross-mechanism testing.

3. **Skipping the OWD prerequisite step** — UNVERIFIED (2026-10-20): that CDS without Private or Public Read-Only OWD appears deployed but functions as if CDS were not present. This is a silent misconfiguration that fails only at runtime access testing, not at deploy time.

## Official Sources Used

- IndustriesSettings CDS flags (Account, CustomObjects, Interaction, InteractionSummary, Opportunity) — api_meta 264 L122543-122578
- `enableDealManagement` and `enableFinancialDealRoleHierarchy` — api_meta 264 L122580-122582, L122614-122616
- ParticipantRole: suffix, API 50.0, defaultAccessLevel Edit/None/Read, parentObject values — api_meta 264 L97087-97153
- Participant group type and the Use Compliant Data Sharing permission — object_reference 264 L155375-155379
- OWD updates run a sharing recalculation — secguide 262 L2785-2786
- Sharing-rule RowCause `Rule` on AccountShare — object_reference 264 L17480
- Compliant Data Sharing for Financial Services Cloud — https://help.salesforce.com/s/articleView?id=sf.fsc_compliant_data_sharing.htm
- Compliant Data Sharing Setup (Trailhead) — https://trailhead.salesforce.com/  (page retired — see host index for current equivalent)
- Considerations and Limitations for Compliant Data Sharing — https://help.salesforce.com/s/articleView?id=sf.fsc_compliant_data_sharing_considerations.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
