# API Version Management — Work Template

Use this template when auditing, upgrading, or standardizing API versions across a Salesforce project.

## Scope

**Skill:** `api-version-management`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- **Project sourceApiVersion:** (from `sfdx-project.json`)
- **Current Salesforce release / API version:** (e.g., Spring '25 / 63.0)
- **Minimum safe API version:** 31.0 (versions 7.0-30.0 retired Summer '22)
- **Managed package?** Yes / No — if yes, minimum subscriber version: ___

## Version Inventory

| Component Type | File Path | Current apiVersion | Target apiVersion | Status |
|---|---|---|---|---|
| Apex Class | `force-app/.../MyClass.cls-meta.xml` | | | |
| Apex Trigger | `force-app/.../MyTrigger.trigger-meta.xml` | | | |
| LWC | `force-app/.../myComponent.js-meta.xml` | | | |
| Aura | `force-app/.../myAuraComp.cmp` | | | |
| VF Page | `force-app/.../MyPage.page-meta.xml` | | | |

## Drift Summary

- **Total versioned components:** ___
- **Components at sourceApiVersion:** ___
- **Components within 2 versions of sourceApiVersion:** ___
- **Components drifted (>2 versions behind):** ___
- **Components at retirement risk (<31.0):** ___

## Transport API Versions (External Integrations)

| Integration Name | Endpoint URL | Current Version | Target Version |
|---|---|---|---|
| | `/services/data/vXX.0/` | | |
| | `/services/Soap/c/XX.0` | | |

## Upgrade Plan

### Tier 1: Retirement-Critical (below v31.0)

- Components: ___
- Target version: ___
- Test strategy: ___

### Tier 2: Drifted (>2 versions behind sourceApiVersion)

- Components: ___
- Target version: ___
- Test strategy: ___

### Tier 3: Alignment (within 2 versions, cosmetic)

- Components: ___
- Target version: ___
- Test strategy: ___

### Final Step: sourceApiVersion Update

- Update `sfdx-project.json` to: ___
- Only after all tiers validated

## CI Gate Configuration

- [ ] Version check added to CI pipeline
- [ ] Minimum version threshold set to: ___
- [ ] Maximum drift tolerance set to: ___ versions behind sourceApiVersion
- [ ] LWC explicit version check enabled

## Review Checklist

- [ ] sourceApiVersion in sfdx-project.json matches target
- [ ] No component below minimum safe version (31.0)
- [ ] All components within 2 versions of sourceApiVersion
- [ ] Every LWC .js-meta.xml has explicit apiVersion
- [ ] External integration endpoints checked for deprecated versions
- [ ] Full test suite passes at new version(s)
- [ ] CI pipeline includes version-drift gate

## Notes

(Record any deviations from the standard pattern and why.)
