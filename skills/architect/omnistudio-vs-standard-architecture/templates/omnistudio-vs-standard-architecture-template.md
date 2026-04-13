# OmniStudio vs Standard Architecture — Decision Template

Use this template when making or documenting a technology selection decision between OmniStudio and the standard Salesforce platform for a guided UI or data orchestration requirement.

---

## Scope

**Skill:** `omnistudio-vs-standard-architecture`

**Request summary:** (describe the specific use case being evaluated)

**Date:** (YYYY-MM-DD)

**Author:** (name/team)

---

## Step 1: License Gate

**Qualifying Industries cloud license present?**
- [ ] Yes — specify: _______________
- [ ] No — decision is Screen Flow + LWC. Skip to Section 5.

**Specific edition confirmed?** (e.g., FSC Growth, Health Cloud Enterprise)
- Edition: _______________
- OmniStudio entitlement level confirmed against pricing/packaging docs: [ ] Yes / [ ] No

**License confirmation method:**
- [ ] Verified in Setup > Company Information > Licenses
- [ ] Confirmed via Salesforce contract order form
- [ ] Salesforce case opened for clarification

---

## Step 2: Use Case Complexity Assessment

**Number of Salesforce objects involved:** ___

**External REST callouts required?**
- [ ] Yes — number of endpoints: ___
- [ ] No

**Number of guided UI steps (if applicable):** ___

**Branching logic complexity:**
- [ ] Simple (linear or 1–2 branches)
- [ ] Moderate (3–5 branches, conditional steps)
- [ ] Complex (6+ branches, parallel data fetch, step skipping)

**Parallel data fetch requirements?**
- [ ] Yes
- [ ] No

**Tooling continuum mapping:**

| Continuum Point | Applies? | Notes |
|---|---|---|
| Dynamic Forms / Dynamic Actions | [ ] Yes / [ ] No | |
| Screen Flow (standalone) | [ ] Yes / [ ] No | |
| Screen Flow + LWC | [ ] Yes / [ ] No | |
| OmniScript + Integration Procedure | [ ] Yes / [ ] No | |
| LWC + Apex (full code) | [ ] Yes / [ ] No | |

**Recommended continuum entry point:** _______________

---

## Step 3: Team Skills Assessment

**OmniStudio-certified developers on project team?**
- [ ] Yes — count: ___
- [ ] No

**OmniStudio experience level of available team:**
- [ ] Expert (3+ production OmniStudio implementations)
- [ ] Intermediate (1–2 production implementations)
- [ ] Novice (training only, no production experience)
- [ ] None

**Estimated ramp time if OmniStudio selected and team is untrained:** ___ weeks

**Long-term maintenance owner:**
- [ ] Dedicated OmniStudio team
- [ ] General Salesforce admin / developer team
- [ ] Client team (self-maintained after handoff)

---

## Step 4: Runtime Path Assessment (if OmniStudio is being considered)

**Current OmniStudio state in org:**
- [ ] None — first OmniStudio implementation
- [ ] Vlocity managed package (`vlocity_ins__` namespace)
- [ ] Salesforce managed package (`industries__` namespace)
- [ ] Standard Runtime (natively embedded, no namespace)

**Standard Runtime enabled in Setup > OmniStudio Settings?**
- [ ] Yes
- [ ] No
- [ ] Not applicable (no OmniStudio in org)

**If managed package is present — migration assessment:**
- Migration scope estimated: [ ] Yes / [ ] No
- OmniStudio Conversion Tool assessed: [ ] Yes / [ ] No
- Migration debt acknowledged and documented: [ ] Yes / [ ] No
- Recommended path: [ ] Migrate first / [ ] Build on managed package as documented debt / [ ] Not applicable

---

## Step 5: Decision

**Selected tooling:**
- [ ] OmniStudio Standard Runtime
- [ ] OmniStudio managed package (documented as interim — migration debt)
- [ ] Screen Flow + LWC
- [ ] Screen Flow + LWC + Apex
- [ ] Dynamic Forms / Dynamic Actions
- [ ] LWC + Apex (full code)

**Primary rationale:** (summarize the key reasons in 2–4 sentences)

**Trade-offs accepted:** (list what is being traded off in this decision)

**Alternatives rejected and why:**

| Alternative | Reason Rejected |
|---|---|
| | |
| | |

---

## Step 6: Stakeholder Sign-Off

| Stakeholder | Role | Sign-Off Date |
|---|---|---|
| | | |
| | | |

---

## Notes

(Record any deviations from the standard workflow, project-specific constraints, or follow-up items)

**Follow-up items:**
- [ ]
- [ ]
