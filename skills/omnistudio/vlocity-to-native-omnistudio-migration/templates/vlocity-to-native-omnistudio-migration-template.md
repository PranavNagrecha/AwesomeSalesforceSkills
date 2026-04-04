# Vlocity to Native OmniStudio Migration — Work Template

Use this template when planning or executing a migration from a Vlocity managed package to native OmniStudio.

---

## Scope

**Skill:** `vlocity-to-native-omnistudio-migration`

**Request summary:** (fill in what the user asked for — e.g., "migrate Claims domain components from vlocity_ins to native OmniStudio in production sandbox")

**Vlocity namespace in use:** `vlocity_ins` | `vlocity_cmt` | `vlocity_ps` _(circle one)_

---

## Pre-Migration Context

Answer these before starting any migration work:

| Question | Answer |
|---|---|
| Is `enableOaForCore` enabled in the target org? | Yes / No / Unknown |
| Has the OmniStudio Migration Tool been run before? | Yes / No |
| Does the org use Vlocity OmniOut for external embedding? | Yes / No / Unknown |
| Does the org have a DataPacks-based CI/CD pipeline? | Yes / No |
| Are there custom Apex classes calling Vlocity service classes? | Yes / No / Unknown |
| How many OmniScripts exist in the org? | _____ |
| How many DataRaptors exist in the org? | _____ |
| How many Integration Procedures exist in the org? | _____ |
| How many FlexCards exist in the org? | _____ |
| Migration approach: | Phased by domain / Single-pass big-bang |

---

## Namespace Audit Results

Run: `python3 scripts/check_vlocity_to_native_omnistudio_migration.py --manifest-dir force-app/`

| File Type | Files With Vlocity References | Notes |
|---|---|---|
| LWC HTML files (`c-omni-script`, `c-flex-card`) | _____ files | |
| Apex classes (`vlocity_ins.`, `vlocity_cmt.`, `vlocity_ps.`) | _____ files | |
| Custom metadata / flows / other | _____ files | |
| **Total affected files** | **_____** | |

---

## Component Inventory

List components scoped for this migration pass. Update status as work progresses.

| Component Name | Type | Migration Tool Status | Native Activated | LWC/Apex Updated | Tested | Notes |
|---|---|---|---|---|---|---|
| (e.g.) Claims_NewLoss | OmniScript | Migrated / Skipped | Yes / No | Yes / No | Pass / Fail / Pending | |
| | DataRaptor | | | | | |
| | Integration Procedure | | | | | |
| | FlexCard | | | | | |

---

## Approach

Which pattern from SKILL.md applies?

- [ ] **Pattern 1: Bulk Namespace Audit Before Migration** — run checker script first, then plan all code changes
- [ ] **Pattern 2: Phased Component Cutover by Domain** — migrate one business domain at a time
- [ ] **Pattern 3: DataPack Pipeline Replacement** — rebuild CI/CD pipeline from VBT to SFDX

Justification: (fill in why this approach fits the org's scale and risk tolerance)

---

## Checklist

Copy from SKILL.md review checklist and tick as complete:

- [ ] All LWC HTML files use `omnistudio-*` component tags, not `c-omni-script` or `c-flex-card`
- [ ] All Apex classes reference `omnistudio.IntegrationProcedureService`, not `vlocity_ins/cmt/ps.IntegrationProcedureService`
- [ ] CI/CD pipeline uses SFDX + native metadata types, not Vlocity Build Tool DataPacks
- [ ] OmniStudio Migration Tool log reviewed; no components in error or skipped state without documented reason
- [ ] All native migrated components activated and functionally tested in sandbox
- [ ] DataRaptor formulas and Integration Procedure HTTP actions verified for namespace-specific differences post-migration
- [ ] Vlocity OmniOut usage assessed and native equivalent confirmed or gap documented
- [ ] Vlocity managed package uninstall dependency check completed (zero remaining Apex/metadata references)

---

## Cutover Plan

| Step | Description | Owner | Target Date | Status |
|---|---|---|---|---|
| 1 | Enable `enableOaForCore` in sandbox | | | |
| 2 | Run namespace audit script | | | |
| 3 | Run OmniStudio Migration Tool (sandbox) | | | |
| 4 | Update LWC markup and Apex classes | | | |
| 5 | Activate native components in sandbox | | | |
| 6 | Side-by-side functional testing | | | |
| 7 | Deactivate Vlocity components in sandbox | | | |
| 8 | Promote to production | | | |
| 9 | Monitor production for regression | | | |
| 10 | Uninstall Vlocity managed package | | | |

---

## Runtime Verification

After activation, verify the runtime is correct:

| Check | Result |
|---|---|
| `enableOaForCore` setting in OmniStudio Settings | `true` / `false` |
| Native OmniScript type used in LWC | `omnistudio-omni-script` confirmed |
| Apex compiles with `omnistudio.*` references | Pass / Fail |
| SFDX retrieve captures native OmniStudio metadata types | Pass / Fail |
| Side-by-side test results match Vlocity baseline | Pass / Fail / Delta documented |

---

## Known Gaps and Risks

Document any Vlocity features without native equivalents, or migration risks identified during discovery:

| Feature / Risk | Impact | Mitigation | Owner |
|---|---|---|---|
| (e.g.) OmniOut used on 3 external portals | High — portals will break if Vlocity removed | Assess native OmniOut or Experience Cloud equivalent before cutover | |
| | | | |

---

## Notes

Record any deviations from the standard pattern, decisions made, or findings discovered during migration:

-
-
