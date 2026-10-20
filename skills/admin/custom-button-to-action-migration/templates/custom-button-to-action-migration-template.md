# Custom Button to Action Migration — Work Template

Use this template when migrating Classic custom buttons (especially JavaScript buttons) to Lightning Quick Actions / Screen Flows / LWC Quick Actions.

---

## Scope

**Skill:** `custom-button-to-action-migration`

**Object:** _(target object)_

**Button count:**

```bash
sf data query --query \
  "SELECT DisplayType, LinkType, COUNT(Id) FROM WebLink WHERE PageOrSobjectType='Account' GROUP BY DisplayType, LinkType"
```

| DisplayType | LinkType | Count |
|---|---|---|
| button | javascript | |
| button | url | |
| link | url | |
| massActionButton | javascript | |

---

## Per-Button Decision Matrix

| Button Name | Type | JS / URL Body Summary | Replacement Pattern | Notes |
|---|---|---|---|---|
| MarkHotProspect | button, javascript | Calls Apex, alerts, reloads | Headless LWC Quick Action (Pattern 1) | |
| OpenLinkedInLookup | button, url | External URL | Headless navigation Quick Action (Pattern 4) | |
| MassMarkAsKey | massActionButton, javascript | getRecordIds + Apex | List-view action calling Apex (Pattern 3; surface UNVERIFIED 2026-10-20) | |
| | | | | |

Patterns: `1=Headless LWC`, `2=Screen Flow`, `3=List-view action`, `4=Headless navigation`, `5=Coexistence (retain Classic)`, `Retire=No replacement`.

---

## Apex Service Refactor

| Original Apex Method | Becomes | Visibility |
|---|---|---|
| (existing class).markAsHotProspect | `@AuraEnabled` static (cacheable=false) with `with sharing` + `WITH USER_MODE` | Public to LWC |
| | | |

Read idiom by the class's `.cls-meta.xml` `apiVersion` (not the org's release): at 67.0 and later `WITH SECURITY_ENFORCED` can't be used and `WITH USER_MODE` is the replacement (apexdev 264 L11926-11927). UNVERIFIED (2026-10-20): the 57.0 floor for `WITH USER_MODE` is a Help figure.

---

## Coexistence Tracking

Add `Last_Action_Source__c` (Picklist) to the object:

| Source | Description |
|---|---|
| Classic Button | JS button invocation |
| Lightning Action | New Lightning Quick Action / LWC / Flow |

Update both Classic JS button code and the new Apex method to write this field.

---

## Adoption Goal

Retire the Classic button when:

- [ ] Adoption metric: ≥ 95% of invocations from "Lightning Action" over rolling 30 days
- [ ] OR fixed retirement date: _(YYYY-MM-DD)_

---

## Test Plan

For each migrated button:

- [ ] Functional parity in sandbox
- [ ] User acceptance: representative user from each affected profile confirms action is discoverable and works
- [ ] Mobile (iOS Salesforce App): LWC quick actions are not supported there (LWC guide `use-config-for-quick-actions`)
- [ ] Mobile (Android Salesforce App): same
- [ ] Service Console subtab navigation (if applicable)
- [ ] Mass Action: tested with a selection above the org's observed cap (200 is UNVERIFIED 2026-10-20, Help-only; verify chunking or user notification)

---

## Sign-Off Checklist

- [ ] Every Classic button has a documented decision: replaced, retained for Classic, or retired
- [ ] Native `alert()`/`confirm()` replaced with `LightningAlert`/`LightningConfirm`/`ShowToastEvent`, and no `sforce.*` left (the native calls are not supported in cross-origin iframes in Chrome and Safari)
- [ ] No Apex method called from LWC returns `PageReference`
- [ ] Mass Action selection cap handled explicitly in code/UX (UNVERIFIED 2026-10-20: 200 is Help-only)
- [ ] Coexistence tracking field deployed and being populated
- [ ] Mobile testing completed
- [ ] Migration audit log persisted (Custom_Button_Migration_Log__c)
- [ ] Retirement criterion documented and being measured
