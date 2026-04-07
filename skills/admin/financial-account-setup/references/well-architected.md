# Well-Architected Notes — Financial Account Setup

## Relevant Pillars

### Security (Trusted)

Financial account data is regulated in most jurisdictions. The FSC data model stores balance information, account numbers, beneficiary designations, and financial goal details — all of which are subject to financial privacy regulations (GLBA, MiFID II, PIPEDA) and firm-level data governance policies.

Key security requirements for FSC financial account configuration:
- **Field-Level Security:** Balance fields, account number fields, and held-away indicator fields should be restricted to relevant roles (advisors, operations) with read-only access for most users. FLS on `FinServ__Balance__c` and `FinServ__FinancialAccountNumber__c` should be reviewed in every profile and permission set.
- **Object-Level Access:** `FinancialAccountRole` records reveal account ownership structures. The object OWD should be Private or Controlled by Parent; sharing rules should limit access to relationship managers and compliance officers.
- **Held-Away Account Edit Prevention:** Validation rules or permission-based restrictions must prevent unauthorized edits to externally-sourced balance data (see gotchas.md for implementation pattern).
- **Audit Trail:** For regulated orgs (broker-dealers, RIAs, banks), Field Audit Trail (Salesforce Shield) on `FinancialAccount` balance fields provides the immutable change history that regulators may require. Evaluate Shield necessity if the org holds GLBA-regulated data.

### Reliability

The FSC rollup engine is a batch process. Rollup accuracy is critical for advisor dashboards, compliance reports, and client-facing portals. Reliability risks include:
- **Stale rollups after bulk loads:** Rollup batch must be triggered after bulk data operations (see gotchas.md — Gotcha 5).
- **Rollup gap for cross-household joint owners:** The managed-package rollup engine will never cover cross-household joint owner balances. This is a known platform gap, not a transient error. Any SLA around "complete household asset view" must account for this limitation and document the custom workaround.
- **Integration reliability for held-away accounts:** Held-away account balances depend on an external data feed. An integration failure will result in stale balance data in FSC. Implement retry logic, alerting on failed balance updates, and a data freshness indicator field on `FinancialAccount` to surface stale records to advisors.

### Operational Excellence

A well-configured FSC financial account setup requires ongoing operational discipline:
- **Picklist governance:** The `FinancialAccountType` picklist must be change-controlled. Additions, modifications, and deprecations should follow the Replace workflow (never delete) and be tested against dependent validation rules and page layouts before production deployment.
- **Namespace documentation:** For managed-package orgs, all configuration documentation must use the `FinServ__` namespace consistently. When the org eventually migrates to Core FSC (if planned), a migration runbook using the documented API names will be required.
- **Rollup batch scheduling:** The FSC rollup batch should be scheduled during off-peak hours and monitored for failures via the Apex Jobs page. A failed rollup batch means advisor dashboards show incorrect data — configure an Apex exception email notification.
- **FinancialAccountRole lifecycle:** When a client relationship ends or a beneficiary designation changes, `FinancialAccountRole` records must be deactivated (set `Active = false`) rather than deleted, to preserve the historical relationship record for compliance purposes.

---

## Architectural Tradeoffs

### Managed-Package FSC vs Core FSC

The managed-package deployment is the dominant pattern in orgs that implemented FSC before Winter '23. It provides a stable, tested data model but introduces the `FinServ__` namespace dependency across all customization. The Core FSC model (standard platform objects) offers cleaner API names, tighter platform integration (e.g., standard sharing model behavior), and no namespace risk — but orgs migrating from managed-package to Core FSC require a full metadata migration project.

**Tradeoff:** Remain on managed-package for stability and avoid migration cost, accepting the namespace complexity and potential package upgrade dependency. Or migrate to Core FSC for a cleaner long-term foundation, accepting the significant short-term migration project cost.

### Native Rollup vs Custom Rollup for Cross-Household Visibility

The managed-package rollup engine is tested, supported, and upgrade-safe. Extending it to cover cross-household joint owner balances requires modifying managed package behavior (not supported) or building a parallel custom rollup. A custom rollup introduces maintenance overhead and must be re-validated after every FSC package upgrade.

**Tradeoff:** Accept the native rollup boundary and train advisors on the limitation (lower cost, no maintenance), or build a custom rollup to a separate custom field (higher fidelity, ongoing maintenance obligation).

---

## Anti-Patterns

1. **Overloading the native FSC rollup fields with custom writes** — Writing to `FinServ__TotalBalance__c` or other managed package rollup fields from custom Apex or Flows will conflict with the FSC batch rollup and result in unpredictable values after the next rollup run. Always write custom rollup results to custom fields you own.

2. **Single record type for all account types** — Using one record type and one page layout for all `FinancialAccountType` values produces a cluttered, confusing user experience and forces advisors to see irrelevant fields (e.g., RMD age on a checking account). A separate record type per account category (retirement, brokerage, deposit, insurance, education) is the standard FSC configuration pattern.

3. **Relying on `FinServ__PrimaryOwner__c` lookup instead of `FinancialAccountRole` records** — The lookup field is a display convenience. The rollup engine, relationship model, and FSC components read from `FinancialAccountRole`. Skipping role records produces accounts that appear configured but do not roll up to households. (See examples.md Anti-Pattern section for full detail.)

---

## Official Sources Used

- FSC Financial Accounts — https://help.salesforce.com/s/articleView?id=sf.fsc_financial_accounts.htm
- FSC Financial Account Roles — https://help.salesforce.com/s/articleView?id=sf.fsc_financial_account_roles.htm
- FinancialAccount Standard Object (Core FSC) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_financialaccount.htm
- FSC Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.financial_services_cloud_object_reference.meta/financial_services_cloud_object_reference/fsc_api_intro.htm
- Salesforce Well-Architected: Trusted Pillar — https://architect.salesforce.com/docs/architect/well-architected/guide/trusted.html
- Salesforce Well-Architected: Reliable Pillar — https://architect.salesforce.com/docs/architect/well-architected/guide/reliable.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
