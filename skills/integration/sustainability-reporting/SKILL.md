---
name: sustainability-reporting
description: "Producing regulatory and voluntary sustainability disclosures from Salesforce Net Zero Cloud (formerly Sustainability Cloud) — the native ESRS / CSRD / SASB / GRI / CDP report builders, the Carbon Accounting Manager data model (Stationary Asset, Vehicle Asset, Scope 3 procurement items, Energy Use Records), the double-materiality assessment prerequisite for CSRD, the MSESRSMainDataraptor Data Mapper for ESRS reports, and the Sustainability Scorecard. NOT for Net Zero Cloud feature setup / emissions-source configuration (see integration/net-zero-cloud-setup), NOT for general CRM Analytics dashboards (Net Zero Cloud's report builders are a separate surface)."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "net zero cloud sustainability cloud carbon accounting manager"
  - "esrs csrd sustainability report builder salesforce"
  - "double materiality assessment csrd prerequisite"
  - "scope 1 2 3 emissions stationary asset vehicle"
  - "msesrsmaindataraptor data mapper esrs report"
  - "sustainability scorecard developer guide"
  - "sasb gri cdp framework sustainability disclosures"
tags:
  - net-zero-cloud
  - sustainability
  - esrs
  - csrd
  - emissions
inputs:
  - "Reporting framework (CSRD / ESRS / SASB / GRI / CDP)"
  - "Reporting period and entity scope"
  - "Whether double-materiality assessment has been completed (CSRD prerequisite)"
outputs:
  - "Framework-specific report (Word / OmniScript / structured output)"
  - "Sustainability Scorecard summary"
  - "Disclosure-readiness checklist with gaps surfaced"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-05
---

# Sustainability Reporting (Net Zero Cloud)

Salesforce Net Zero Cloud (formerly "Sustainability Cloud") is the
industry product for carbon accounting and regulatory sustainability
disclosure. It ships a Carbon Accounting Manager data model and a
set of native report builders for the major frameworks: **ESRS**
(European Sustainability Reporting Standards under CSRD), **SASB**,
**GRI**, **CDP**.

This skill covers the **reporting / disclosure output layer** —
which framework to use, how to drive the native report builders,
the data prerequisites, and the common pitfalls. Configuring
emissions sources and ingesting energy data is a separate skill.

## The Carbon Accounting Manager data model (briefly)

Net Zero Cloud organizes emissions data into typed source objects
that map to the GHG Protocol's three scopes:

| Scope | Source category | Net Zero Cloud objects |
|---|---|---|
| Scope 1 | Direct emissions (owned facilities, fleet) | `StationaryAssetCarbonInventory`, `VehicleAssetCarbonInventory` |
| Scope 2 | Purchased energy | `StationaryAssetEnergyUse`, electricity / heating purchases |
| Scope 3 | Value-chain (procurement, travel, waste) | `ScopeThreeCarbonInventory`, procurement / travel / waste records |

The unit-of-measure inputs are **Energy Use Records** — typed
source records that the platform converts into CO2-equivalent
emissions via emission factors.

## Report builders

| Framework | Output format | Builder name |
|---|---|---|
| ESRS (CSRD) | Word document via Data Mapper | ESRS Report Builder, MSESRSMainDataraptor |
| SASB | Sector-specific structured output | SASB Report Builder (sector applicability matters) |
| GRI | Disclosure-aligned structured output | GRI Report Builder |
| CDP | Submission-aligned questionnaire output | CDP Report Builder |

The ESRS path uses an OmniScript / Data Mapper combination that
generates a Microsoft Word disclosure. CSRD compliance specifically
requires that a **double-materiality assessment** has been completed
before the report is generated — skipping this prerequisite produces
a non-compliant CSRD output even if the report builder runs without
error.

## Double-materiality (CSRD prerequisite)

Double materiality has two axes:

- **Impact materiality** — how the business impacts society and
  the environment.
- **Financial materiality** — how sustainability matters affect the
  business's financial performance.

CSRD requires both. The assessment is a discrete project step, not
something the report builder produces. Net Zero Cloud has tooling
to capture the assessment results; the work itself is human and
stakeholder-driven.

## Sustainability Scorecard

The Sustainability Scorecard is Net Zero Cloud's snapshot view of
emissions performance against targets. It aggregates Scope 1 / 2 /
3 data into a single readable summary; it is a different surface
from the framework-specific report builders. Scorecard is for
internal monitoring; report builders are for external disclosure.

## Recommended Workflow

1. **Confirm Net Zero Cloud is licensed and provisioned.** It is a separately purchased industry cloud; presence is not implied by an Enterprise / Unlimited license.
2. **Select the target framework.** CSRD / ESRS for EU regulated entities; SASB for sector-aligned investor disclosures; GRI for general voluntary disclosure; CDP for CDP submission. More than one is common; report builders run independently.
3. **Verify double-materiality assessment** if CSRD is in scope. Without it, the ESRS output is structurally correct but compliance-deficient.
4. **Validate the underlying emissions data.** Energy Use Records, asset coverage, supplier coverage. Gaps in input data produce gaps in disclosure.
5. **Run the framework-specific report builder.** ESRS goes through MSESRSMainDataraptor and produces a Word document; SASB / GRI / CDP have their own outputs.
6. **Reconcile against the Sustainability Scorecard.** Scorecard and report-builder numbers should agree for the same scope and period; a mismatch means a configuration drift.
7. **Track disclosure-readiness gaps.** SASB sector applicability, CDP submission workflow, and supplier-data coverage are common gap areas. Document for the next reporting cycle.

## What This Skill Does Not Cover

| Topic | See instead |
|---|---|
| Net Zero Cloud feature setup / emissions-source config | `integration/net-zero-cloud-setup` |
| CRM Analytics general dashboards | `data/crm-analytics-patterns` |
| Sustainability Cloud (legacy product name) before rebrand | (Same product; treat the name as Net Zero Cloud) |
| ESG performance benchmarking | App-layer (CDP, MSCI, etc.) |
