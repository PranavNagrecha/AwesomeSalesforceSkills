# LLM Anti-Patterns — Sustainability Reporting

Mistakes AI assistants commonly make when advising on Net Zero
Cloud sustainability disclosures.

---

## Anti-Pattern 1: Confusing Net Zero Cloud report builders with CRM Analytics dashboards

**What the LLM generates.**

> Build a CRM Analytics dashboard to produce the CSRD report.

**Why it happens.** The LLM treats "report" as "dashboard" and
defaults to CRM Analytics.

**Correct pattern.** CSRD / ESRS reports are produced by the Net
Zero Cloud ESRS Report Builder (using MSESRSMainDataraptor and a
Word template), not by CRM Analytics dashboards. CRM Analytics is
an internal-monitoring surface; report builders are the disclosure
surface.

**Detection hint.** Any sustainability reporting recommendation
that targets CRM Analytics for regulatory output.

---

## Anti-Pattern 2: Skipping the double-materiality assessment for CSRD

**What the LLM generates.**

> To produce the CSRD report, run the ESRS Report Builder.

**Why it happens.** The LLM treats the report builder as the
complete output.

**Correct pattern.** CSRD requires a double-materiality assessment
as a prerequisite. The report builder does not validate that this
was completed; the auditor will. Plan and document the assessment
before generating the report.

**Detection hint.** Any CSRD workflow that does not name double-
materiality as a step.

---

## Anti-Pattern 3: Treating "Sustainability Cloud" and "Net Zero Cloud" as different products

**What the LLM generates.**

> Sustainability Cloud is the older product; Net Zero Cloud is the
> newer one.

**Why it happens.** Rebranding training-data ambiguity.

**Correct pattern.** Same product, different name. Use "Net Zero
Cloud" in current docs; recognize "Sustainability Cloud" as the
historical name.

**Detection hint.** Any treatment that posits two distinct products.

---

## Anti-Pattern 4: Recommending "SASB" without sector

**What the LLM generates.**

> Generate the SASB report.

**Why it happens.** SASB sounds singular.

**Correct pattern.** SASB standards are sector-specific (78 sectors
in SICS). Identify the company's primary SICS sector first; the
SASB Report Builder requires that selection.

**Detection hint.** Any SASB recommendation without sector.

---

## Anti-Pattern 5: Asserting Scope 3 categories are optional

**What the LLM generates.**

> Scope 3 reporting is optional in CSRD.

**Why it happens.** GHG Protocol distinguishes mandatory vs
optional categories in voluntary frameworks; the LLM
overgeneralizes.

**Correct pattern.** CSRD requires reporting of material Scope 3
categories. The double-materiality assessment determines which are
material. Treating Scope 3 as optional under CSRD is a compliance
error.

**Detection hint.** Any CSRD guidance that frames Scope 3 as
optional.

---

## Anti-Pattern 6: Treating Net Zero Cloud as part of standard Salesforce licensing

**What the LLM generates.**

> Enable Net Zero Cloud from Setup -> Sustainability Cloud
> Settings.

**Why it happens.** The LLM assumes feature toggles for industry
clouds.

**Correct pattern.** Net Zero Cloud is a separately licensed
industry cloud. Confirm licensing before assuming features are
available.

**Detection hint.** Any "enable from Setup" guidance for Net Zero
Cloud features without a license-check step.

---

## Anti-Pattern 7: Custom Data Mapper changes treated as admin task

**What the LLM generates.**

> Edit the MSESRSMainDataraptor Data Mapper from Setup ->
> Sustainability -> Configuration.

**Why it happens.** The LLM treats Data Mapper changes as a
standard config click-path.

**Correct pattern.** Data Mappers are OmniStudio objects;
modifications require OmniStudio expertise (and care — these
mappers ship as part of the product). Custom disclosure topics
typically need a specialist.

**Detection hint.** Any "edit the Data Mapper" recommendation
without an OmniStudio caveat.
