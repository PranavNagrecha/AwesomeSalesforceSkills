# Examples — Net Zero Cloud Setup

## Example 1: First-Year CSRD Inventory for an EU Manufacturer

**Context:** A mid-sized EU manufacturer is preparing its first CSRD ESRS E1 disclosure. Operating in 4 EU countries, 12 plants, 800 vehicles in fleet, ~6,000 suppliers in Tier 1.

**Problem:** Net Zero Cloud was provisioned three months ago. The team loaded stationary asset records and utility-bill data, expecting the disclosure pack to populate. The pack is empty.

**Solution:** Two missing activations:

1. The **Stationary Asset Carbon Calculation** DPE definition was never activated. Activated and scheduled it nightly. Manually triggered a backfill run; `StnryAssetCrbnFtprnt` rows populated for all 12 plants × 12 months.
2. The disclosure pack was created without the metric mapping. Configured the ESRS E1 pack: GHG Scope 1 (gross) → sum of `StnryAssetCrbnFtprnt` + `VehicleAssetCrbnFtprnt` for combustion sources; GHG Scope 2 (location-based) → sum of stationary asset purchased-electricity rows with location-based factor; same for market-based via market-based factor selection.
3. For Scope 3, performed a quick materiality screen: Cat. 1 Purchased Goods (~70% of footprint), Cat. 6 Business Travel, Cat. 7 Employee Commute, Cat. 11 Use of Sold Products. Loaded these four; deferred the remaining 11 categories with documented materiality reasoning.
4. Activated the Scope 3 calculation DPE definitions for the four loaded categories.

After backfill and DPE runs, the ESRS E1 pack populated with Scope 1, Scope 2 (dual-method), and Scope 3 (4-category) totals — auditor-acceptable starting point for first-year disclosure.

---

## Example 2: Refreshing Historical Totals After DEFRA Annual Update

**Context:** A UK-headquartered company uses the Salesforce-bundled DEFRA factor set. DEFRA publishes its annual update on June 1; the prior year's totals must be restated for consistency in the year-on-year disclosure.

**Problem:** The team naively swapped the active factor set, expecting prior totals to update. The DEFRA 2024 set was activated but `StnryAssetCrbnFtprnt` rows for 2023 still showed totals calculated with DEFRA 2023 factors.

**Solution:** Forced recalculation:

1. Confirmed the new factor set was active and `EmssnFctr` rows mapped to the same activity types as the prior set.
2. Activated the DPE definition that reassigns `StnryAssetEnrgyUse` rows to the new factor set for the 2023 fiscal year.
3. Re-ran the **Stationary Asset Carbon Calculation** DPE for the 2023 period (parameterized by date range).
4. Verified `StnryAssetCrbnFtprnt` rows showed updated totals.
5. Documented the restatement in the audit log: "2023 Scope 1 totals restated using DEFRA 2024 factors (delta: +1.2%) for year-on-year consistency in the FY24 ESRS E1 disclosure."

**Lesson:** Activating a new factor set does not retroactively recalculate. The recalc DPE must be re-run for the affected period, and the restatement documented.

---

## Example 3: Supplier Engagement Lifting a Spend-Based Estimate to Supplier-Specific

**Context:** A retailer's first-year Scope 3 Cat. 1 Purchased Goods total used spend-based estimation across all suppliers, producing ~2.4 MtCO2e ± 30% uncertainty. The board asked to reduce uncertainty for the next disclosure cycle.

**Problem:** Of 6,000 suppliers, only the top 200 were responsible for ~85% of spend. The team needed to engage these 200 to obtain supplier-specific emissions data.

**Solution:** Supplier engagement program:

1. Created `Account` records for the top 200 suppliers; linked to existing `Scope3PcmtItem` rows by supplier name match.
2. Sent supplier engagement requests through Net Zero Cloud's Supplier Engagement feature; tracked responses via supplier maturity scoring.
3. For 60 suppliers that responded with verified emissions data, created supplier-specific `EmssnFctr` records.
4. Re-loaded `Scope3PcmtItem` rows; the calculation engine now uses supplier-specific factors for the 60 suppliers, falls back to spend-based for the rest.
5. New Cat. 1 total: 2.1 MtCO2e ± 18%. Reduction in uncertainty driven by supplier-specific data on 35% of spend.

**Lesson:** Spend-based Scope 3 is the right starting point. Engagement programs progressively replace spend-based estimates with supplier-specific data, reducing uncertainty over multi-year cycles.

---

## Anti-Pattern: Loading Fleet Emissions Onto Automotive Cloud `Vehicle`

A company licensed both Automotive Cloud (for dealer operations) and Net Zero Cloud (for sustainability reporting). The team assumed the `Vehicle` standard object served both purposes and loaded fleet fuel-use as custom fields on `Vehicle`. Net Zero Cloud's carbon calculation produced zero fleet totals because it reads `VehicleAssetCrbnFtprnt`, not `Vehicle`.

**Why it happens:** Two different industry clouds with overlapping naming. `Vehicle` (Automotive Cloud) is the dealer-asset record; `VehicleAssetCrbnFtprnt` (Net Zero Cloud) is the emissions record.

**Correct approach:** Treat them as separate objects. Link them with a custom lookup if cross-domain reporting is needed, but the carbon calculation must read from `VehicleAssetCrbnFtprnt`.
