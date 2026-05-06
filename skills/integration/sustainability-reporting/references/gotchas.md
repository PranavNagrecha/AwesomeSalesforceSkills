# Gotchas — Sustainability Reporting (Net Zero Cloud)

Real-world surprises in producing sustainability disclosures from
Net Zero Cloud.

---

## Gotcha 1: CSRD requires double-materiality assessment as a prerequisite

**What happens.** Team runs the ESRS report builder, gets a clean
Word document, files it. Auditor flags it as non-compliant because
no double-materiality assessment was performed.

**When it occurs.** Teams treating the report builder as the
complete CSRD output.

**How to avoid.** Complete and document the double-materiality
assessment before generating the ESRS report. The report builder
does not validate that this prerequisite was completed.

---

## Gotcha 2: SASB is sector-specific; one-size SASB doesn't exist

**What happens.** Team picks "SASB" without selecting a sector;
report builder produces an output with metrics that don't apply
to the company.

**When it occurs.** First-time SASB reporting without SICS
classification.

**How to avoid.** Identify the SICS sector first; configure the
SASB Report Builder for that sector explicitly.

---

## Gotcha 3: Scope 3 totals look low because coverage is incomplete

**What happens.** Scope 3 emissions report shows a small number
that appears favorable; in reality the small number reflects
missing data, not low emissions.

**When it occurs.** Procurement / supplier / travel / commuting /
waste data not yet ingested into the appropriate Scope 3 typed
records.

**How to avoid.** Audit Scope 3 category coverage explicitly.
Disclose categories with coverage gaps in the narrative; do not let
"small total" imply "low emissions".

---

## Gotcha 4: Net Zero Cloud is a separately licensed product

**What happens.** Team assumes Net Zero Cloud is part of
Enterprise / Unlimited; tries to enable; nothing happens.

**When it occurs.** Pre-purchase scoping conversations.

**How to avoid.** Confirm Net Zero Cloud licensing in the
contract. It is an industry cloud add-on.

---

## Gotcha 5: Emission factors version drift between report runs

**What happens.** Two reports run a month apart against the same
underlying data produce different numbers. The platform's emission-
factor library was updated.

**When it occurs.** Annual factor refreshes by Net Zero Cloud or
manual updates by the team.

**How to avoid.** Pin the emission-factor version per report run;
record the version in the disclosure metadata. Auditors will ask.

---

## Gotcha 6: ESRS Report Builder output is a Word template, not a final document

**What happens.** Stakeholder receives the output and asks "is this
ready to file?" The Word document has narrative placeholders that
must be filled by the sustainability team.

**When it occurs.** First-time ESRS reporting.

**How to avoid.** Plan a narrative-completion step in the project
timeline. The report builder produces structure and quantitative
data; humans complete the qualitative content.

---

## Gotcha 7: Calendar / period-boundary issues across surfaces

**What happens.** Sustainability Scorecard "Q1 totals" disagree
with ESRS report "Q1 totals" by a small amount. Cause: time-zone
or day-boundary handling on Energy Use Records puts records on
different sides of the period boundary.

**When it occurs.** Cross-region reporting where source data uses
local time and the platform stores UTC.

**How to avoid.** Standardize on UTC at the data ingestion layer.
Document the period-boundary convention.

---

## Gotcha 8: Customizing the Data Mapper requires OmniStudio skills

**What happens.** Customer wants to add a custom disclosure topic
to the ESRS output. Standard admin can't do it; the Data Mapper is
an OmniStudio object.

**When it occurs.** Companies with bespoke disclosure requirements
beyond the framework standard.

**How to avoid.** Plan for OmniStudio expertise in the
implementation team or scope to standard outputs.

---

## Gotcha 9: GRI and SASB report builder coverage was historically thin

**What happens.** Trailhead and product docs cover ESRS deeply; GRI
and SASB coverage is thinner. Implementations frequently
supplement with external blogs and Trailhead modules.

**When it occurs.** GRI / SASB greenfield builds.

**How to avoid.** Budget time for documentation gaps; engage
Salesforce Premier Support or a Net Zero Cloud SI for
non-CSRD-and-non-CDP frameworks.
