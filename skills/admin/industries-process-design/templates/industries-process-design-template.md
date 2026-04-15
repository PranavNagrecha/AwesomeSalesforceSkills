# Industries Process Design — Work Template

Use this template when designing or customizing industry-specific process workflows in Salesforce Industries clouds.
Fill in all sections before producing process maps, configuration specs, or development guidance.

---

## Scope

**Skill:** `industries-process-design`

**Request summary:** (describe what process the user wants to design, customize, or troubleshoot)

**Industry vertical:** [ ] Insurance Cloud (FSC)   [ ] Communications Cloud   [ ] Energy and Utilities Cloud

---

## License and Platform Readiness

| Item | Status | Notes |
|---|---|---|
| Industry cloud license confirmed in org | [ ] Yes [ ] No | Setup > Installed Packages |
| Claims Management module license (Insurance only) | [ ] Yes [ ] No [ ] N/A | Setup > Company Information > PSLs |
| OmniStudio licensed in org | [ ] Yes [ ] No | Required for OmniScript-based capture UIs |
| CIS integration active and tested (E&U only) | [ ] Yes [ ] No [ ] N/A | Test existing service order type end-to-end first |
| Communications Cloud package installed (Comms only) | [ ] Yes [ ] No [ ] N/A | Check for vlocity_cmt namespace objects |

---

## Prebuilt Component Inventory

### For Insurance Cloud

| Claims Lifecycle Stage | Prebuilt OmniScript Exists? | Customization Needed? | Notes |
|---|---|---|---|
| FNOL Intake | [ ] Yes [ ] No | [ ] None [ ] Minor [ ] Significant | |
| Segmentation and Assignment | [ ] Yes [ ] No | [ ] None [ ] Minor [ ] Significant | |
| Workload Management | [ ] Yes [ ] No | [ ] None [ ] Minor [ ] Significant | |
| Investigation | [ ] Yes [ ] No | [ ] None [ ] Minor [ ] Significant | |
| Financials (Adjuster's Workbench) | [ ] Yes [ ] No | [ ] None [ ] Minor [ ] Significant | |
| Closure | [ ] Yes [ ] No | [ ] None [ ] Minor [ ] Significant | |

**DIP path:** [ ] Managed-package   [ ] Native-core (post-Oct 2025)

### For Communications Cloud

| Item | Status | Notes |
|---|---|---|
| EPC Product Offerings configured for all products in scope | [ ] Yes [ ] No | Decomposition rules cannot be defined without EPC |
| ProductChildItem records exist for all bundle components | [ ] Yes [ ] No | |
| Existing decomposition rule sets identified | [ ] Yes [ ] No | List rule sets: |
| New bundle/product requiring new rules | (name): | |

### For Energy and Utilities Cloud

| Service Order Type | Already Configured? | CIS Endpoint Confirmed? | Exception Path Designed? |
|---|---|---|---|
| Connect | [ ] Yes [ ] No | [ ] Yes [ ] No | [ ] Yes [ ] No |
| Disconnect | [ ] Yes [ ] No | [ ] Yes [ ] No | [ ] Yes [ ] No |
| Rate Change | [ ] Yes [ ] No | [ ] Yes [ ] No | [ ] Yes [ ] No |
| (new type): ____________ | [ ] New | [ ] Yes [ ] No | [ ] Yes [ ] No |

---

## Process Stage Customization Scope

For each stage that requires work, classify and document:

| Stage Name | Vertical | Classification | Description |
|---|---|---|---|
| | | [ ] Use prebuilt as-is | |
| | | [ ] Customize prebuilt | |
| | | [ ] Build new (within framework) | |

> Do NOT use classification "Rebuild in different runtime" — flag this as a design risk and escalate.

---

## Data Flow per Stage

For each stage requiring customization or new build:

### Stage: _______________

**Input data required:**
- Object: ______________ Fields: ______________
- Object: ______________ Fields: ______________

**Output data written:**
- Object: ______________ Fields: ______________
- Object: ______________ Fields: ______________

**Branching conditions:**
- If ______________ then show/execute ______________
- If ______________ then show/execute ______________

**External API calls:**
- Endpoint: ______________ Direction: [ ] Inbound [ ] Outbound
- Request payload fields: ______________
- Response status values and their meaning: ______________

**Exception path:**
- On API failure: set status to ______________ trigger ______________
- Manual resolution procedure: ______________

---

## Integration Validation Checklist (E&U and Comms Only)

Before activating any service order automation or order decomposition:

- [ ] CIS integration tested with existing order type (not just sandbox mock) — E&U
- [ ] New service order type registered in E&U service order configuration with CIS endpoint mapping
- [ ] EPC decomposition rules configured for all new product offerings — Communications Cloud
- [ ] Test commercial order submitted and technical order records verified in vlocity_cmt objects — Comms
- [ ] External provisioning system notification mechanism confirmed (push vs pull, Salesforce trigger) — Comms

---

## OmniScript Customization Notes (Insurance and E&U)

**OmniScript name and type:**

**Managed-package or org-namespace:** [ ] Managed-package   [ ] Org-namespace

**Steps being modified:**
1. Step name: ______________ Change: ______________
2. Step name: ______________ Change: ______________

**New Block elements added:**
| Block Name | Parent Step | Conditional View Expression | Elements Inside |
|---|---|---|---|
| | | | |

**DataRaptor / Integration Procedure changes:**
| Action Name | Type | Direction | Purpose |
|---|---|---|---|
| | Pre-Step / Post-Step | Read / Transform / IP | |

---

## Upgrade Compatibility Assessment

- [ ] No managed-package components directly edited (cloned instead if necessary)
- [ ] All customizations documented as org-namespace metadata or unlocked package components
- [ ] Remote Action bindings in any cloned OmniScripts verified against org-namespace Apex classes
- [ ] Decomposition rule configurations versioned in metadata (not manual org config only)

---

## Testing Sign-Off Criteria

**Insurance:** Complete claim ran through all six stages in sandbox with correct Claim, ClaimParticipant, and financial record outcomes.

**Communications Cloud:** Commercial order submitted → technical order records generated → correct item count and dependency sequence → status transitions to Completed with provisioning callback.

**E&U Cloud:** Service order executed in production-equivalent environment → CIS callout fired and received success response → ServiceContract updated correctly → exception path tested with a simulated CIS failure.

---

## Deviations from Standard Pattern

(Record any approach that differs from the standard pattern in SKILL.md and explain why)

| Deviation | Reason | Risk | Mitigation |
|---|---|---|---|
| | | | |

---

## Notes

(Record architecture decisions, open questions, and anything that needs escalation)
