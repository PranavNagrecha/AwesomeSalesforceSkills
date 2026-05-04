---
name: net-zero-cloud-setup
description: "Use this skill when configuring Salesforce Net Zero Cloud — including Scope 1/2/3 emission source modeling via the StnryAssetCrbnFtprnt / VehicleAssetCrbnFtprnt / Scope3CrbnFtprnt object families, emission factor library setup (EmssnFctr / EmssnFctrSet), DPE-driven carbon calculation jobs, supplier engagement scoring, and CSRD / ESRS / TCFD disclosure pack mapping. Triggers on: Net Zero Cloud setup, Sustainability Cloud carbon accounting, Scope 1 2 3 emissions Salesforce, emission factor library, supplier engagement Net Zero, ESG disclosure pack mapping. NOT for ESG content scoring (use Marketing Cloud), NOT for general financial reporting (use Accounting Subledger), NOT for energy-only utility billing (use Energy & Utilities Cloud)."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
tags:
  - net-zero-cloud
  - sustainability-cloud
  - carbon-accounting
  - scope-1
  - scope-2
  - scope-3
  - emission-factors
  - csrd
  - esrs
  - tcfd
  - data-processing-engine
  - industry-cloud
inputs:
  - "Net Zero Cloud license enabled on the org"
  - "Inventory of emission sources by scope (stationary assets, vehicles, purchased goods, business travel, etc.)"
  - "Activity data feeds (utility bills, fuel logs, expense systems, supplier emissions data)"
  - "Disclosure framework in scope (CSRD, ESRS, TCFD, SBTi, GHG Protocol)"
outputs:
  - "Configured emission source records with activity data and emission factor links"
  - "Activated DPE-driven carbon calculation jobs producing CrbnFtprnt totals"
  - "Supplier engagement scoring with Scope3PcmtItem records for purchased-goods category"
  - "Disclosure-pack mapping ready for CSRD / ESRS / TCFD reporting"
triggers:
  - "configuring Salesforce Net Zero Cloud from scratch"
  - "Scope 1 / Scope 2 / Scope 3 carbon accounting in Salesforce"
  - "loading emission factor library Net Zero Cloud"
  - "DPE carbon calculation job not running or stale totals"
  - "supplier engagement scoring CSRD ESRS disclosure"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-03
---

# Net Zero Cloud Setup

This skill activates when a practitioner is configuring Salesforce Net Zero Cloud (formerly Sustainability Cloud) — the industry cloud for greenhouse-gas inventory, carbon accounting, supplier engagement, and ESG disclosure. It covers the Scope 1 / 2 / 3 object families, emission factor library setup, DPE-driven carbon calculation, and disclosure-framework mapping. It does NOT cover Marketing Cloud ESG content scoring, generic financial reporting, or utility-billing flows that aren't carbon-related.

---

## Before Starting

Gather this context before working in this domain:

- Confirm Net Zero Cloud license is provisioned. The Scope 1/2/3 object families (`StnryAssetCrbnFtprnt`, `VehicleAssetCrbnFtprnt`, `Scope3CrbnFtprnt`, `Scope3EmssnSrc`, `Scope3PcmtItem`, `EmssnFctr`, `EmssnFctrSet`) appear in Object Manager only after license activation.
- Identify the **disclosure framework** in scope: CSRD / ESRS for EU operations, SEC Climate Disclosure for US public filers, TCFD for voluntary, SBTi for science-based targets, GHG Protocol as the universal underpinning. The framework drives which scopes and categories are mandatory.
- Identify activity data sources for each scope. Scope 1 = direct fuel / refrigerant logs. Scope 2 = utility bills (location-based vs market-based). Scope 3 = the 15 categories from purchased goods to franchises — most companies omit categories that don't apply.
- Decide whether emission factors come from a vendor library (EPA, DEFRA, IEA bundled by Salesforce) or a custom factor set negotiated with an auditor. Custom factors require the most up-front work.

---

## Core Concepts

### The Three-Scope Object Hierarchy

Net Zero Cloud splits the inventory into three scope buckets, each with its own object family:

**Scope 1 — Direct Emissions** (e.g., on-site fuel combustion, fleet fuel, refrigerant leaks):
- `StnryAssetCrbnFtprnt` — stationary asset (building, plant, generator) with fuel-burn activity data.
- `StnryAssetEnrgyUse` — energy use rows attached to a stationary asset.
- `VehicleAssetCrbnFtprnt` — vehicle asset (owned fleet) with fuel-use activity data.
- `RentalCarEnrgyUse` — short-term vehicle rentals (treated as Scope 1 in some frameworks, Scope 3 Cat. 6 in others).

**Scope 2 — Purchased Energy** (e.g., grid electricity, district heating):
- Same `StnryAssetCrbnFtprnt` / `StnryAssetEnrgyUse` objects, but the energy type marks it as purchased rather than combusted.
- Location-based vs. market-based methods are tracked via the emission factor selection on each row.

**Scope 3 — Value-Chain Emissions** (the 15 GHG Protocol categories):
- `Scope3CrbnFtprnt` — top-level Scope 3 footprint per category per period.
- `Scope3EmssnSrc` — source records (e.g., specific supplier, specific business-travel program).
- `Scope3PcmtItem` — purchased-goods category line items.
- `Scope3PcmtSummary` — purchased-goods category summary.
- `StnryAssetEnvrSrc` — environmental source linkage on the stationary asset.

### Emission Factor Library

`EmssnFctr` rows are the per-activity coefficients (e.g., 2.31 kg CO2e per liter of diesel). They live inside `EmssnFctrSet` collections (e.g., "EPA 2024 GHGRP Factors", "DEFRA 2024 UK Factors").

Net Zero Cloud ships several Salesforce-curated factor sets out of the box. Custom sets are required when:

- An auditor specifies a non-bundled regional factor (e.g., a specific country's grid factor).
- The org has internal lifecycle assessment data for a custom factor.
- A supplier-specific factor is provided (Scope 3 Cat. 1 supplier-specific method).

### DPE-Driven Carbon Calculation

Like the rest of the Industries platform, Net Zero Cloud uses DPE batch jobs to multiply activity data × emission factor and produce the `…CrbnFtprnt` rows. The calculation jobs are **not automatic** — they must be activated.

A typical setup activates:

- **Stationary Asset Carbon Calculation** — produces `StnryAssetCrbnFtprnt` from activity data.
- **Vehicle Asset Carbon Calculation** — produces `VehicleAssetCrbnFtprnt`.
- **Scope 3 Calculation** definitions per category (purchased goods, business travel, employee commute, etc.).

Re-running the calculation after a factor set update is required to refresh historical totals.

### Supplier Engagement (Scope 3 Category 1)

Purchased Goods & Services is typically the largest Scope 3 category for non-extractive industries. Net Zero Cloud uses:

- `Scope3PcmtItem` — line items from purchase records (often loaded from ERP spend data).
- Supplier scoring via the Supplier Engagement feature — assigns each supplier a maturity level (e.g., "Reports Scope 1 & 2", "Has Verified Targets") and uses supplier-specific factors when available, falling back to spend-based factors otherwise.

### Disclosure Pack Mapping

The output of Net Zero Cloud is a disclosure-ready pack mapped to a regulatory framework. Common targets:

- **CSRD / ESRS E1** (EU Corporate Sustainability Reporting Directive — Climate Change disclosure).
- **TCFD** (Task Force on Climate-Related Financial Disclosures).
- **CDP Climate Change Questionnaire** (annual voluntary).
- **GHG Protocol Corporate Standard** (universal).

The mapping happens in the disclosure pack configuration: which CrbnFtprnt totals roll into which disclosure metric.

---

## Common Patterns

### Pattern 1: Initial Carbon Inventory Setup

**When to use:** First-time Net Zero Cloud deployment.

**How it works:**

1. Choose the emission factor set(s) appropriate to operating regions. Activate the Salesforce-curated sets for those regions; create custom sets only if regulator or auditor requires.
2. Load stationary assets (buildings, plants) with `StnryAssetCrbnFtprnt` parent records and `StnryAssetEnrgyUse` activity rows for each fuel/electricity type per period.
3. Load fleet assets via `VehicleAssetCrbnFtprnt`.
4. For Scope 3, decide which of the 15 categories are material. Load activity data only for material categories.
5. Activate the carbon calculation DPE definitions for Scope 1 / 2 / 3 categories in scope.
6. Run the calculations once to backfill, then schedule recurring runs.

### Pattern 2: Refreshing Historical Totals After Factor Update

**When to use:** A factor set is updated (e.g., DEFRA publishes new annual factors, or an auditor specifies a corrected regional grid factor).

**How it works:**

1. Activate the new factor set (or update the relevant `EmssnFctr` rows in a custom set).
2. Reassign affected `StnryAssetEnrgyUse` / `VehicleAssetCrbnFtprnt` / `Scope3CrbnFtprnt` rows to the new factor set / factor (often via a DPE definition).
3. Re-run the carbon calculation DPE for the affected periods.
4. Verify the disclosure-pack metrics now reflect the updated factors.
5. Document the factor change in the audit log — auditors require traceability.

### Pattern 3: Supplier Engagement for Purchased Goods

**When to use:** Org wants to move from spend-based Scope 3 Cat. 1 estimation to supplier-specific factors.

**How it works:**

1. Load supplier list and link to `Account` records.
2. Score suppliers via the Supplier Engagement feature (or manually attach maturity level).
3. For suppliers with verified emissions data, attach supplier-specific `EmssnFctr` records.
4. Reload `Scope3PcmtItem` rows; the calculation engine uses supplier-specific factors when available, falls back to spend-based otherwise.
5. Track over time: improving the supplier engagement score reduces estimation uncertainty.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Stationary asset (building) emissions | `StnryAssetCrbnFtprnt` + `StnryAssetEnrgyUse` per fuel/electricity type | Standard parent-child structure; do not flatten activity into the asset record |
| Owned vehicle fleet | `VehicleAssetCrbnFtprnt` | Standard object; do not reuse Automotive Cloud `Vehicle` for emissions tracking |
| Purchased goods (Scope 3 Cat. 1) | `Scope3PcmtItem` from ERP spend data | Built-in object with supplier-specific factor support |
| Custom regional emission factor | Custom `EmssnFctrSet` with `EmssnFctr` rows | Only when auditor / regulator specifies; else use bundled sets |
| Refreshing historical totals after factor update | Re-run carbon calculation DPE for affected periods | Recalc is the only safe path; do not edit `…CrbnFtprnt` rows manually |
| Disclosure mapping | Configure the disclosure pack matching the framework in scope | One pack per framework; do not co-mingle CSRD and TCFD mappings |

---

## Recommended Workflow

1. Confirm Net Zero Cloud license; verify standard objects appear in Object Manager.
2. Identify the disclosure framework(s) in scope; this drives which scopes and categories are mandatory.
3. Activate the appropriate `EmssnFctrSet` for operating regions (Salesforce-bundled or custom).
4. Load stationary asset carbon footprint records and activity rows per period.
5. Load vehicle asset carbon footprint records for owned fleet.
6. For Scope 3, materially-assess and load only the categories in scope (most orgs cover 4–6 of 15).
7. Activate the carbon calculation DPE definitions; run once manually to backfill, then schedule recurring runs.
8. Configure the disclosure pack(s) for the framework(s) in scope; verify roll-up metrics match expected totals.
9. Document the inventory boundary (operational control vs. equity share vs. financial control), the base year, and the factor sets used in the audit log.

---

## Review Checklist

- [ ] Disclosure framework(s) identified before object loading
- [ ] `EmssnFctrSet` activated for all operating regions
- [ ] Stationary asset records have activity rows for all fuel / electricity types
- [ ] Vehicle asset records distinct from any Automotive Cloud `Vehicle` records
- [ ] Scope 3 categories loaded only for material categories (not all 15 by default)
- [ ] Carbon calculation DPE definitions activated AND scheduled
- [ ] First calculation manually executed; `…CrbnFtprnt` rows populated
- [ ] Disclosure pack(s) configured per framework
- [ ] Audit-log entries for inventory boundary, base year, and factor sets used
- [ ] Custom factor sets justified by auditor / regulator requirement (not preference)

---

## Salesforce-Specific Gotchas

1. **Carbon Calculation DPE Is Not Automatic** — Net Zero Cloud orgs go live with no calculation jobs running. `…CrbnFtprnt` rows stay empty even when activity data is loaded. Activate the DPE definitions and schedule them as part of go-live.

2. **Location-Based vs Market-Based Scope 2 Tracked Per Row** — Scope 2 reporting requires both location-based and market-based totals. The split is driven by the emission factor selected on each `StnryAssetEnrgyUse` row, not a separate object. Misconfiguring the factor selection silently produces a single-method total that fails dual-reporting requirements.

3. **Scope 3 Is NOT All 15 Categories By Default** — Loading every Scope 3 category produces noise (employee-commute estimates with high uncertainty crowd out material categories). Materially assess first; load only categories that pass the materiality threshold for the framework.

4. **Manual Edits to `…CrbnFtprnt` Rows Get Overwritten** — Practitioners sometimes hand-correct a calculated total when actuals don't match expectations. The next DPE run overwrites the manual edit. Corrections must happen at the activity-data or factor level, not on the calculated row.

5. **Custom EmssnFctrSet Without Audit Trail** — Custom factor sets without a documented source / effective date / approval reference fail external audit. Always attach metadata explaining where the factor came from and who approved it.

6. **Reusing Automotive Cloud `Vehicle` for Emissions** — `Vehicle` (Automotive Cloud) and `VehicleAssetCrbnFtprnt` (Net Zero Cloud) are distinct objects. The Net Zero Cloud calculation engine reads `VehicleAssetCrbnFtprnt`. Loading fleet emissions onto Automotive Cloud `Vehicle` records produces empty Net Zero Cloud totals.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Inventory boundary document | Operational control / equity share / financial control choice with reasoning |
| Materiality assessment | Which Scope 3 categories are in scope and why |
| Emission factor library map | Active `EmssnFctrSet` per region + custom factor justification |
| DPE activation runbook | Per-scope calculation definition activation + schedule |
| Disclosure pack configuration | Per-framework metric mapping (CSRD, TCFD, CDP, etc.) |
| Audit log | Base year, inventory boundary, factor sets, restatement history |

---

## Related Skills

- manufacturing-cloud-setup — for sibling Industries Cloud DPE-activation patterns and shared platform behaviors
- automotive-cloud-setup — for distinguishing the `Vehicle` (asset) vs. `VehicleAssetCrbnFtprnt` (emissions) split when both clouds are licensed
- industries-cloud-selection — for the architect-level decision of whether Net Zero Cloud is the right fit
