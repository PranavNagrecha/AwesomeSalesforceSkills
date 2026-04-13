# OmniStudio vs Standard Decision — Work Template

Use this template when evaluating whether to use OmniStudio or standard Salesforce tooling for a guided UI or data transformation use case.

## Scope

**Skill:** `omnistudio-vs-standard-decision`

**Request summary:** (fill in the specific use case being evaluated)

---

## Step 1: License Gate

**Org edition:** _______________

**Industries Cloud license present?**
- [ ] Yes — specify: FSC / Health Cloud / Manufacturing Cloud / Nonprofit Cloud / Education Cloud
- [ ] No — standard tooling only; OmniStudio is not an option. Stop here and proceed to Standard Tooling section.
- [ ] Unknown — check Setup > Company Information > Licenses before proceeding.

**License confirmed by:** Setup UI / Contract documentation / Salesforce AE

---

## Step 2: Use Case Complexity Assessment

| Dimension | Details |
|---|---|
| Number of Salesforce objects involved | |
| External REST callouts required? (Y/N) | |
| Number of UI steps / screens | |
| Branching logic complexity (simple / moderate / complex) | |
| Data transformations across multiple sources? (Y/N) | |

**Complexity verdict:**
- [ ] Simple (1–2 objects, no external callouts, 1–4 steps) → Screen Flow + LWC is adequate
- [ ] Moderate (2–3 objects, 1 external callout, 5–8 steps) → either tool is viable
- [ ] Complex (3+ objects, multiple external callouts, 8+ steps) → OmniStudio preferred if licensed

---

## Step 3: Team Skills Assessment

**OmniStudio-trained developers/admins on team?**
- [ ] Yes — list certifications or project experience: _______________
- [ ] No — note available ramp time: _______________ weeks

**Long-term ownership:** Who will maintain the components post-launch?
_______________

**Skills verdict:**
- [ ] Team is OmniStudio-capable — no ramp risk
- [ ] Team needs ramp — factor ___ weeks into timeline
- [ ] Team is standard Salesforce admin/developer profile — standard tooling preferred for maintainability

---

## Step 4: Deployment State (If Org Already Uses OmniStudio)

**Current OmniStudio state:**
- [ ] No existing OmniStudio — greenfield decision
- [ ] Managed package — legacy Vlocity (`vlocity_ins__` namespace)
- [ ] Managed package — Salesforce-repackaged (`industries__` namespace)
- [ ] Standard Designers (on-platform, native LWC, no managed package namespace)

**If managed package:** Migration to Standard Designers planned?
- [ ] Yes — timeline: _______________
- [ ] No — note: new components should align to existing managed-package model until migration is planned

---

## Step 5: Decision

**Recommendation:** OmniStudio / Standard Tooling / Hybrid (document reasoning)

**Rationale:**
1. License: _______________
2. Use case complexity: _______________
3. Team readiness: _______________
4. Deployment state: _______________

**Specific tooling selected:**
- [ ] OmniScript + Integration Procedure + FlexCards
- [ ] Screen Flow + LWC + Apex
- [ ] Hybrid: _______________

---

## Step 6: Migration Path (If Applicable)

If the org is on managed-package OmniStudio and a migration to Standard Designers is needed:

**Migration scope:**
- OmniScript components to convert: _______________
- Integration Procedures to convert: _______________
- DataRaptors to convert: _______________
- FlexCards to convert: _______________

**Migration tool:** Salesforce OmniStudio Conversion Tool

**Estimated effort:** _______________

**Dependencies / risks:** _______________

---

## Review Checklist

- [ ] License confirmed in Setup — not assumed from cloud edition name
- [ ] Use case complexity mapped to decision table
- [ ] Team skills assessed and ramp time accounted for
- [ ] Deployment state confirmed (managed package vs Standard Designers)
- [ ] If managed package: namespace confirmed (vlocity_ins__ or industries__)
- [ ] Decision documented with explicit rationale
- [ ] Migration path documented if managed-package OmniStudio is in use

---

## Notes

(Record any deviations from the standard pattern and why.)
