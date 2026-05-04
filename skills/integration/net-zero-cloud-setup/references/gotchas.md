# Gotchas — Net Zero Cloud Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Carbon Calculation DPE Is Not Automatic

**What happens:** Activity data is loaded but `…CrbnFtprnt` rows stay empty. The disclosure pack shows zero totals.

**When it occurs:** Net Zero Cloud go-live where the activation step was skipped.

**How to handle:** Activate every relevant Carbon Calculation DPE definition (Stationary Asset, Vehicle Asset, Scope 3 per category). Schedule them; run once manually to backfill historical periods. Document activation in the org runbook.

---

## Gotcha 2: Activating a New Factor Set Doesn't Recalculate History

**What happens:** A new annual factor set (DEFRA, EPA) is activated, but existing `…CrbnFtprnt` totals retain old factors. Auditors flag the inconsistency.

**When it occurs:** Annual factor refresh cycles.

**How to handle:** After activating the new factor set, re-run the carbon calculation DPE for the affected periods (parameterized by date range). Document the restatement in the audit log.

---

## Gotcha 3: Manual Edits to `…CrbnFtprnt` Rows Are Overwritten

**What happens:** A practitioner edits a calculated total to match a supplier-provided figure. The next DPE run overwrites the manual edit.

**When it occurs:** Reconciliation between calculated totals and external auditor expectations.

**How to handle:** Corrections must happen at the activity-data layer (`StnryAssetEnrgyUse`, `Scope3PcmtItem`) or at the factor layer (`EmssnFctr`), not on the calculated row. If a one-off override is genuinely required, suppress the DPE run for that record via a flag — but this is an audit risk.

---

## Gotcha 4: Scope 2 Dual-Method Reporting Driven Per Row

**What happens:** Scope 2 totals report a single number rather than the required location-based + market-based dual methodology. Auditors flag the disclosure as non-compliant.

**When it occurs:** First-year Scope 2 reporting where the dual-method requirement was not understood.

**How to handle:** Each `StnryAssetEnrgyUse` row for purchased electricity needs to roll up into both methods. The factor selection on each row determines which method it counts toward; configure the disclosure pack to surface both totals. GHG Protocol Scope 2 Guidance (2015) defines the dual-reporting requirement.

---

## Gotcha 5: Scope 3 Materiality Without Documentation

**What happens:** A team loads only 4 of 15 Scope 3 categories and the auditor asks why the others were excluded. No documentation exists.

**When it occurs:** First-year Scope 3 reporting where material categories were chosen but not formally documented.

**How to handle:** Perform a structured materiality assessment for each of the 15 categories with a documented rationale (e.g., "Cat. 8 Upstream Leased Assets: not material — no leased operations"). Auditors accept material-only reporting; they reject undocumented exclusions.

---

## Gotcha 6: `Vehicle` (Automotive Cloud) vs `VehicleAssetCrbnFtprnt` (Net Zero Cloud) Confusion

**What happens:** A company licensed both clouds loads fleet fuel-use onto `Vehicle` records. The Net Zero Cloud calculation produces zero fleet totals.

**When it occurs:** Dual-licensed orgs where the team didn't realize the two clouds use distinct objects.

**How to handle:** Use `VehicleAssetCrbnFtprnt` for emissions, `Vehicle` for dealer / asset records. Link with a custom lookup if cross-domain reporting is needed.
