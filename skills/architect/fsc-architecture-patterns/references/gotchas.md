# Gotchas — FSC Architecture Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: CDS Enforcement Requires Private OWD — Enabling CDS Alone Is Insufficient

**What happens:** An architect enables Compliant Data Sharing in FSC Settings and configures CDS share sets, then discovers during a security audit that advisors can still see all financial account records regardless of their `FinancialAccountRole` assignments. CDS appears configured but is effectively inert.

**When it occurs:** When the default Organization-Wide Default (OWD) for `FinancialAccount` is set to Public Read/Write or Public Read-Only. CDS share sets grant additional access on top of OWD; they do not restrict access below it. If OWD already gives everyone visibility, there is nothing for CDS to narrow.

**How to avoid:** Set the OWD for `FinancialAccount` to Private before enabling CDS. Verify the OWD setting in `Setup > Sharing Settings` after CDS activation. Test with a user who holds no `FinancialAccountRole` records and confirm they see zero financial account records. Include OWD validation as a required step in the CDS activation checklist.

---

## Gotcha 2: Managed-Package and Platform-Native FSC Cannot Coexist — Sandbox Contamination Is Irreversible Without a Refresh

**What happens:** A developer installs the `FinServ__` managed package in a sandbox that was configured for platform-native FSC (or vice versa) to test a third-party AppExchange product that requires the managed package. Object naming conflicts arise, FSC Settings becomes inconsistent, and the sandbox is in an unsupported hybrid state. The only recovery is a full sandbox refresh.

**When it occurs:** When sandbox org topology is not actively enforced. Common triggers: AppExchange trial installs, a new developer following old FSC documentation that instructs managed-package installation, or an automated sandbox seeding script that installs packages without checking for platform-native FSC configuration.

**How to avoid:** Document explicitly in the project's sandbox management runbook that managed-package FSC (`FinServ__`) must not be installed in any org configured for platform-native FSC. Create a sandbox governance checklist item that verifies this before any package installation. If you must test an AppExchange product that requires the managed package, use a dedicated isolated sandbox, not any sandbox in the platform-native pipeline.

---

## Gotcha 3: FSC Rollup Batch Does Not Self-Heal After Failure — Stale Household KPIs Silently Persist

**What happens:** The FSC rollup batch (which aggregates household-level financial data like Total Assets Under Management, total financial goals, and net worth) fails due to a governor limit violation or a data quality issue. The batch does not retry or alert automatically. Household-level rollup fields show stale values indefinitely. Advisors and branch managers see incorrect household KPIs without any platform-visible error message.

**When it occurs:** After bulk data loads that introduce malformed `FinancialHolding` or `FinancialAccount` records, after governor limit increases due to an automation change, or when the batch schedule is disrupted by an org maintenance window that is not followed by a manual re-run.

**How to avoid:** Configure the rollup batch schedule in FSC Settings and supplement it with a Scheduled Apex job that monitors the batch completion status and fires an alert if the batch has not completed successfully within its expected window. Include "check rollup batch last-run timestamp" in the daily operational monitoring checklist. Document the re-run procedure (`FSCSettings.runRollups()` or through the FSC Settings UI batch trigger) in the operational runbook so any admin can execute it without developer involvement.

---

## Gotcha 4: CDS Does Not Automatically Apply to External (Experience Cloud) Users

**What happens:** An org has Compliant Data Sharing properly configured for internal advisors. The team adds an Experience Cloud portal for clients to view their own financial accounts. Portal users (Customer Community Plus license) are assigned a profile and OWD for external users. A misconfiguration in the external-user OWD allows portal users to see financial account records belonging to other clients, bypassing the CDS restrictions that protect internal users.

**When it occurs:** CDS controls internal user sharing. External user access is governed by the external-user OWD, Experience Cloud sharing sets, and sharing rules defined for external users separately. If an architect configures CDS thoroughly for internal users but does not review the external-user sharing model, the two systems operate independently with potentially contradictory results.

**How to avoid:** After designing CDS for internal users, conduct a separate security review for any Experience Cloud users who access FSC data. Set the external-user OWD for `FinancialAccount` to Private. Use Experience Cloud sharing sets to grant each portal user access only to their own financial accounts. Run a sharing inspection on at least one external user test account before go-live to confirm they cannot see any financial accounts other than their own.

---

## Gotcha 5: Person Account Disablement After FSC Data Exists Is Destructive and Unsupported

**What happens:** An org enables FSC — which requires Person Accounts — and accumulates client `Person Account` records. A business decision later determines that the org should be restructured to use standard Contacts and Business Accounts instead. Attempting to disable Person Accounts at this point is blocked by Salesforce if any Person Account records exist, and there is no supported migration path to convert `Person Account` records to standard `Contact + Account` pairs.

**When it occurs:** When the Person Account enablement decision is made without executive sign-off, or when an FSC pilot org is merged into a larger existing org where Person Accounts were deliberately not enabled. In the latter case, the merge requires either accepting Person Accounts in the merged org or abandoning the FSC data from the pilot.

**How to avoid:** Person Account enablement must be treated as a permanent, irreversible org-level decision. Obtain explicit stakeholder sign-off before enabling in any production org or production-path sandbox. Document this constraint in the architecture decision record. If there is any uncertainty about long-term data model direction, resolve that uncertainty in a discovery phase before enabling FSC in any org that will eventually become production.
