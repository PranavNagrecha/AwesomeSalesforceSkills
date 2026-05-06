# Examples — Sustainability Reporting

## Example 1 — CSRD ESRS report for an EU subsidiary

**Context.** EU manufacturing subsidiary needs to file a CSRD-
aligned ESRS sustainability report.

**Pre-flight checklist.**

- Net Zero Cloud licensed; subsidiary entity scoped.
- Stationary Asset and Vehicle Asset records populated for facilities
  and fleet.
- Scope 3 procurement data ingested (typically via supplier surveys
  or third-party feeds).
- Energy Use Records cover the reporting period with no monthly
  gaps.
- **Double-materiality assessment completed and stored.**

**Run.** Navigate to ESRS Report Builder; select reporting period
and entity; trigger the MSESRSMainDataraptor. Output: Microsoft Word
document with disclosure tables and narrative placeholders.

**Post-process.** Sustainability team fills narrative sections;
controller signs off; disclosure is filed.

---

## Example 2 — Sustainability Scorecard vs ESRS report number mismatch

**Context.** Scorecard shows 12,400 tCO2e total Scope 1+2 for Q1.
ESRS report shows 12,810 tCO2e for the same period and entity.

**Diagnosis.** Configuration drift between scorecard scope and
report scope. Common causes:

- Scorecard excludes a vehicle asset class that the ESRS report
  includes.
- Different emission-factor versions in use across the two surfaces.
- Time-zone boundary on Energy Use Records placing a Q1 / Q2
  border-record on the wrong side of the scorecard's calendar
  vs the report builder's calendar.

**Fix.** Audit scope and emission-factor configuration. The two
surfaces should agree on the same data; a mismatch is a
configuration bug, not a sampling artifact.

---

## Example 3 — Scope 3 procurement coverage gap

**Context.** Scope 3 emissions report shows total ~30% lower than
peer benchmarks suggest.

**Likely cause.** Scope 3 categories not all covered. The GHG
Protocol's 15 Scope 3 categories include purchased goods and
services, capital goods, fuel-and-energy-related upstream, business
travel, employee commuting, waste, end-of-life, etc. Net Zero
Cloud captures these via typed records, but coverage depends on
data ingestion.

**Fix.** Audit which Scope 3 categories have records. Categories
without data simply do not contribute to totals — looks like low
emissions but is actually missing data. Document the coverage gap
in the disclosure narrative.

---

## Example 4 — SASB sector applicability

**Context.** Investor relations team requests a SASB report.

**Catch.** SASB standards are sector-specific. A retailer files
against the SASB Multiline and Specialty Retailers standard, not
the same standard as a software-as-a-service company. The Net Zero
Cloud SASB Report Builder requires a sector selection that
determines which metrics are required.

**Fix.** Identify the company's primary SASB sector (SICS
classification). Map to the corresponding SASB standard. Configure
the report builder accordingly.

---

## Example 5 — Combining frameworks in one cycle

**Pattern.** Many companies disclose against more than one framework
per year:

| Framework | Audience | Cadence |
|---|---|---|
| CSRD / ESRS | EU regulator | Annual |
| SASB | Investors (sector-specific) | Annual |
| GRI | General voluntary | Annual or biennial |
| CDP | CDP submission | Annual via CDP portal |
| Sustainability Scorecard | Internal monitoring | Quarterly or monthly |

**Implication.** Underlying data feeds all of them; framework-
specific reports differ in structure, narrative requirements, and
which scope-3 categories are mandatory. The work is "configure the
data once, run the appropriate report builders".

---

## Example 6 — MSESRSMainDataraptor walkthrough

**Context.** ESRS Report Builder uses an OmniStudio Data Mapper
named MSESRSMainDataraptor (delivered with Net Zero Cloud) that
extracts disclosure-relevant data and maps to a Word template.

**Inputs.** Reporting period, entity, materiality assessment, scope
selections.

**Process.**

1. Data Mapper runs and pulls aggregated emissions, energy, and
   material-topic data.
2. Output is rendered into the Word template as a structured
   disclosure document.
3. Narrative sections are placeholders that the sustainability team
   completes.

**Customization.** Light customization (additional fields, new
disclosure topics) is supported via the Data Mapper UI. Deeper
customization (entirely new disclosures) typically requires an
OmniStudio specialist.
