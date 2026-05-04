# Well-Architected Notes — Net Zero Cloud Setup

## Relevant Pillars

- **Reliability** — Carbon disclosure totals are externally audited and may carry legal liability under CSRD or SEC Climate Disclosure rules. Calculation jobs must run reliably; restated totals must be traceable to the factor change that drove them. DPE job monitoring and audit logging are non-optional.
- **Security** — Emission data, supplier engagement scoring, and unverified Scope 3 estimates can be commercially sensitive. Restrict access to the Sustainability objects via a dedicated permission set; limit external sharing of calculation outputs.
- **Operational Excellence** — Annual factor refresh cycles (DEFRA, EPA, IEA) require recurring restatement workflows. Build the restatement workflow as a runbook, not a one-off project task.

## Architectural Tradeoffs

**Salesforce-Bundled vs. Custom Factor Sets:** Bundled sets (DEFRA, EPA, IEA) are maintained by Salesforce and refresh on the publisher cadence — low operational burden. Custom sets are required for auditor-specified factors but carry the burden of source documentation, effective dating, and refresh management. Default to bundled; justify each custom factor.

**Spend-Based vs. Supplier-Specific Scope 3 Cat. 1:** Spend-based estimation is fast (load ERP spend, multiply by industry factor) but carries 30%+ uncertainty. Supplier-specific data reduces uncertainty but requires multi-year supplier engagement programs. Most orgs progress from spend-based → hybrid → supplier-specific over 3–5 year cycles.

**Loading All 15 Scope 3 Categories vs. Material Subset:** Loading all 15 produces noise that can crowd out genuinely material categories in disclosure narratives. Material-only reporting (with documented exclusions) is auditor-acceptable and operationally sustainable. The materiality screen happens once per disclosure cycle, not per data load.

**Real-Time Calculation vs. Periodic DPE Batch:** DPE batch is correct for carbon accounting because activity data arrives in periodic feeds (utility bills, ERP exports) rather than real-time streams. Real-time recalc is unnecessary and would consume DPE quota disproportionately.

## Anti-Patterns

1. **Skipping Carbon Calculation DPE Activation** — Most common Net Zero Cloud go-live failure. Activity data sits stranded in `…EnrgyUse` rows; disclosure pack shows zero totals.

2. **Loading All 15 Scope 3 Categories Without Materiality Screen** — Produces noisy disclosures that mask material categories and burn DPE quota on low-value calculations.

3. **Manual Edits to Calculated Totals** — Overwritten on next DPE run, and an audit-trail risk regardless. Corrections belong at the activity-data or factor layer.

4. **Custom Factor Sets Without Source Documentation** — Auditor reviews fail when custom factors lack documented sources, effective dates, and approval references.

5. **Co-mingling CSRD and TCFD Mappings in One Disclosure Pack** — Each framework has distinct metric definitions and aggregation rules. Use one pack per framework to keep mappings auditable.

## Official Sources Used

- Net Zero Cloud (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sf.netzero_cloud.htm&type=5
- Net Zero Cloud Object Reference (`StnryAssetCrbnFtprnt`, `Scope3CrbnFtprnt`, `EmssnFctr`) — https://developer.salesforce.com/docs/atlas.en-us.netzero_cloud_dev.meta/netzero_cloud_dev/netzero_cloud_intro.htm
- Salesforce Industries Common Resources Developer Guide (Data Processing Engine, Batch Management) — https://developer.salesforce.com/docs/atlas.en-us.industries_dev.meta/industries_dev/industries_dev_intro.htm
- GHG Protocol Corporate Accounting and Reporting Standard — https://ghgprotocol.org/corporate-standard
- GHG Protocol Scope 2 Guidance (dual-method reporting) — https://ghgprotocol.org/scope-2-guidance
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
