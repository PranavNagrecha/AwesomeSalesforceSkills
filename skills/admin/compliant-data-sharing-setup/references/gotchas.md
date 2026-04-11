# Gotchas — Compliant Data Sharing Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Managers Do Not Inherit Subordinate Records Under CDS

**What happens:** After CDS is enabled on Account, a regional manager who previously saw all accounts owned by their direct reports and subordinates suddenly loses that access. The manager's record count in list views drops to zero for records they don't own directly, and they report CDS as "broken" or "blocking legitimate access."

**When it occurs:** Any time CDS is enabled on an object where managers relied on role-hierarchy inheritance to see team records. This is the design intent of CDS — it is working correctly — but it surprises every org that enables it without explicit role-hierarchy audit.

**How to avoid:** Before enabling CDS, identify all manager users who relied on hierarchy inheritance and create explicit Participant Role assignments for each record they need to access. Consider using `ParticipantGroup` (via the `fsc-compliant-sharing-api` skill) to manage team-level access efficiently. Document this behavior in change management materials so managers understand the transition.

---

## Gotcha 2: Disabling CDS Requires Deleting All Participant Role Assignments First

**What happens:** An administrator attempts to disable CDS for an object (e.g., by setting `enableCompliantDataSharingForAccount = false` in IndustriesSettings or via a Salesforce Support ticket). The platform returns an error or the support team refuses to proceed because active `AccountParticipant` records exist on the org.

**When it occurs:** Any attempt to deactivate CDS while participant records are present. Salesforce blocks deactivation to prevent orphaned share rows and incomplete access states. The error message is not always descriptive about the root cause.

**How to avoid:** Before initiating a CDS deactivation, query and delete all participant records for the target object. For Account: `SELECT Id FROM AccountParticipant` — delete all results. For Opportunity: `SELECT Id FROM OpportunityParticipant`. For Financial Deal: query `FinancialDealParticipant`. Once all participant records are cleared, the deactivation request can proceed. This cleanup often requires bulk data operations (Data Loader or Apex batch) for orgs with large participant sets.

---

## Gotcha 3: CDS and Standard Sharing Rules Run Simultaneously and Independently

**What happens:** An admin enables CDS expecting it to replace the existing sharing model entirely. But existing sharing rules (criteria-based or owner-based) continue to function independently. Users who were previously visible to each other via a sharing rule remain visible after CDS enablement, even across business lines the admin intended to separate.

**When it occurs:** Any org that has existing sharing rules on CDS-enabled objects. CDS disables role-hierarchy inheritance; it does not deactivate, override, or interact with sharing rules. Both access paths coexist.

**How to avoid:** Audit all sharing rules on target objects before enabling CDS. Specifically identify rules that grant cross-team or cross-line access and delete or disable them as part of the CDS rollout. Treat CDS enablement as a sharing model migration, not just an additive feature toggle.

---

## Gotcha 4: OWD Must Be Private or Public Read-Only Before Enabling CDS

**What happens:** CDS is enabled in IndustriesSettings while the target object's OWD is still Public Read/Write. Participant Role assignments are created and appear to save successfully, but no share rows are written because there is nothing for the CDS engine to extend — every user already has full access via OWD. CDS appears completely non-functional.

**When it occurs:** Any enablement sequence where OWD is changed after CDS is turned on, or where OWD is accidentally left at Public Read/Write during testing and then forgotten.

**How to avoid:** Always verify and change OWD before enabling CDS per object. The sequence must be: (1) OWD to Private → (2) sharing recalculation completes → (3) CDS enabled. Reversing steps 1 and 3 produces a configuration that looks enabled but produces no access grants.

---

## Gotcha 5: Financial Deal CDS Requires Deal Management to Be Enabled First

**What happens:** An admin enables `enableCompliantDataSharingForFinancialDeal = true` in IndustriesSettings but Deal Management has never been activated for the org. The Financial Deal Participants related list is not available on page layouts, participant record inserts have no effect, and the Setup UI for CDS configuration for Financial Deal shows no options.

**When it occurs:** Any org enabling Financial Deal CDS without first activating Deal Management under Setup > Financial Services > Financial Deal Settings.

**How to avoid:** Verify Deal Management is enabled as the first step in any Financial Deal CDS rollout. This is an independent feature flag from CDS itself and must be enabled separately. After Deal Management is enabled, the Financial Deal Participants related list becomes available in the page layout editor and CDS for Financial Deal functions normally.
